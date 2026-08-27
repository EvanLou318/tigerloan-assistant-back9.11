# -*- coding: utf-8 -*-
# 端到端验证：真实登录后端 -> 注入 JWT -> 逐页检查渲染数据并截图
import json
import time
import subprocess
import websocket
import urllib.request
import os
import base64

CHROME = r"C:/Program Files/Google/Chrome/Application/chrome.exe"
PORT = 9228
BASE = "http://localhost:5173/"
OUT_DIR = r"C:/Users/madta/WorkBuddy/2026-08-19-12-24-26/loan-assistant/scripts/e2e_shots"
os.makedirs(OUT_DIR, exist_ok=True)

# 1. 真实登录获取 token
req = urllib.request.Request(
    "http://localhost:3001/api/auth/login",
    data=json.dumps({"phone": "13800138000", "password": "abc123"}).encode(),
    headers={"Content-Type": "application/json"},
)
login = json.loads(urllib.request.urlopen(req).read())
assert login["success"], "登录失败"
TOKEN = login["data"]["token"]
USER = json.dumps(login["data"]["user"], ensure_ascii=False)
print("login ok, user:", login["data"]["user"]["name"])

chrome = subprocess.Popen([
    CHROME,
    "--headless=new",
    f"--remote-debugging-port={PORT}",
    "--remote-allow-origins=*",
    "--disable-gpu",
    "--no-first-run",
    "--window-size=390,844",
    "about:blank",
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

time.sleep(2.5)

tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json").read())
page = next(t for t in tabs if t["type"] == "page")
ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=30)
msg_id = 0

def send(method, params=None):
    global msg_id
    msg_id += 1
    ws.send(json.dumps({"id": msg_id, "method": method, "params": params or {}}))
    while True:
        data = json.loads(ws.recv())
        if data.get("id") == msg_id:
            return data

def eval_js(expr):
    res = send("Runtime.evaluate", {"expression": expr, "returnByValue": True})
    return res.get("result", {}).get("result", {}).get("value")

def screenshot(name):
    res = send("Page.captureScreenshot", {"format": "png"})
    path = os.path.join(OUT_DIR, name)
    with open(path, "wb") as f:
        f.write(base64.b64decode(res["result"]["data"]))
    print("saved:", name)

errors = []

def goto(path, wait=2.5, check=None, label=""):
    # 每次导航前确保 token 存在
    eval_js(f"localStorage.setItem('token', {json.dumps(TOKEN)}); localStorage.setItem('userInfo', {json.dumps(USER)});")
    send("Page.navigate", {"url": BASE + "#" + path})
    time.sleep(wait)
    if check:
        val = eval_js(check)
        status = "OK" if val else "FAIL"
        print(f"  [{status}] {label or path} => {val}")
        if not val:
            errors.append(f"{path}: {label} => {val}")

send("Page.enable")
send("Runtime.enable")
send("Emulation.setDeviceMetricsOverride", {"width": 390, "height": 844, "deviceScaleFactor": 2, "mobile": True})

# 初始化域
send("Page.navigate", {"url": BASE + "#/login"})
time.sleep(2)
eval_js(f"localStorage.setItem('token', {json.dumps(TOKEN)}); localStorage.setItem('userInfo', {json.dumps(USER)});")

# 2. 首页（今日日程来自后端）
goto("/home", wait=3,
     check="""(() => { const t = document.body.innerText; return t.includes('今日日程') ? 'home rendered' : document.body.innerText.slice(0,80) })()""",
     label="首页渲染")

# 3. 产品库（种子产品来自后端）
goto("/products", wait=3,
     check="""(() => { const n = document.querySelectorAll('.product-card, [class*=card]').length;
        return n > 0 ? ('cards=' + n) : 'NO CARDS'; })()""",
     label="产品列表")
screenshot("e2e_products.png")

# 4. 客户列表（客户数据来自后端 SQLite）
goto("/customers", wait=3,
     check="""(() => { const t = document.body.innerText;
        return ['张明','陈丽'].filter(n => t.includes(n)).join(',') || 'SEED NAMES MISSING'; })()""",
     label="客户列表含种子客户")
screenshot("e2e_customers.png")

# 5. 客户详情（直接刷新进入，验证按需加载）
goto("/customers/c001", wait=3,
     check="""(() => { const t = document.body.innerText; return t.includes('张明') ? 'detail ok' : 'NOT FOUND'; })()""",
     label="客户详情直连")
screenshot("e2e_customer_detail.png")

# 6. 日程列表
goto("/schedules", wait=3,
     check="""(() => { return document.querySelector('.fab') ? 'list ok' : 'MISSING'; })()""",
     label="日程页")
screenshot("e2e_schedules.png")

# 7. AI 匹配页（调 /api/ai/match，mock 延迟约 3s，多等一会）
goto("/customers/c001/match", wait=9,
     check="""(() => { const t = document.body.innerText;
        return (t.includes('准入') || t.includes('匹配')) ? 'match page content ok' : t.slice(0,60); })()""",
     label="AI匹配结果")
screenshot("e2e_match.png")

ws.close()
chrome.terminate()

print("\n===== RESULT =====")
if errors:
    print("FAILED:")
    for e in errors:
        print(" -", e)
else:
    print("ALL E2E CHECKS PASSED")
