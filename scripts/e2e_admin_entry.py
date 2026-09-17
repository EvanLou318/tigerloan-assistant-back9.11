# -*- coding: utf-8 -*-
# 管理后台入口按钮 e2e：
# 1) 未登录点击 → 出现提示 toast 且 URL 带 redirect=/admin
# 2) 登录成功 → 自动进入 /admin（而非 /home）
import json, time, subprocess, websocket, urllib.request, os, base64

CHROME = r"C:/Program Files/Google/Chrome/Application/chrome.exe"
PORT = 9242
BASE = "http://localhost:5173/"
OUT_DIR = r"C:/Users/madta/WorkBuddy/2026-08-19-12-24-26/loan-assistant/scripts/e2e_shots/admin_entry"
os.makedirs(OUT_DIR, exist_ok=True)
PASS, FAIL = [], []

def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("PASS " if cond else "FAIL ") + name + ((" | " + str(detail)[:150]) if (detail and not cond) else ""))

chrome = subprocess.Popen([
    CHROME, "--headless=new", f"--remote-debugging-port={PORT}",
    "--remote-allow-origins=*", "--disable-gpu", "--no-first-run",
    "--window-size=390,844", "about:blank",
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
send("Emulation.setDeviceMetricsOverride", {"width": 390, "height": 844, "deviceScaleFactor": 2, "mobile": True})

# 确保无登录态
send("Page.navigate", {"url": BASE + "#/login"})
time.sleep(2.5)
eval_js("localStorage.removeItem('token'); localStorage.removeItem('userInfo'); location.hash = '#/login'; location.reload()")
time.sleep(2)

# ---- 场景 1：未登录点击管理后台入口 ----
clicked = eval_js("""
(() => {
  const el = [...document.querySelectorAll('.admin-link')].find(s => s.textContent.includes('管理后台入口'));
  if (!el) return 'no-link';
  el.click();
  return 'clicked';
})()
""")
check("1.1 找到并点击管理后台入口", clicked == "clicked", clicked)
time.sleep(1.2)

url1 = eval_js("location.hash")
check("1.2 URL 记录 redirect=/admin", "redirect=%2Fadmin" in url1 or "redirect=/admin" in url1, url1)
toast1 = eval_js("document.body.innerText.includes('请先登录')")
check("1.3 出现「请先登录」提示", toast1 is True, toast1)
shot("01_not_logged_in_toast.png")

# ---- 场景 2：在带 redirect 的登录页登录 → 自动进入 /admin ----
filled = eval_js("""
(() => {
  const inputs = [...document.querySelectorAll('input.van-field__control')];
  if (inputs.length < 2) return 'no-inputs:' + inputs.length;
  const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
  setter.call(inputs[0], '13800138000');
  inputs[0].dispatchEvent(new Event('input', { bubbles: true }));
  setter.call(inputs[1], 'abc123');
  inputs[1].dispatchEvent(new Event('input', { bubbles: true }));
  return 'filled:' + inputs[0].value + ':' + inputs[1].value;
})()
""")
check("2.0 表单填充成功", str(filled).startswith("filled:13800138000:abc123"), filled)
time.sleep(0.5)
submit_r = eval_js("""
(() => {
  const btn = [...document.querySelectorAll('button')].find(b => b.textContent.replace(/\\s/g, '') === '登录');
  if (!btn) return 'no-btn';
  btn.click();
  return 'submitted';
})()
""")
check("2.0b 点击登录按钮", submit_r == "submitted", submit_r)
# 等待登录 + 跳转
deadline = time.time() + 15
final_hash = ""
while time.time() < deadline:
    final_hash = eval_js("location.hash") or ""
    if final_hash.startswith("#/admin"):
        break
    time.sleep(0.5)
check("2.1 登录后自动进入 /admin", final_hash.startswith("#/admin"), final_hash)
time.sleep(2)
admin_text = eval_js("(document.querySelector('.admin-shell, .admin-layout, main, #app')?.innerText || '').slice(0, 400)") or ""
check("2.2 管理后台页面已渲染（非登录页）", ("数据看板" in admin_text or "退出登录" in admin_text or "工作台" in admin_text), admin_text[:120])
shot("02_admin_after_login.png")

print(f"\n===== {len(PASS)} PASS / {len(FAIL)} FAIL =====")
if FAIL:
    print("FAILED:", FAIL)
ws.close()
chrome.kill()
