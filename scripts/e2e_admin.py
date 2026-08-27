# -*- coding: utf-8 -*-
# 管理后台端到端验证：真实 JWT -> 逐页检查渲染并截图（桌面视口）
import json
import time
import subprocess
import websocket
import urllib.request
import os
import base64

CHROME = r"C:/Program Files/Google/Chrome/Application/chrome.exe"
PORT = 9230
BASE = "http://localhost:5173/"
OUT_DIR = r"C:/Users/madta/WorkBuddy/2026-08-19-12-24-26/loan-assistant/scripts/e2e_shots"
os.makedirs(OUT_DIR, exist_ok=True)

req = urllib.request.Request(
    "http://localhost:3001/api/auth/login",
    data=json.dumps({"phone": "13800138000", "password": "abc123"}).encode(),
    headers={"Content-Type": "application/json"},
)
login = json.loads(urllib.request.urlopen(req).read())
TOKEN = login["data"]["token"]
USER = json.dumps(login["data"]["user"], ensure_ascii=False)
print("login ok")

chrome = subprocess.Popen([
    CHROME,
    "--headless=new",
    f"--remote-debugging-port={PORT}",
    "--remote-allow-origins=*",
    "--disable-gpu",
    "--no-first-run",
    "--window-size=1440,900",
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
    eval_js(f"localStorage.setItem('token', {json.dumps(TOKEN)}); localStorage.setItem('userInfo', {json.dumps(USER)});")
    send("Page.navigate", {"url": BASE + "#" + path})
    time.sleep(wait)
    if check:
        val = eval_js(check)
        ok = val and not str(val).startswith('FAIL')
        print(f"  [{'OK' if ok else 'FAIL'}] {label or path} => {val}")
        if not ok:
            errors.append(f"{path}: {label} => {val}")

send("Page.enable")
send("Runtime.enable")
send("Emulation.setDeviceMetricsOverride", {"width": 1440, "height": 900, "deviceScaleFactor": 1, "mobile": False})
send("Page.navigate", {"url": BASE + "#/login"})
time.sleep(2)
eval_js(f"localStorage.setItem('token', {json.dumps(TOKEN)}); localStorage.setItem('userInfo', {json.dumps(USER)});")

goto("/admin/dashboard", wait=3,
     check="""(() => { const t = document.body.innerText;
        return (t.includes('数据看板') && t.includes('客户总数') && document.querySelectorAll('.stat-card').length >= 5)
          ? 'dashboard ok' : 'FAIL cards=' + document.querySelectorAll('.stat-card').length; })()""",
     label="数据看板")
screenshot("admin_dashboard.png")

goto("/admin/customers", wait=3,
     check="""(() => { const t = document.body.innerText;
        return t.includes('张明') ? 'customers ok' : 'FAIL no seed customer'; })()""",
     label="客户管理")
screenshot("admin_customers.png")

goto("/admin/products", wait=3,
     check="""(() => { const t = document.body.innerText;
        return (t.includes('产品名称') && document.querySelectorAll('tbody tr').length > 0) ? 'products ok' : 'FAIL'; })()""",
     label="产品管理")
screenshot("admin_products.png")

goto("/admin/schedules", wait=3,
     check="""(() => { return document.querySelectorAll('tbody tr').length > 0 ? 'schedules ok' : 'FAIL'; })()""",
     label="日程管理")
screenshot("admin_schedules.png")

goto("/admin/users", wait=3,
     check="""(() => { const t = document.body.innerText;
        return t.includes('李经理') ? 'users ok' : 'FAIL'; })()""",
     label="用户管理")
screenshot("admin_users.png")

ws.close()
chrome.terminate()

print("\n===== RESULT =====")
if errors:
    print("FAILED:")
    for e in errors:
        print(" -", e)
else:
    print("ALL ADMIN E2E CHECKS PASSED")
