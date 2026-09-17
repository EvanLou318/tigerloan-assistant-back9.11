# -*- coding: utf-8 -*-
# 管理后台独立登录页 e2e：
# 1) 未登录直达 /admin/dashboard → 跳 /admin/login 并带 redirect
# 2) 移动端登录页「管理后台入口」→ /admin/login
# 3) 后台登录页登录 → 进入 /admin/dashboard（redirect 回跳生效）
import json, time, subprocess, websocket, urllib.request, os, base64

CHROME = r"C:/Program Files/Google/Chrome/Application/chrome.exe"
PORT = 9243
BASE = "http://localhost:5173/"
OUT_DIR = r"C:/Users/madta/WorkBuddy/2026-08-19-12-24-26/loan-assistant/scripts/e2e_shots/admin_login_v2"
os.makedirs(OUT_DIR, exist_ok=True)
PASS, FAIL = [], []

def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("PASS " if cond else "FAIL ") + name + ((" | " + str(detail)[:150]) if (detail and not cond) else ""))

chrome = subprocess.Popen([
    CHROME, "--headless=new", f"--remote-debugging-port={PORT}",
    "--remote-allow-origins=*", "--disable-gpu", "--no-first-run",
    "--window-size=1440,900", "about:blank",
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2.5)

tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json").read())
page = next(t for t in tabs if t["type"] == "page")
ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=60)
mid = [0]

def send(method, params=None):
    mid[0] += 1
    ws.send(json.dumps({"id": mid[0], "method": method, "params": params or {}}))
    while True:
        d = json.loads(ws.recv())
        if d.get("id") == mid[0]:
            return d

def eval_js(expr):
    res = send("Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True})
    r = res.get("result", {}).get("result", {})
    if r.get("subtype") == "error" or res.get("exceptionDetails"):
        return "__JS_ERROR__ " + str(res.get("exceptionDetails", {}).get("exception", {}).get("description", ""))
    return r.get("value")

def shot(name):
    res = send("Page.captureScreenshot", {"format": "png"})
    with open(os.path.join(OUT_DIR, name), "wb") as f:
        f.write(base64.b64decode(res["result"]["data"]))

send("Page.enable")
send("Runtime.enable")
send("Emulation.setDeviceMetricsOverride", {"width": 1440, "height": 900, "deviceScaleFactor": 1, "mobile": False})

# ---- 场景 1：未登录直达 /admin/dashboard → 后台登录页 ----
send("Page.navigate", {"url": BASE + "#/admin/dashboard"})
time.sleep(2.5)
eval_js("localStorage.removeItem('token'); localStorage.removeItem('userInfo');")
send("Page.navigate", {"url": BASE + "#/admin/dashboard"})
time.sleep(2.5)
h1 = eval_js("location.hash") or ""
check("1.1 未登录访问后台 → 跳后台登录页", h1.startswith("#/admin/login"), h1)
check("1.2 携带 redirect 回跳参数", "redirect=/admin/dashboard" in h1 or "redirect=%2Fadmin%2Fdashboard" in h1, h1)
check("1.3 后台登录页已渲染", (eval_js("document.body.innerText.includes('管理后台')") is True), "")
shot("01_admin_login.png")

# ---- 场景 2：移动端登录页入口按钮 → /admin/login ----
eval_js("location.hash = '#/login'; location.reload()")
time.sleep(2.5)
clicked = eval_js("""
(() => {
  const el = [...document.querySelectorAll('.admin-link')].find(s => s.textContent.includes('管理后台入口'));
  if (!el) return 'no-link';
  el.click();
  return 'clicked';
})()
""")
time.sleep(1.2)
h2 = eval_js("location.hash") or ""
check("2.1 点击移动端入口 → 后台登录页", clicked == "clicked" and h2.startswith("#/admin/login"), (clicked, h2))
shot("02_entry_to_admin_login.png")

# ---- 场景 3：后台登录页登录 → /admin/dashboard（redirect 生效）----
r_fill = eval_js("""
(() => {
  const inputs = [...document.querySelectorAll('input.van-field__control')];
  if (inputs.length < 2) return 'no-inputs:' + inputs.length;
  const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
  setter.call(inputs[0], '13800138000');
  inputs[0].dispatchEvent(new Event('input', { bubbles: true }));
  setter.call(inputs[1], 'abc123');
  inputs[1].dispatchEvent(new Event('input', { bubbles: true }));
  return 'filled';
})()
""")
check("3.0 表单填充成功", r_fill == "filled", r_fill)
r_btn = eval_js("""
(() => {
  const btn = [...document.querySelectorAll('button')].find(b => b.textContent.replace(/\\s/g, '') === '登录');
  if (!btn) return 'no-btn';
  btn.click();
  return 'submitted';
})()
""")
check("3.0b 点击登录按钮", r_btn == "submitted", r_btn)
deadline = time.time() + 15
final_hash = ""
while time.time() < deadline:
    final_hash = eval_js("location.hash") or ""
    if final_hash.startswith("#/admin/dashboard"):
        break
    time.sleep(0.5)
check("3.1 登录后按 redirect 进入 /admin/dashboard", final_hash.startswith("#/admin/dashboard"), final_hash)
time.sleep(2)
admin_text = eval_js("(document.querySelector('#app')?.innerText || '').slice(0, 500)") or ""
check("3.2 后台看板已渲染", ("数据看板" in admin_text or "客户管理" in admin_text), admin_text[:100])
shot("03_admin_dashboard.png")

print(f"\n===== {len(PASS)} PASS / {len(FAIL)} FAIL =====")
if FAIL:
    print("FAILED:", FAIL)
ws.close()
chrome.kill()
