# -*- coding: utf-8 -*-
"""冒烟：直达后台地址 → 登录 → 应回到 #/admin/dashboard（而非移动端 /home）"""
import json, subprocess, time, urllib.request, sys, os

BASE = "http://127.0.0.1:3001"
PORT = 9361
PROFILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".qa_chrome_adminfix")
PROCS = []

def kill_chrome():
    try:
        subprocess.run(["taskkill", "/F", "/IM", "chrome.exe", "/FI",
                        f"WINDOWTITLE eq qa_adminfix*"], capture_output=True, timeout=10)
    except Exception:
        pass

def cdp_connect(port):
    for _ in range(30):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=2) as r:
                v = json.loads(r.read())
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
        self.mid += 1
        mid = self.mid
        self.ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == mid:
                return msg.get("result", {})
    def eval(self, expr, fire=False):
        p = {"expression": expr, "returnByValue": True, "awaitPromise": False}
        if fire:
            self.send("Runtime.evaluate", p)
            return None
        r = self.send("Runtime.evaluate", p)
        return r.get("result", {}).get("value")

def find_chrome():
    for p in (r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
              os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")):
        if os.path.exists(p):
            return p
    raise RuntimeError("chrome not found")

def main():
    passed = failed = 0
    def check(name, cond):
        nonlocal passed, failed
        print(("PASS " if cond else "FAIL ") + name)
        passed += cond; failed += (not cond)

    chrome = find_chrome()
    args = [chrome, "--headless=new", "--remote-debugging-port=%d" % PORT,
            "--remote-allow-origins=*", "--no-first-run", "--no-default-browser-check",
            "--window-size=1440,900", "--user-data-dir=" + os.path.abspath(PROFILE),
            "about:blank"]
    proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    PROCS.append(proc)
    try:
        ws = cdp_connect(PORT)
        c = CDP(ws)
        c.send("Page.enable"); c.send("Runtime.enable")

        # 1) 未登录直达后台
        c.eval("location.href = '%s/#/admin/dashboard'" % BASE, fire=True)
        time.sleep(3)
        url = c.eval("location.hash") or ""
        check("未登录直达后台 → 落在登录页", "/login" in url)
        check("登录页携带 redirect 参数", "redirect" in url)

        # 2) 登录
        ok = c.eval("""(async () => {
          const doLogin = () => {
            const phone = document.querySelector('input[type=tel], input[placeholder*="手机"]')
            const pwd = document.querySelector('input[type=password]')
            if (!phone || !pwd) return false
            const set = (el, v) => {
              const proto = Object.getPrototypeOf(el)
              const desc = Object.getOwnPropertyDescriptor(proto, 'value')
              desc.set.call(el, v)
              el.dispatchEvent(new Event('input', { bubbles: true }))
            }
            set(phone, '13800138000'); set(pwd, 'abc123')
            return true
          }
          if (!doLogin()) return 'no-input'
          const btns = [...document.querySelectorAll('button')]
          const btn = btns.find(b => /登\s*录|登录/.test(b.textContent)) || btns.find(b => b.type === 'submit')
          if (!btn) return 'no-btn'
          btn.click()
          return 'clicked'
        })()""")
        print("login action:", ok)
        time.sleep(4)
        url = c.eval("location.hash") or ""
        check("登录后回到后台 dashboard（非移动端 /home）", "/admin/dashboard" in url)
        body = c.eval("document.body.innerText.slice(0, 600)") or ""
        check("页面渲染后台布局（数据看板）", ("数据看板" in body) or ("管理后台" in body))
        # 移动端 tabbar 不应出现
        has_tabbar = c.eval("!!document.querySelector('.tabbar, .home-tabbar, .main-tabbar')")
        check("未渲染移动端 tabbar", not has_tabbar)

        # 3) 已登录状态再开后台地址 → 直接进入
        c.eval("location.href = '%s/#/admin/services'" % BASE, fire=True)
        time.sleep(3)
        url = c.eval("location.hash") or ""
        body = c.eval("document.body.innerText.slice(0, 600)") or ""
        check("已登录直达 /admin/services 正常进入", "/admin/services" in url and ("三方服务" in body or "服务商" in body))

        print("\n%d passed, %d failed" % (passed, failed))
        sys.exit(1 if failed else 0)
    finally:
        try: proc.kill()
        except Exception: pass

if __name__ == "__main__":
    main()
