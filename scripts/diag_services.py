# -*- coding: utf-8 -*-
# 三方服务页诊断：JWT 登录 -> 截图 + 控制台日志 + DOM 文本
import json
import time
import subprocess
import websocket
import urllib.request
import os
import base64

CHROME = r"C:/Program Files/Google/Chrome/Application/chrome.exe"
PORT = 9232
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
print("login ok, role =", login["data"]["user"]["role"])

chrome = subprocess.Popen([
    CHROME, "--headless=new", f"--remote-debugging-port={PORT}",
    "--remote-allow-origins=*", "--disable-gpu", "--no-first-run",
    "--window-size=1440,900", "about:blank",
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

send("Page.enable")
send("Runtime.enable")
send("Log.enable")
send("Emulation.setDeviceMetricsOverride", {"width": 1440, "height": 900, "deviceScaleFactor": 1, "mobile": False})

# 先访问登录页建立 origin，再写入 localStorage
send("Page.navigate", {"url": BASE + "#/login"})
time.sleep(2.5)
eval_js(f"localStorage.setItem('token', {json.dumps(TOKEN)}); localStorage.setItem('userInfo', {json.dumps(USER)});")

# 访问服务页
send("Page.navigate", {"url": BASE + "#/admin/services"})
time.sleep(3.5)

# 截图
res = send("Page.captureScreenshot", {"format": "png"})
with open(os.path.join(OUT_DIR, "diag_services.png"), "wb") as f:
    f.write(base64.b64decode(res["result"]["data"]))
print("saved diag_services.png")

# 检查关键 DOM
checks = {
    "cards_count": "document.querySelectorAll('.cat-card').length",
    "groups_length": "(() => { try { return JSON.parse(localStorage.getItem('vue_debug_groups') || '[]').length; } catch(e){ return 'err:'+e.message; } })()",
    "page_text": "document.body.innerText.slice(0, 500)",
    "route_path": "location.hash",
    "user_info": "localStorage.getItem('userInfo')",
    "errors": "(() => { const d=document.querySelector('.loading')||document.querySelector('.empty'); return d ? d.innerText : '无loading/empty'; })()",
}
for k, expr in checks.items():
    val = eval_js(expr)
    print(f"[{k}] => {val}")

# 尝试获取 Vue 组件内部 groups（通过暴露到 window）
eval_js("""(() => {
  const app = document.querySelector('#app')?.__vue_app__;
  if (!app) return;
  const router = app.config.globalProperties.$router;
  const route = app.config.globalProperties.$route;
  window.__diag_route = route ? route.path : 'no route';
  window.__diag_components = Array.from(app._context.components || []).map(c => c.name || c.__name);
})()""")
print("route:", eval_js("window.__diag_route || 'not set'"))

chrome.terminate()
