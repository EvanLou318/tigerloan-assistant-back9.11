#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日程列表「日期范围筛选」交互验证（Chrome headless CDP）
- 快捷区间「近7天 / 近30天」过滤正确，再次点击取消
- 自定义范围（van-calendar 区间选择）过滤正确，徽标显示范围
- 选范围后自动从「今日」切到「全部」tab
- 点徽标 ✕ 清除筛选
数据：通过 API 预置 4 条 [QA] 日程（昨天 / 明天 / +10天 / +40天）
"""
import json
import os
import subprocess
import time
import urllib.error
import urllib.request

import websocket

BASE = 'http://127.0.0.1:3001'
API = 'http://127.0.0.1:3001'
CDP_PORT = 9337

results = []


def http(method, url, token=None, body=None):
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


def check(name, cond, detail=''):
    results.append((name, bool(cond), detail))
    print(('  [PASS] ' if cond else '  [FAIL] ') + name + (f' :: {detail}' if detail else ''))
    return bool(cond)


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

USER_DIR = os.path.join(os.getcwd(), '.qa_chrome_home_filter')


class CDP:
    def __init__(self, ws_url):
        self.ws = websocket.create_connection(ws_url, timeout=30)
        self.i = 0

    def send(self, method, params=None, timeout=30):
        self.i += 1
        mid = self.i
        self.ws.send(json.dumps({'id': mid, 'method': method, 'params': params or {}}))
        end = time.time() + timeout
        while time.time() < end:
            try:
                self.ws.settimeout(max(0.5, end - time.time()))
                msg = json.loads(self.ws.recv())
            except websocket.WebSocketTimeoutException:
                continue  # 事件间隙里 recv 会超时，未到总 deadline 就继续等
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

    def eval_fire(self, expr):
        """发射后不管：用于会触发页面刷新/跳转的表达式（上下文销毁后响应不会回来，
        等待它会一直超时；后续 send() 会按 id 丢弃这条迟到响应）"""
        self.i += 1
        self.ws.send(json.dumps({'id': self.i, 'method': 'Runtime.evaluate',
                                 'params': {'expression': expr, 'returnByValue': True}}))

    def mouse_click(self, x, y):
        """真实鼠标事件：Vant 日历对合成 .click() 的响应不稳定"""
        for t in ('mousePressed', 'mouseReleased'):
            self.send('Input.dispatchMouseEvent',
                      {'type': t, 'x': x, 'y': y, 'button': 'left', 'clickCount': 1})

    def selected_days(self):
        """当前日历选中格（带 开始/结束 标记），用于校验点击是否生效"""
        return self.eval("""
          [...document.querySelectorAll('.van-calendar__day')]
            .filter(e => [...e.classList].some(c => /--start$|--end$/.test(c)))
            .map(e => e.textContent.trim())
        """)

    def click_day_until(self, day, month_title, expect):
        """点击后校验选中状态；偶发丢失就重试（最多 4 次）"""
        for _ in range(4):
            self.click_day(day, month_title)
            time.sleep(1)
            sel = self.selected_days() or []
            if all(any(s.startswith(e) for s in sel) for e in expect):
                return True
        return False

    def click_day(self, day, month_title):
        """每次重新定位格子坐标再点击（Vue 重渲染会替换元素，缓存引用会失效）"""
        pos = self.eval(f"""
          (() => {{
            const months = [...document.querySelectorAll('.van-calendar__month')];
            const m = months.find(el => (el.querySelector('.van-calendar__month-title')?.textContent || '').includes('{month_title}'));
            if (!m) return null;
            const cell = [...m.querySelectorAll('.van-calendar__day')].find(e =>
              e.textContent.trim().replace(/(开始|结束)$/, '') === '{day}' && !e.className.includes('disabled'));
            if (!cell) return null;
            const r = cell.getBoundingClientRect();
            return {{x: r.x + r.width / 2, y: r.y + r.height / 2}};
          }})()
        """)
        if not pos:
            return False
        self.mouse_click(pos['x'], pos['y'])
        return True

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


def qa_cards(cdp):
    """当前列表里的 [QA] 日程标题（按顺序）"""
    return cdp.eval("""
      [...document.querySelectorAll('.schedule-card .title-text')]
        .map(t => t.textContent.trim())
        .filter(t => t.startsWith('[QA]'))
    """)


def click_tab(cdp, label):
    return cdp.eval(f"""
      (() => {{
        const t = [...document.querySelectorAll('.tab-item')].find(e => e.textContent.includes('{label}'));
        if (!t) return 'NO_TAB';
        t.click();
        return 'OK';
      }})()
    """)


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

        # ---- 登录 ----
        r = http('POST', f'{API}/api/auth/login', body={'phone': '13800138000', 'password': 'abc123'})
        token = r['data']['token']
        user = r['data']['user']

        # ---- 准备 4 条 [QA] 日程：昨天 / 明天 / +10天 / +40天 ----
        print('== 预置日程数据 ==')
        existing = http('GET', f'{API}/api/schedules', token)['data']
        for s in existing:
            if str(s.get('title', '')).startswith('[QA]'):
                http('DELETE', f'{API}/api/schedules/{s["id"]}', token)

        iso = lambda ts: time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(ts)) + '+08:00'
        day = lambda n: time.mktime(time.strptime(
            time.strftime('%Y-%m-%d', time.localtime(time.time() + n * 86400)), '%Y-%m-%d'))

        plan = [(-5, '昨天'), (1, '明天'), (10, '十天后'), (40, '四十天后')]
        ids = {}
        for offset, label in plan:
            base = day(offset) + 14 * 3600
            created = http('POST', f'{API}/api/schedules', token, {
                'title': f'[QA] {label}的日程',
                'startTime': iso(base),
                'endTime': iso(base + 3600),
                'reminderTime': iso(base - 1800),
                'priority': 'P1',
                'type': 'task',
            })
            ids[label] = (created.get('data') or {}).get('id')
        check('4 条 [QA] 日程创建成功', all(ids.values()), str(ids))

        # ---- 两段式导航：先落域，写 token，再整页跳到目标路由（每次导航独立完成） ----
        bust = f'?_={int(time.time())}'
        cdp.send('Page.navigate', {'url': f'{BASE}/{bust}#/login'})
        if not cdp.wait("location.host.includes('127.0.0.1:3001')", timeout=20):
            raise RuntimeError('首次导航未落到应用')
        cdp.eval(f"localStorage.setItem('token', {json.dumps(token)});"
                 f"localStorage.setItem('userInfo', {json.dumps(json.dumps(user))}); 'ok'")
        bust2 = f'?_b={int(time.time()) + 1}'
        cdp.send('Page.navigate', {'url': f'{BASE}/{bust2}#/schedules'})
        time.sleep(2)
        if not cdp.wait("!!document.querySelector('.schedule-page')", timeout=15):
            diag = cdp.eval(
                "JSON.stringify({url: location.href, body: document.body.innerText.slice(0, 120)})")
            raise RuntimeError(f'日程页未渲染 :: {diag}')
        click_tab(cdp, '全部')
        time.sleep(0.6)

        titles = qa_cards(cdp)
        check('未筛选时 4 条 [QA] 全部可见', len(titles) == 4, str(titles))

        # ---- 近7天 ----
        print('== 快捷区间：近7天 ==')
        click_tab(cdp, '今日')
        time.sleep(0.4)
        cdp.eval("""
          [...document.querySelectorAll('.filter-chip')].find(e => e.textContent.includes('近7天')).click(); 'ok'
        """)
        time.sleep(0.5)
        check('选范围后自动切到「全部」tab', cdp.eval(
            "[...document.querySelectorAll('.tab-item')].find(e => e.classList.contains('active'))?.textContent.includes('全部')"
        ) is True)
        titles = qa_cards(cdp)
        check('近7天只显示明天(+1d)的日程', titles == ['[QA] 明天的日程'], str(titles))

        # 再点一次取消
        cdp.eval("""
          [...document.querySelectorAll('.filter-chip')].find(e => e.textContent.includes('近7天')).click(); 'ok'
        """)
        time.sleep(0.5)
        check('再次点击近7天取消筛选', len(qa_cards(cdp)) == 4)

        # ---- 近30天 ----
        print('== 快捷区间：近30天 ==')
        cdp.eval("""
          [...document.querySelectorAll('.filter-chip')].find(e => e.textContent.includes('近30天')).click(); 'ok'
        """)
        time.sleep(0.5)
        titles = qa_cards(cdp)
        check('近30天显示明天+十天后的日程', set(titles) == {'[QA] 明天的日程', '[QA] 十天后的日程'}, str(titles))
        cdp.eval("""
          [...document.querySelectorAll('.filter-chip')].find(e => e.textContent.includes('近30天')).click(); 'ok'
        """)
        time.sleep(0.4)

        # ---- 自定义范围：本月 12 日 ~ 25 日（覆盖明天 12 号与 +10d 的 21 号） ----
        print('== 自定义范围（日历区间选择） ==')
        cdp.eval("""
          [...document.querySelectorAll('.filter-chip')].find(e => e.textContent.includes('自定义')).click(); 'ok'
        """)
        if not cdp.wait("!!document.querySelector('.van-calendar') && !!document.querySelector('.van-calendar__confirm')"):
            raise RuntimeError('日历弹层未出现')
        today = time.localtime()
        month_title = f'{today.tm_year}年{today.tm_mon}月'
        # 默认预选「今天~明天」：点 12 重新开始选（start=12），点 25 作为 end；
        # 鼠标事件偶发丢失，每步点击后校验选中状态，不对就重试
        r1 = cdp.click_day_until('12', month_title, ['12开始'])
        r2 = cdp.click_day_until('25', month_title, ['12开始', '25结束'])
        check('日历两天均选中', r1 and r2, f'12:{r1} 25:{r2}')
        confirm_disabled = cdp.eval("document.querySelector('.van-calendar__confirm')?.disabled")
        check('确认按钮已激活（范围完整）', confirm_disabled is False, str(confirm_disabled))
        cdp.eval("document.querySelector('.van-calendar__confirm').click(); 'ok'")
        time.sleep(0.8)
        badge = cdp.eval("document.querySelector('.range-badge')?.textContent.trim() || ''")
        check('范围徽标显示 9/12 ~ 9/25', f'{today.tm_mon}/12' in badge and f'{today.tm_mon}/25' in badge, badge)
        titles = qa_cards(cdp)
        check('自定义范围显示明天+十天后日程', set(titles) == {'[QA] 明天的日程', '[QA] 十天后的日程'}, str(titles))

        # ---- 点徽标清除 ----
        cdp.eval("document.querySelector('.range-badge').click(); 'ok'")
        time.sleep(0.5)
        check('点徽标清除筛选后 4 条全可见', len(qa_cards(cdp)) == 4)
        check('徽标消失', cdp.eval("!document.querySelector('.range-badge')") is True)

    finally:
        proc.terminate()
        # 清理测试数据
        try:
            r = http('POST', f'{API}/api/auth/login', body={'phone': '13800138000', 'password': 'abc123'})
            token = r['data']['token']
            for s in http('GET', f'{API}/api/schedules', token)['data']:
                if str(s.get('title', '')).startswith('[QA]'):
                    http('DELETE', f'{API}/api/schedules/{s["id"]}', token)
            print('== 测试数据已清理 ==')
        except Exception:
            pass

    failed = [n for n, ok, _ in results if not ok]
    print(f'\n===== 结果：{len(results) - len(failed)}/{len(results)} passed =====')
    if failed:
        print('FAILED:', failed)
        raise SystemExit(1)


if __name__ == '__main__':
    main()
