#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
首页「今日日程」卡片内联详情弹框 - 交互验证
- 点击首页日程卡片：不跳路由，当前页打开详情弹框
- 弹框内容与卡片一致（标题/时间/优先级）
- 标记完成：请求发出、弹框收起、首页列表刷新
- 删除：确认后弹框收起、卡片消失
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

import websocket

BASE = 'http://127.0.0.1:5173'
API = 'http://127.0.0.1:3001'
CDP_PORT = 9333


def http(method, url, token=None, body=None):
    """轻量 HTTP 封装：避免依赖 requests（隔离 venv 未安装）"""
    data = json.dumps(body, ensure_ascii=False).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header('Content-Type', 'application/json')
    if token:
        req.add_header('X-Auth-Token', token)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode() or '{}')
CHROME = None
for p in [
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
    os.path.expanduser(r'~\AppData\Local\Google\Chrome\Application\chrome.exe'),
]:
    if os.path.exists(p):
        CHROME = p
        break
assert CHROME, 'Chrome not found'

USER_DIR = os.path.join(os.getcwd(), '.qa_chrome_home_detail')
PROFILE = os.path.join(os.getcwd(), 'qa_probe_home_detail.json')
PHONE = '13800138000'
PWD = 'abc123'

results = []

# popup 是否真正可见（Vant 关闭后 DOM 会保留但 display:none，必须看计算样式）
POPUP_VISIBLE = """
(() => {
  const p = document.querySelector('.detail-popup');
  if (!p) return false;
  const s = getComputedStyle(p);
  if (s.display === 'none' || s.visibility === 'hidden' || s.opacity === '0') return false;
  const r = p.getBoundingClientRect();
  return r.height > 0 && r.top < window.innerHeight;
})()
"""


def check(name, cond, detail=''):
    results.append((name, bool(cond), detail))
    print(('  [PASS] ' if cond else '  [FAIL] ') + name + (f' :: {detail}' if detail else ''))
    return bool(cond)


class CDP:
    def __init__(self, ws_url):
        self.ws = websocket.create_connection(ws_url, timeout=30)
        self.i = 0
        self.console_errors = []

    def drain(self, timeout=0.05):
        """非阻塞收取事件，累计控制台错误"""
        self.ws.settimeout(timeout)
        try:
            while True:
                msg = json.loads(self.ws.recv())
                m = msg.get('method')
                if m == 'Runtime.exceptionThrown':
                    d = msg['params']['exceptionDetails']
                    self.console_errors.append('exception: ' + str(d.get('text', '')))
                elif m == 'Runtime.consoleAPICalled' and msg['params'].get('type') == 'error':
                    args = msg['params'].get('args', [])
                    self.console_errors.append(
                        'console.error: ' + ' '.join(str(a.get('value', '')) for a in args))
        except Exception:
            pass
        finally:
            self.ws.settimeout(30)

    def send(self, method, params=None, timeout=30):
        self.i += 1
        mid = self.i
        self.ws.send(json.dumps({'id': mid, 'method': method, 'params': params or {}}))
        end = time.time() + timeout
        while time.time() < end:
            msg = json.loads(self.ws.recv())
            if msg.get('id') == mid:
                if 'error' in msg:
                    raise RuntimeError(f'{method}: {msg["error"]}')
                return msg.get('result', {})
        raise TimeoutError(method)

    def eval(self, expr, timeout=30):
        r = self.send('Runtime.evaluate', {
            'expression': expr, 'returnByValue': True, 'awaitPromise': True,
        }, timeout)
        res = r.get('result', {})
        if r.get('exceptionDetails'):
            raise RuntimeError(r['exceptionDetails'].get('text', '') + ' :: '
                               + str(res.get('description', '')))
        return res.get('value')

    def wait(self, expr, timeout=15, interval=0.3):
        end = time.time() + timeout
        while time.time() < end:
            try:
                if self.eval(expr):
                    return True
            except Exception:
                pass
            time.sleep(interval)
        return False


