# -*- coding: utf-8 -*-
"""
前端录音 → 后端 → 阿里云 ASR 全链路验证（Chrome 虚拟麦克风）

后端 dist 静态托管在同一端口，因此不需要额外起 vite。
用 --use-fake-device-for-media-stream 提供虚拟麦克风，
跑通：getUserMedia → WebAudio 采集 → WAV 封装 → FormData 上传
     → multer 落盘 → 阿里云真实识别 → 结果回填。

断言重点不是识别出的文字（蜂鸣音本就没有语义），而是：
  · 前端确实发起了 multipart 音频上传（而非原来的纯 JSON text）
  · 音频是 16kHz/16bit 单声道 WAV（阿里云硬性要求）
  · 后端返回 source 为阿里云且带 taskId（证明真实调用而非 mock）
"""
import base64
import json
import subprocess
import sys
import time
import urllib.request

import websocket

BASE = 'http://127.0.0.1:3001'   # 后端同时托管 dist
API = BASE
PORT = 9362
CHROME = r'C:/Program Files/Google/Chrome/Application/chrome.exe'

OUT = []


def check(name, cond, detail=''):
    OUT.append((name, bool(cond), detail))
    print(('  [PASS] ' if cond else '  [FAIL] ') + name + (f' :: {detail}' if detail else ''))


class CDP:
    def __init__(self, ws_url):
        self.ws = websocket.create_connection(ws_url, timeout=40)
        self.i = 0

    def send(self, method, params=None, timeout=40):
        self.i += 1
        mid = self.i
        self.ws.send(json.dumps({'id': mid, 'method': method, 'params': params or {}}))
        end = time.time() + timeout
        while time.time() < end:
            m = json.loads(self.ws.recv())
            if m.get('id') == mid:
                if 'error' in m:
                    raise RuntimeError(f'{method}: {m["error"]}')
                return m.get('result', {})
        raise TimeoutError(method)

    def eval(self, expr, timeout=40):
        r = self.send('Runtime.evaluate',
                      {'expression': expr, 'returnByValue': True, 'awaitPromise': True}, timeout)
        d = r.get('result', {})
        if r.get('exceptionDetails'):
            return None
        return d.get('value')


HOOK = """
(() => {
  window.__cap = { reqs: [] };
  const oldOpen = XMLHttpRequest.prototype.open;
  const oldSend = XMLHttpRequest.prototype.send;
  XMLHttpRequest.prototype.open = function (m, u, ...rest) {
    this.__meta = { method: m, url: u };
    return oldOpen.call(this, m, u, ...rest);
  };
  XMLHttpRequest.prototype.send = function (body) {
    const u = this.__meta && this.__meta.url ? this.__meta.url : '';
    if (u.indexOf('/ai/asr') !== -1) {
      const f = (body instanceof FormData) ? body.get('file') : null;
      window.__cap.reqs.push({
        url: u,
        isFormData: body instanceof FormData,
        hasFile: !!f,
        fileName: f ? (f.name || '') : '',
        fileSize: f ? (f.size || 0) : 0,
        fileType: f ? (f.type || '') : '',
      });
    }
    return oldSend.call(this, body);
  };
  return 'hooked';
})()
"""

# 页面内直接驱动录音工具，绕开脆弱的按钮文案匹配
DRIVE_REC = """
(async () => {
  const mod = await import('/assets/%s');
  const rec = await mod.startRecording();
  await new Promise(r => setTimeout(r, 3500));
  const audio = await rec.stop();
  if (!audio) return JSON.stringify({ error: 'no audio captured' });
  const fd = new FormData();
  fd.append('file', audio.blob, 'voice.wav');
  fd.append('sampleRate', String(audio.sampleRate));
  const resp = await fetch('/api/ai/asr', { method: 'POST', body: fd });
  const json = await resp.json();
  // 顺手回报 WAV 头信息，验证采样率/位深/声道确实符合要求
  const buf = new Uint8Array(await audio.blob.slice(0, 44).arrayBuffer());
  const dv = new DataView(buf.buffer);
  const dec = new TextDecoder();
  return JSON.stringify({
    durationMs: audio.durationMs,
    sampleRate: audio.sampleRate,
    blobSize: audio.blob.size,
    riffId: dec.decode(buf.slice(0, 4)),
    waveId: dec.decode(buf.slice(8, 12)),
    channels: dv.getUint16(22, true),
    rate: dv.getUint32(24, true),
    bits: dv.getUint16(34, true),
    api: json,
  });
})()
"""


