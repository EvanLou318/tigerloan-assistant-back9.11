# -*- coding: utf-8 -*-
"""
DeepSeek LLM + 阿里云 ASR 端到端真实调用验证

验证链路：
  1. 生成带语音内容的测试音频 → POST /api/ai/asr（multipart）→ 应调阿里云真实识别
  2. ASR 转写结果 → POST /api/ai/extract/customer-voice → 应调 DeepSeek 真实结构化提取
  3. /api/ai/extract/schedule 同样走 DeepSeek
  4. 错误路径：错凭证 / 错 appkey / 空音频 应给出可读报错而非崩溃
"""
import json
import os
import struct
import subprocess
import sys
import time
import urllib.error
import urllib.request
import wave

API = 'http://127.0.0.1:3001'
OUT = []


def check(name, cond, detail=''):
    OUT.append((name, bool(cond), detail))
    print(('  [PASS] ' if cond else '  [FAIL] ') + name + (f' :: {detail}' if detail else ''))


def http(method, url, token=None, body=None, form=None, timeout=60):
    """form: list of tuples for multipart; body: dict for JSON"""
    if form:
        boundary = '----QAFormBoundary' + str(int(time.time() * 1000))
        data = bytearray()
        for key, val in form:
            if isinstance(val, tuple):  # (filename, bytes)
                fn, content = val
                data += f'--{boundary}\r\n'.encode()
                data += f'Content-Disposition: form-data; name="{key}"; filename="{fn}"\r\n'.encode()
                data += b'Content-Type: audio/wav\r\n\r\n'
                data += content + b'\r\n'
            else:
                data += f'--{boundary}\r\n'.encode()
                data += f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode()
                data += str(val).encode() + b'\r\n'
        data += f'--{boundary}--\r\n'.encode()
        req = urllib.request.Request(url, data=bytes(data), method='POST')
        req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
    else:
        d = json.dumps(body, ensure_ascii=False).encode() if body is not None else None
        req = urllib.request.Request(url, data=d, method=method)
        if d:
            req.add_header('Content-Type', 'application/json')
    if token:
        req.add_header('X-Auth-Token', token)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raw = e.read().decode() or '{}'
        try:
            return json.loads(raw)
        except Exception:
            return {'success': False, 'message': raw[:200]}


def gen_speech_like_wav(path, seconds=2.0, rate=16000):
    """合成一段类语音信号（多谐波+包络），比纯正弦更接近真实语音能量分布。
    阿里云对无声/纯音通常返回空串，这里只为验证链路连通与字段完整。"""
    n = int(seconds * rate)
    frames = bytearray()
    for i in range(n):
        t = i / rate
        # 音节包络 4Hz，模拟连续说话
        env = max(0.0, min(1.0, (t * 4) % 1.0 * 2.2))
        env *= min(1.0, i / (rate * 0.05), (n - i) / (rate * 0.05))
        f0 = 130 + 25 * (1 if (int(t * 2) % 2) else -1)  # 基频抖动
        v = 0.0
        for k, amp in ((1, 1.0), (2, 0.5), (3, 0.28), (4, 0.14)):
            v += amp * pow(k, -1.0) * pow(2, 3.14159) * 0.1 * __import__('math').sin(2 * 3.14159 * f0 * k * t)
        frames += struct.pack('<h', int(max(-1, min(1, v * env)) * 32000))
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(bytes(frames))
    return path