def main():
    print('== 启动 Chrome ==')
    proc = subprocess.Popen([
        CHROME, '--headless=new', f'--remote-debugging-port={CDP_PORT}',
        '--remote-allow-origins=*', f'--user-data-dir={USER_DIR}',
        '--window-size=390,844', '--hide-scrollbars', '--no-first-run',
        '--disable-gpu', '--no-default-browser-check', 'about:blank',
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    try:
        for _ in range(60):
            try:
                urllib.request.urlopen(f'http://127.0.0.1:{CDP_PORT}/json/version', timeout=2)
                break
            except Exception:
                time.sleep(0.5)
        else:
            raise RuntimeError('Chrome CDP not ready')

        tgt = json.loads(urllib.request.urlopen(
            urllib.request.Request(f'http://127.0.0.1:{CDP_PORT}/json/new?about:blank',
                                   method='PUT'), timeout=5).read())
        cdp = CDP(tgt['webSocketDebuggerUrl'])
        cdp.send('Page.enable')
        cdp.send('Runtime.enable')
        cdp.send('Console.enable')

        # ---- 注入登录态 ----
        print('== 准备登录态 ==')
        r = http('POST', f'{API}/api/auth/login',
                 body={'phone': PHONE, 'password': PWD})
        token = r['data']['token']
        user = r['data']['user']
        cdp.send('Page.navigate', {'url': BASE})
        time.sleep(2)
        cdp.eval(f"localStorage.setItem('token', {json.dumps(token)});"
                 f"localStorage.setItem('userInfo', {json.dumps(json.dumps(user))});"
                 "'ok'")

        # ---- 准备一条今日日程 ----
        print('== 准备今日日程数据 ==')
        # 清掉之前的测试数据
        existing = http('GET', f'{API}/api/schedules', token)['data']
        for s in existing:
            if str(s.get('title', '')).startswith('[QA]'):
                http('DELETE', f'{API}/api/schedules/{s["id"]}', token)
        # 用 ISO 时间（与前端 Create.vue 的 toISOString() 一致），保证落在「今日」窗口内
        now = time.localtime()
        base = time.mktime((now.tm_year, now.tm_mon, now.tm_mday, 14, 0, 0, 0, 0, -1))
        iso = lambda ts: time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(ts)) + '+08:00'
        created = http('POST', f'{API}/api/schedules', token, {
            'title': '[QA] 首页详情交互验证',
            'startTime': iso(base),
            'endTime': iso(base + 3600),
            'reminderTime': iso(base - 1800),
            'priority': 'P0',
            'type': 'meeting',
            'location': '总部 3 楼会议室',
            'customerName': '张伟',
            'remark': '验证首页内联详情弹框',
        })
        sid = (created.get('data') or {}).get('id')
        if not sid:
            print('  创建日程失败:', created)
        check('测试日程创建成功', sid is not None, f'id={sid}')

        # ---- 打开首页 ----
        cdp.send('Page.navigate', {'url': f'{BASE}/#/home'})
        time.sleep(3)
        cdp.wait("document.querySelectorAll('.schedule-row').length > 0", timeout=15)

        url_before = cdp.eval('location.href')
        rows = cdp.eval("document.querySelectorAll('.schedule-row').length")
        check('首页渲染今日日程卡片', rows > 0, f'{rows} 条')

        # 找到 QA 那条并点击
        cdp.eval("""
          (() => {
            const rows = [...document.querySelectorAll('.schedule-row')];
            const t = rows.find(r => r.querySelector('.i-title')?.textContent.includes('[QA]'));
            window.__qaRow = t;
            return t ? t.querySelector('.i-title').textContent.trim() : null;
          })()
        """)
        card_title = cdp.eval("window.__qaRow?.querySelector('.i-title')?.textContent?.trim()")
        check('目标卡片存在', card_title is not None, card_title)
        cdp.eval("window.__qaRow.click(); 'clicked'")
        time.sleep(1.2)

        # ---- 断言 1：路由未跳转 ----
        url_after = cdp.eval('location.href')
        check('点击后未离开首页（仍在 #/home）', '#/home' in url_after, url_after)

        # ---- 断言 2：详情弹框打开 ----
        popup_open = cdp.eval(POPUP_VISIBLE)
        check('当前页打开详情弹框', popup_open)
        if not popup_open:
            print('   popup 状态:', cdp.eval(
                "(()=>{const p=document.querySelector('.detail-popup');"
                "return p?JSON.stringify(getComputedStyle(p).display):'NOT_IN_DOM'})()"))

        dp_title = cdp.eval("document.querySelector('.dp-title-text')?.textContent?.trim()")
        check('弹框标题与卡片一致', dp_title == card_title, f'弹框={dp_title} 卡片={card_title}')

        dp_meta = cdp.eval("""
          (() => {
            const rows = [...document.querySelectorAll('.dp-row')].map(r => ({
              lbl: r.querySelector('.dp-lbl')?.textContent?.trim(),
              val: r.querySelector('.dp-val')?.textContent?.trim(),
            }));
            return JSON.stringify(rows);
          })()
        """)
        meta = json.loads(dp_meta)
        labels = [m['lbl'] for m in meta]
        check('弹框展示 时间/地点/客户/提醒/备注', 
              all(k in labels for k in ['时间', '地点', '客户', '提醒', '备注']), str(labels))
        dp_tags = cdp.eval("""
          [...document.querySelectorAll('.dp-tag')].map(t => t.textContent.trim()).join('|')
        """)
        check('弹框标签含 紧急 P0 / 面谈 / 未完成',
              'P0' in dp_tags and '面谈' in dp_tags and '未完成' in dp_tags, dp_tags)
        check('底部提供「前往日程列表」次级入口',
              cdp.eval("!!document.querySelector('.dp-more')"))

        # ---- 断言 3：标记完成 ----
        print('== 验证「标记完成」 ==')
        btn_txt = cdp.eval("document.querySelector('.dp-actions .van-button')?.textContent?.trim()")
        check('主操作按钮文案为「标记完成」', '标记完成' in (btn_txt or ''), btn_txt)
        cdp.eval("document.querySelector('.dp-actions .van-button').click(); 'ok'")
        time.sleep(2.5)
        done_state = http('GET', f'{API}/api/schedules', token)['data']
        row = next((s for s in done_state if s['id'] == sid), None)
        check('后端已置为完成', row and row.get('done') in (1, True), str(row and row.get('done')))
        still_open = cdp.eval(POPUP_VISIBLE)
        rows_now = cdp.eval("document.querySelectorAll('.schedule-row').length")
        check('完成后弹框收起', not still_open, f'仍可见={still_open}')
        check('卡片从今日未完成列表移除', rows_now == rows - 1, f'{rows} -> {rows_now}')

        # ---- 断言 4：还原 + 删除 ----
        print('== 验证「删除日程」 ==')
        http('PATCH', f'{API}/api/schedules/{sid}', token, {'done': False})
        cdp.send('Page.navigate', {'url': f'{BASE}/#/home'})
        time.sleep(3)
        cdp.eval("""
          (() => {
            const rows = [...document.querySelectorAll('.schedule-row')];
            const t = rows.find(r => r.querySelector('.i-title')?.textContent.includes('[QA]'));
            if (t) t.click();
            return !!t;
          })()
        """)
        time.sleep(1.2)
        check('重新打开详情弹框', cdp.eval(POPUP_VISIBLE))
        cdp.eval("document.querySelector('.dp-delete').click(); 'ok'")
        time.sleep(0.8)
        # 确认弹窗
        dlg = cdp.eval("document.querySelector('.van-dialog__confirm') ? true : false")
        check('删除前弹出二次确认', dlg)
        if dlg:
            cdp.eval("document.querySelector('.van-dialog__confirm').click(); 'ok'")
            time.sleep(2.5)
        left = http('GET', f'{API}/api/schedules', token)['data']
        check('后端已删除该日程', not any(s['id'] == sid for s in left))
        check('删除后弹框收起', not cdp.eval(POPUP_VISIBLE))

        # ---- 断言 5：层级正确 + 无控制台错误 ----
        print('== 验证层级与运行时健康 ==')
        cdp.send('Page.navigate', {'url': f'{BASE}/#/home'})
        time.sleep(3)
        requests_data = cdp.eval("""
          (() => {
            const rows = [...document.querySelectorAll('.schedule-row')];
            if (rows.length) rows[0].click();
            return rows.length;
          })()
        """)
        time.sleep(1.2)
        if requests_data:
            z = cdp.eval("""
              (() => {
                const p = document.querySelector('.detail-popup');
                const tab = document.querySelector('.van-tabbar');
                const pr = p ? p.parentElement.className || p.parentElement.tagName : null;
                return JSON.stringify({
                  popupParent: pr,
                  popupZ: p ? +getComputedStyle(p).zIndex : null,
                  tabbarZ: tab ? +getComputedStyle(tab).zIndex : null,
                  overlayParent: document.querySelector('.van-overlay')
                    ? (document.querySelector('.van-overlay').parentElement.id
                       || document.querySelector('.van-overlay').parentElement.tagName) : null,
                });
              })()
            """)
            import json as _j
            info = _j.loads(z)
            check('弹层挂载到 body（脱离内容容器）', info['overlayParent'] == 'BODY', str(info))
            check('弹层层级高于底部导航',
                  info['popupZ'] and info['tabbarZ'] and info['popupZ'] > info['tabbarZ'],
                  f"popup={info['popupZ']} tabbar={info['tabbarZ']}")

        cdp.drain()
        errs = cdp.console_errors
        check('页面无控制台错误/异常', len(errs) == 0, '; '.join(errs[:3]))

        # 截图
        shot = cdp.send('Page.captureScreenshot', {'format': 'png', 'captureBeyondViewport': False})
        import base64
        with open('qa_home_detail_after.png', 'wb') as f:
            f.write(base64.b64decode(shot['data']))
        print('  截图: qa_home_detail_after.png')

    finally:
        try:
            proc.terminate()
        except Exception:
            pass

    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f'\n==== 结果：{passed}/{total} 通过 ====')
    for n, ok, d in results:
        if not ok:
            print(f'  失败: {n} :: {d}')
    return 0 if passed == total else 1


if __name__ == '__main__':
    sys.exit(main())