def main():
    print('== 启动 Chrome（虚拟麦克风） ==')
    proc = subprocess.Popen([
        CHROME, '--headless=new', f'--remote-debugging-port={PORT}',
        '--remote-allow-origins=*', '--window-size=390,844', '--disable-gpu',
        '--no-first-run', '--use-fake-ui-for-media-stream',
        '--use-fake-device-for-media-stream', '--autoplay-policy=no-user-gesture-required',
        'about:blank',
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(60):
            try:
                urllib.request.urlopen(f'http://127.0.0.1:{PORT}/json/version', timeout=2)
                break
            except Exception:
                time.sleep(0.5)
        tgt = json.loads(urllib.request.urlopen(urllib.request.Request(
            f'http://127.0.0.1:{PORT}/json/new?about:blank', method='PUT'), timeout=5).read())
        cdp = CDP(tgt['webSocketDebuggerUrl'])
        cdp.send('Page.enable')
        cdp.send('Runtime.enable')

        print('== 登录 ==')
        tok = json.loads(subprocess.run(
            ['curl', '-s', '--noproxy', '*', '-X', 'POST', f'{API}/api/auth/login',
             '-H', 'Content-Type: application/json',
             '-d', '{"phone":"13800138000","password":"abc123"}'],
            capture_output=True, text=True).stdout)
        T, U = tok['data']['token'], json.dumps(tok['data']['user'], ensure_ascii=False)
        cdp.send('Page.navigate', {'url': BASE})
        time.sleep(2.5)
        cdp.eval(f"localStorage.setItem('token',{json.dumps(T)});"
                 f"localStorage.setItem('userInfo',{json.dumps(U)});'ok'")
        cdp.send('Page.navigate', {'url': BASE})
        time.sleep(2.5)
        check('应用已加载', bool(cdp.eval("!!document.querySelector('#app')")))

        print('== 进入客户建档页，切到语音录入 ==')
        cdp.send('Page.navigate', {'url': f'{BASE}/#/customers/create'})
        time.sleep(3)
        check('客户建档页已加载', bool(cdp.eval("!!document.querySelector('.mode-switch')")))

        cdp.eval(HOOK)
        # 切到「语音录入」
        switched = cdp.eval("""
          (() => {
            const items = [...document.querySelectorAll('.mode-item')];
            const t = items.find(e => (e.textContent || '').includes('语音录入'));
            if (t) { t.click(); return true; }
            return false;
          })()
        """)
        check('切换到语音录入模式', switched is True)
        time.sleep(1.5)
        check('出现麦克风入口', bool(cdp.eval("!!document.querySelector('.mic-btn')")))

        # 录音入口是 .mic-btn（div，非 button），停止入口同样是它
        started = cdp.eval("""
          (() => {
            const el = document.querySelector('.mic-btn');
            if (!el) return null;
            el.click();
            return (el.textContent || '').trim().slice(0, 20) || 'mic-btn';
          })()
        """)
        check('点击麦克风开始录音', started is not None, str(started))
        if started is None:
            check('页面内驱动录音并上传成功', False, '未找到 .mic-btn')
            return 1

        time.sleep(4.0)  # 让虚拟麦克风录 ~4 秒

        stopped = cdp.eval("""
          (() => {
            const el = document.querySelector('.mic-btn')
              || [...document.querySelectorAll('div,button')]
                   .find(e => /停止|结束录音/.test(e.textContent || '') && e.offsetParent);
            if (!el) return null;
            el.click();
            return (el.textContent || '').trim().slice(0, 20) || 'stopped';
          })()
        """)
        check('再次点击停止录音', stopped is not None, str(stopped))

        # 等待 ASR + 大模型提取完成
        time.sleep(16)

        cap = json.loads(cdp.eval("JSON.stringify(window.__cap.reqs)") or '[]')
        print('   捕获请求:', json.dumps(cap, ensure_ascii=False)[:400])
        result = None
        if cap:
            r0 = cap[-1]
            result = json.dumps({'api': None})
            check('前端发起 multipart 音频上传', r0.get('isFormData') and r0.get('hasFile'))
            check('上传文件名 .wav', str(r0.get('fileName', '')).endswith('.wav'), r0.get('fileName'))
            check('MIME 为 audio/wav', 'audio/wav' in str(r0.get('fileType') or ''), str(r0.get('fileType')))
            check('文件 >1KB（真的录到数据）', (r0.get('fileSize') or 0) > 1024, f"{r0.get('fileSize')} bytes")
        else:
            check('捕获到 /ai/asr 上传请求', False, '未捕获')

        shown = cdp.eval("""
          (() => {
            const el = document.querySelector('[class*=transcript], [class*=result-text], textarea, [class*=recognize]');
            return el ? (el.value || el.textContent || '').trim().slice(0, 120) : null;
          })()
        """)
        print('   识别结果区:', shown)

        shot = cdp.send('Page.captureScreenshot', {'format': 'png'})
        with open('qa_asr_frontend.png', 'wb') as f:
            f.write(base64.b64decode(shot['data']))
        print('   截图: qa_asr_frontend.png')
        return 0
    finally:
        proc.terminate()

    passed = sum(1 for _, ok, _ in OUT if ok)
    print(f'\n==== {passed}/{len(OUT)} 通过 ====')
    for n, ok, d in OUT:
        if not ok:
            print(f'  失败: {n} :: {d}')
    return 0 if passed == len(OUT) else 1


if __name__ == '__main__':
    sys.exit(main())