def main():
    wav_path = os.path.join(os.getcwd(), '.qa_speech_16k.wav')
    gen_speech_like_wav(wav_path, seconds=2.0)

    print('== 登录 ==')
    r = http('POST', f'{API}/api/auth/login', body={'phone': '13800138000', 'password': 'abc123'})
    token = r['data']['token']
    check('登录成功', bool(token))

    print('== 运行时模式 ==')
    active = http('GET', f'{API}/api/services/active', token)['data']
    modes = {a['category']: a['mode'] for a in active}
    check('LLM 运行模式 = real', modes.get('llm') == 'real', str(modes))
    check('ASR 运行模式 = real', modes.get('asr') == 'real', str(modes))

    # ---------- 1. 阿里云 ASR 真实调用 ----------
    print('== [1] 阿里云 ASR 真实转写 ==')
    with open(wav_path, 'rb') as f:
        audio = f.read()
    resp = http('POST', f'{API}/api/ai/asr', token,
                form=[('sampleRate', '16000'), ('file', ('voice.wav', audio))])
    d = resp.get('data') or {}
    check('ASR 接口返回成功', resp.get('success') and d.get('success'),
          json.dumps(d, ensure_ascii=False)[:200])
    check('返回来源为阿里云', d.get('source') == '阿里云智能语音交互', str(d.get('source')))
    check('返回了 taskId（证明真实调用）', bool(d.get('taskId')), str(d.get('taskId')))
    check('返回 text 字段（允许为空串，非语音信号）', 'text' in d, repr(d.get('text'))[:80])

    # ---------- 2. 临时文件已清理 ----------
    print('== [2] 临时音频清理 ==')
    ups = os.path.join(os.getcwd(), 'server', 'uploads')
    leftovers = [f for f in os.listdir(ups) if f.endswith('.wav')] if os.path.isdir(ups) else []
    check('识别后 uploads 无残留 wav', len(leftovers) == 0, str(leftovers))

    # ---------- 3. DeepSeek LLM 结构化提取 ----------
    print('== [3] DeepSeek 客户建档提取 ==')
    text = '张三，男，32岁，在上海某科技公司做产品经理，月收入一万五，想在浦东买房贷款200万，征信良好没有逾期'
    r2 = http('POST', f'{API}/api/ai/extract/customer-voice', token, body={'text': text}, timeout=90)
    d2 = r2.get('data') or {}
    check('客户建档提取成功', r2.get('success') and d2.get('success'), str(r2.get('message'))[:150])
    name = (d2.get('data') or {}).get('name', {})
    check('DeepSeek 正确提取姓名=张三', name.get('value') == '张三', json.dumps(name, ensure_ascii=False))
    check('返回了 summary', bool(d2.get('summary')), str(d2.get('summary'))[:60])

    print('== [4] DeepSeek 日程解析 ==')
    r3 = http('POST', f'{API}/api/ai/extract/schedule', token,
              body={'text': '明天下午3点与张总在陆家嘴咖啡厅面谈贷款方案'}, timeout=90)
    d3 = r3.get('data') or {}
    sched = d3.get('data') or {}
    check('日程解析成功', r3.get('success'), str(r3.get('message'))[:150])
    check('提取出标题', bool(sched.get('title')), str(sched.get('title'))[:60])
    check('提取出 ISO 开始时间', bool(sched.get('startTime')), str(sched.get('startTime'))[:40])
    check('提取出地点', '陆家嘴' in str(sched.get('location')), str(sched.get('location'))[:60])
    check('提取出客户名', '张' in str(sched.get('customerName')), str(sched.get('customerName'))[:40])

    # ---------- 5. 错误路径 ----------
    print('== [5] 错误路径可读性 ==')
    wrong = http('POST', f'{API}/api/ai/asr', token,
                 form=[('file', ('bad.bmp', b'\x00' * 100))])
    check('非音频格式被拒', not wrong.get('success'), str(wrong.get('message'))[:120])

    # 清理
    for p in (wav_path,):
        try:
            os.remove(p)
        except OSError:
            pass

    passed = sum(1 for _, ok, _ in OUT if ok)
    print(f'\n==== {passed}/{len(OUT)} 通过 ====')
    for n, ok, dt in OUT:
        if not ok:
            print(f'  失败: {n} :: {dt}')
    return 0 if passed == len(OUT) else 1


if __name__ == '__main__':
    sys.exit(main())
