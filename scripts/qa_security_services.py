# -*- coding: utf-8 -*-
"""冒烟：1) Security 角色权限矩阵 tab 点击切换 2) Services ASR 编辑回显掩码"""
import json, subprocess, time, urllib.request, sys, os

urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))
BASE = "http://127.0.0.1:3001"
PORT = 9369
PROFILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                       ".qa_chrome_sec_%d" % (time.time() * 1000 % 1e9))
import websocket

def cdp_connect(port):
    for _ in range(30):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list", timeout=2) as r:
                tabs = json.loads(r.read())
            page = next(t for t in tabs if t["type"] == "page")
            return websocket.create_connection(page["webSocketDebuggerUrl"], timeout=10)
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
        dl = time.time() + 15
        while True:
            if time.time() > dl:
                raise RuntimeError("CDP timeout: " + method)
            try:
                msg = json.loads(self.ws.recv())
            except websocket.WebSocketTimeoutException:
                continue
            if msg.get("id") == mid:
                return msg.get("result", {})
    def eval(self, expr, fire=False):
        p = {"expression": expr, "returnByValue": True, "awaitPromise": False}
        if fire:
            self.send("Runtime.evaluate", p)
            return None
        return self.send("Runtime.evaluate", p).get("result", {}).get("value")
    def wait_ready(self, timeout=25):
        dl = time.time() + timeout
        while time.time() < dl:
            try:
                if self.eval("document.readyState") == "complete":
                    return True
            except Exception:
                pass
            time.sleep(0.5)
        return False
    def click_at(self, x, y):
        for t, btn in (("mousePressed", "left"), ("mouseReleased", "left")):
            self.send("Input.dispatchMouseEvent", {"type": t, "x": x, "y": y, "button": btn, "clickCount": 1})

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
    proc = subprocess.Popen([chrome, "--headless=new", "--remote-debugging-port=%d" % PORT,
                             "--remote-allow-origins=*", "--no-first-run", "--no-default-browser-check",
                             "--window-size=1440,900", "--user-data-dir=" + os.path.abspath(PROFILE),
                             "about:blank"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        c = CDP(cdp_connect(PORT))
        c.send("Page.enable"); c.send("Runtime.enable")

        c.eval("location.href = '%s/#/login'" % BASE, fire=True)
        time.sleep(1); c.wait_ready()
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
        c.eval("location.href = '%s/#/admin/security'" % BASE, fire=True)
        time.sleep(2); c.wait_ready(); time.sleep(3)

        # ---- 问题 2：角色权限矩阵 tab 点击 ----
        n_tabs = c.eval("document.querySelectorAll('.role-tab').length") or 0
        check("角色 tab 渲染 3 个", n_tabs == 3)
        names = c.eval("[...document.querySelectorAll('.role-tab')].map(b => b.textContent.trim())") or []
        check("tab 文本含团队主管/贷款经理", "团队主管" in names and "贷款经理" in names)

        def active_name():
            return c.eval("document.querySelector('.role-tab.active')?.textContent.trim()") or ""
        desc = lambda: c.eval("document.querySelector('.role-desc')?.textContent.trim()") or ""
        # 注意：矩阵渲染的是权限目录全集（16 个 checkbox），应断言「勾选数」而非元素总数
        n_boxes = lambda: c.eval("document.querySelectorAll('.perm-groups input[type=checkbox]').length") or 0
        n_checked = lambda: c.eval("[...document.querySelectorAll('.perm-groups input[type=checkbox]')].filter(b => b.checked).length") or 0

        check("初始 active=管理员", active_name() == "管理员")
        d0, b0, k0 = desc(), n_boxes(), n_checked()

        # 真实鼠标点击「团队主管」
        box = c.eval("""(() => { const el = [...document.querySelectorAll('.role-tab')].find(b => b.textContent.trim() === '团队主管'); if (!el) return null; const r = el.getBoundingClientRect(); return { x: r.x + r.width / 2, y: r.y + r.height / 2 } })()""")
        check("定位到团队主管 tab", bool(box))
        c.click_at(box["x"], box["y"]); time.sleep(1.2)
        check("点击后 active=团队主管", active_name() == "团队主管")
        check("角色描述已切换", desc() != d0 and len(desc()) > 0)
        check("权限矩阵勾选数变化(16→8)", b0 == 16 and k0 == 16 and n_checked() == 8)

        # 点击「贷款经理」
        box2 = c.eval("""(() => { const el = [...document.querySelectorAll('.role-tab')].find(b => b.textContent.trim() === '贷款经理'); if (!el) return null; const r = el.getBoundingClientRect(); return { x: r.x + r.width / 2, y: r.y + r.height / 2 } })()""")
        check("定位到贷款经理 tab", bool(box2))
        c.click_at(box2["x"], box2["y"]); time.sleep(1.2)
        check("点击后 active=贷款经理", active_name() == "贷款经理")
        check("贷款经理矩阵勾选数=1", n_checked() == 1)

        # 切回管理员（回归）
        box3 = c.eval("""(() => { const el = [...document.querySelectorAll('.role-tab')].find(b => b.textContent.trim() === '管理员'); const r = el.getBoundingClientRect(); return { x: r.x + r.width / 2, y: r.y + r.height / 2 } })()""")
        c.click_at(box3["x"], box3["y"]); time.sleep(1)
        check("切回管理员 active 恢复", active_name() == "管理员")

        # ---- 问题 1：Services ASR 编辑回显掩码 ----
        c.eval("location.href = '%s/#/admin/services'" % BASE, fire=True)
        time.sleep(2); c.wait_ready(); time.sleep(3)
        edit_btn = c.eval("""(() => {
          const rows = [...document.querySelectorAll('table tr')]
          for (const tr of rows) {
            if (tr.textContent.includes('阿里云') || tr.textContent.includes('语音')) {
              const btn = [...tr.querySelectorAll('button')].find(b => b.textContent.trim() === '编辑')
              if (btn) { const r = btn.getBoundingClientRect(); return { x: r.x + r.width / 2, y: r.y + r.height / 2 } }
            }
          }
          return null
        })()""")
        check("找到 ASR 供应商编辑按钮", bool(edit_btn))
        if edit_btn:
            c.click_at(edit_btn["x"], edit_btn["y"]); time.sleep(1.2)
            ph = c.eval("document.querySelector('input[placeholder*=\\'当前：\\']')?.placeholder") or ""
            hint = c.eval("[...document.querySelectorAll('.hint')].map(h => h.textContent).join('|')") or ""
            check("API Key 提示显示当前掩码", "当前：" in ph)
            check("AppKey 提示显示当前已配置掩码", "当前已配置：" in hint)
            # 关闭弹框（取消按钮）
            cancel = c.eval("""(() => { const b = [...document.querySelectorAll('button')].find(x => /取\\s*消/.test(x.textContent)); if (!b) return null; const r = b.getBoundingClientRect(); return { x: r.x + r.width / 2, y: r.y + r.height / 2 } })()""")
            if cancel: c.click_at(cancel["x"], cancel["y"])

        print("\n%d passed, %d failed" % (passed, failed))
        sys.exit(1 if failed else 0)
    finally:
        try: proc.kill()
        except Exception: pass

if __name__ == "__main__":
    main()
