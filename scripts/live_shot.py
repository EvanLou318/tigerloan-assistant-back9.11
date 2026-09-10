# -*- coding: utf-8 -*-
# 线上环境截图/校验：验证发布后的实际渲染效果
import json, time, subprocess, websocket, urllib.request, os, base64, sys

CHROME = r"C:/Program Files/Google/Chrome/Application/chrome.exe"
PORT = 9251
BASE = "https://91fbcd73077147039da3de0cbcf2cc12.app.workbuddy.link/"
OUT_DIR = r"C:/Users/madta/WorkBuddy/2026-08-19-12-24-26/loan-assistant/scripts/e2e_shots/live_published"
os.makedirs(OUT_DIR, exist_ok=True)

# 用 curl 登录：Python urllib 走代理时 POST 会返回 502
raw = subprocess.run([
    "curl", "-s", "-m", "25", "-X", "POST", BASE + "api/auth/login",
    "-H", "Content-Type: application/json",
    "-d", json.dumps({"phone": "13800138000", "password": "abc123"}),
], capture_output=True, text=True).stdout
login = json.loads(raw)
TOKEN = login["data"]["token"]
USER = json.dumps(login["data"]["user"], ensure_ascii=False)
print("live login ok")

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

def goto(path, name, wait=4.0, auth=True):
    if auth:
        eval_js(f"localStorage.setItem('token', {json.dumps(TOKEN)}); localStorage.setItem('userInfo', {json.dumps(USER)});")
    send("Page.navigate", {"url": BASE + "#" + path})
    time.sleep(wait)
    screenshot(name)

send("Page.enable")
send("Emulation.setDeviceMetricsOverride", {
    "width": 390, "height": 844, "deviceScaleFactor": 2, "mobile": True,
})

goto("/login", "01_login.png", auth=False)
goto("/home", "02_home.png")
goto("/products", "03_products.png")
goto("/customers", "04_customers.png")
goto("/schedules", "05_schedules.png")
goto("/profile", "06_profile.png")

# 特征校验：新图标系统 + 主色 + 无 emoji
checks = eval_js("""JSON.stringify({
  appIconCount: document.querySelectorAll('svg.app-icon').length,
  vanIconCount: document.querySelectorAll('.van-icon').length,
  bodyBg: getComputedStyle(document.body).backgroundColor,
  hasEmoji: /[\\u{1F300}-\\u{1FAFF}\\u{2600}-\\u{27BF}]/u.test(document.body.innerText || ''),
  html: document.title
})""")
print("CHECKS:", checks)

ws.close()
chrome.terminate()
print("DONE ->", OUT_DIR)
