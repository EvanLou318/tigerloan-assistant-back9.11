# -*- coding: utf-8 -*-
"""冒烟：1) 首页日程卡片与日程页统一（ScheduleCard）2) 头像上传全链路"""
import json, subprocess, time, urllib.request, sys, os, struct, zlib

# 本机环境可能存在代理（导致访问 127.0.0.1 被 502），CDP/本地 API 一律直连
_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
urllib.request.install_opener(_opener)

BASE = "http://127.0.0.1:3001"
PORT = 9363
# 唯一 profile：避免上次残留的 SingletonLock 让 Chrome 秒退
PROFILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                       ".qa_chrome_cardfix_%d" % int(time.time() * 1000 % 1e9))

def cdp_connect(port):
    for _ in range(30):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list", timeout=2) as r:
                tabs = json.loads(r.read())
            page = next(t for t in tabs if t["type"] == "page")
            import websocket
            ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=8)
            return ws
        except Exception:
            time.sleep(0.5)
    raise RuntimeError("CDP connect failed")

class CDP:
    def __init__(self, ws):
        self.ws, self.mid = ws, 0
    def send(self, method, params=None):
        import websocket
        self.mid += 1
        mid = self.mid
        self.ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        deadline = time.time() + 15
        while True:
            if time.time() > deadline:
                raise RuntimeError("CDP send timeout: " + method)
            try:
                msg = json.loads(self.ws.recv())
            except websocket.WebSocketTimeoutException:
                continue  # 事件间隙，继续等响应
            if msg.get("id") == mid:
                return msg.get("result", {})
    def eval(self, expr, fire=False):
        p = {"expression": expr, "returnByValue": True, "awaitPromise": False}
        if fire:
            self.send("Runtime.evaluate", p)
            return None
        r = self.send("Runtime.evaluate", p)
        return r.get("result", {}).get("value")
    def set_file(self, selector, path):
        doc = self.send("DOM.getDocument", {"depth": -1})
        node = self.send("DOM.querySelector", {"nodeId": doc["root"]["nodeId"], "selector": selector})
        if not node.get("nodeId"):
            return False
        self.send("DOM.setFileInputFiles", {"files": [path], "nodeId": node["nodeId"]})
        return True

def find_chrome():
    for p in (r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
              os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")):
        if os.path.exists(p):
            return p
    raise RuntimeError("chrome not found")

def make_png(path):
    sig = b'\x89PNG\r\n\x1a\n'
    def chunk(t, d):
        c = struct.pack('>I', len(d)) + t + d
        return c + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    data = sig + chunk(b'IHDR', struct.pack('>IIBBBBB', 4, 4, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(b'\x00' + b'\x33\x66\x99' * 4)) + chunk(b'IEND', b'')
    with open(path, 'wb') as f:
        f.write(data)

def main():
    passed = failed = 0
    def check(name, cond):
        nonlocal passed, failed
        print(("PASS " if cond else "FAIL ") + name)
        passed += cond; failed += (not cond)

    png_path = os.path.abspath(os.path.join(PROFILE, "_test_avatar.png"))
    os.makedirs(PROFILE, exist_ok=True)
    make_png(png_path)

    chrome = find_chrome()
    proc = subprocess.Popen([chrome, "--headless=new", "--remote-debugging-port=%d" % PORT,
                             "--remote-allow-origins=*", "--no-first-run", "--no-default-browser-check",
                             "--window-size=414,896", "--user-data-dir=" + os.path.abspath(PROFILE),
                             "about:blank"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        ws = cdp_connect(PORT)
        c = CDP(ws)
        c.send("Page.enable"); c.send("Runtime.enable"); c.send("DOM.enable")

        def wait_ready(timeout=20):
            """等页面主线程空闲（Vue 初始化会阻塞 evaluate）"""
            deadline = time.time() + timeout
            while time.time() < deadline:
                try:
                    state = c.eval("document.readyState")
                    if state == "complete":
                        return True
                except Exception:
                    pass
                time.sleep(0.5)
            return False

        # 两段式导航：写 token 再进首页
        c.eval("location.href = '%s/#/home'" % BASE, fire=True)
        time.sleep(1)
        wait_ready()
        c.eval("""(() => {
          const x = new XMLHttpRequest()
          x.open('POST', '/api/auth/login', false)
          x.setRequestHeader('Content-Type', 'application/json')
          x.send(JSON.stringify({ phone: '13800138000', password: 'abc123' }))
          const j = JSON.parse(x.responseText)
          localStorage.setItem('token', j.data.token)
          localStorage.setItem('userInfo', JSON.stringify(j.data.user))
          return 'ok'
        })()""")
        time.sleep(1)
        c.eval("location.href = '%s/#/home'" % BASE, fire=True)
        time.sleep(1)
        wait_ready()
        time.sleep(2)

        # 1) 首页日程卡片：新组件类名
        home_card = c.eval("!!document.querySelector('.schedule-list .schedule-card')")
        has_chip = c.eval("!!document.querySelector('.schedule-list .schedule-card .prio-chip')")
        has_tstart = c.eval("!!document.querySelector('.schedule-list .schedule-card .t-start')")
        old_style = c.eval("!!document.querySelector('.schedule-list .schedule-row')")
        check("首页渲染统一卡片 .schedule-card", home_card)
        check("首页卡片含优先级徽标 .prio-chip", has_chip)
        check("首页卡片含时间列 .t-start", has_tstart)
        check("首页旧卡片 .schedule-row 已移除", not old_style)

        # 2) 日程页卡片一致
        c.eval("location.hash = '#/schedules'", fire=True)
        time.sleep(3)
        list_card = c.eval("!!document.querySelector('.schedule-list .schedule-card')")
        list_chip = c.eval("!!document.querySelector('.schedule-list .schedule-card .prio-chip')")
        check("日程页渲染 .schedule-card", list_card)
        check("日程页卡片含 .prio-chip", list_chip)

        # 3) 头像上传全链路（真实 file input + DOM.setFileInputFiles）
        c.eval("location.hash = '#/profile'", fire=True)
        time.sleep(3)
        before = c.eval("(JSON.parse(localStorage.getItem('userInfo')||'{}').avatar) || ''") or ""
        ok_set = c.set_file('input[type="file"]', png_path)
        time.sleep(4)
        after = c.eval("(JSON.parse(localStorage.getItem('userInfo')||'{}').avatar) || ''") or ""
        img_shown = c.eval("!!document.querySelector('.avatar-img')")
        check("file input 设置成功", ok_set)
        check("头像地址已更新", bool(after) and after != before and after.startswith('/uploads/avatar_'))
        check("页面渲染出头像图片 .avatar-img", img_shown)
        # 回读文件
        s = None
        try:
            with urllib.request.urlopen(BASE + after, timeout=8) as resp:
                s = resp.status
        except Exception:
            s = None
        check("头像文件可访问(200)", s == 200)

        print("\n%d passed, %d failed" % (passed, failed))
        sys.exit(1 if failed else 0)
    finally:
        try: proc.kill()
        except Exception: pass

if __name__ == "__main__":
    main()
