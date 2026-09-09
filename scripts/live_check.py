# -*- coding: utf-8 -*-
# 线上发布地址真实渲染验证：登录页 + 登录后首页/产品列表截图
import json, time, subprocess, websocket, urllib.request, os, base64

CHROME = r"C:/Program Files/Google/Chrome/Application/chrome.exe"
PORT = 9241
BASE = "https://3000-91fbcd73077147039da3de0cbcf2cc12.e2b.sh7.sandbox.cloudstudio.club/"
OUT_DIR = r"C:/Users/madta/WorkBuddy/2026-08-19-12-24-26/loan-assistant/scripts/e2e_shots/live_check"
os.makedirs(OUT_DIR, exist_ok=True)

req = urllib.request.Request(
    BASE + "api/auth/login",
    data=json.dumps({"phone": "13800138000", "password": "abc123"}).encode(),
    headers={"Content-Type": "application/json"},
)
login = json.loads(urllib.request.urlopen(req, timeout=20).read())
TOKEN = login["data"]["token"]
USER = json.dumps(login["data"]["user"], ensure_ascii=False)
print("online login ok")

chrome = subprocess.Popen([
    CHROME, "--headless=new", f"--remote-debugging-port={PORT}",
    "--remote-allow-origins=*", "--disable-gpu", "--no-first-run",
    "--window-size=390,844", "about:blank",
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2.5)

tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json").read())
page = next(t for t in tabs if t["type"] == "page")
ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=40)
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
    with open(os.path.join(OUT_DIR, name), "wb") as f:
        f.write(base64.b64decode(res["result"]["data"]))
    print("saved:", name)

send("Page.enable")
send("Runtime.enable")
send("Emulation.setDeviceMetricsOverride", {"width": 390, "height": 844, "deviceScaleFactor": 2, "mobile": True})
send("Emulation.setTouchEmulationEnabled", {"enabled": True})

# 登录页
eval_js("localStorage.clear()")
send("Page.navigate", {"url": BASE + "#/login"})
time.sleep(4)
screenshot("01_login_live.png")

# 登录态首页
eval_js(f"localStorage.setItem('token', {json.dumps(TOKEN)}); localStorage.setItem('userInfo', {json.dumps(USER)});")
send("Page.navigate", {"url": BASE + "#/home"})
time.sleep(4)
screenshot("02_home_live.png")

# 产品列表（验证 API 数据拉取）
send("Page.navigate", {"url": BASE + "#/products"})
time.sleep(4)
screenshot("03_products_live.png")

# 拿页面实际文本验证渲染非空
body_text = eval_js("document.body.innerText.slice(0, 300)")
print("--- body text (home) ---")
print((body_text or "").replace("\n", " | ")[:300])

print("DONE ->", OUT_DIR)
chrome.terminate()
