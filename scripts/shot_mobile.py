# -*- coding: utf-8 -*-
# 手机端全页面截图：390x844 移动视口，输出到 scripts/e2e_shots/mobile_<suffix>/
import json, time, subprocess, websocket, urllib.request, os, base64, sys

CHROME = r"C:/Program Files/Google/Chrome/Application/chrome.exe"
PORT = 9240
BASE = "http://localhost:5173/"
SUFFIX = sys.argv[1] if len(sys.argv) > 1 else "base"
OUT_DIR = rf"C:/Users/madta/WorkBuddy/2026-08-19-12-24-26/loan-assistant/scripts/e2e_shots/mobile_{SUFFIX}"
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
    CHROME, "--headless=new", f"--remote-debugging-port={PORT}",
    "--remote-allow-origins=*", "--disable-gpu", "--no-first-run",
    "--window-size=390,844", "about:blank",
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
    with open(os.path.join(OUT_DIR, name), "wb") as f:
        f.write(base64.b64decode(res["result"]["data"]))
    print("saved:", name)

def goto(path, name, wait=2.8, auth=True):
    if auth:
        eval_js(f"localStorage.setItem('token', {json.dumps(TOKEN)}); localStorage.setItem('userInfo', {json.dumps(USER)});")
    send("Page.navigate", {"url": BASE + "#" + path})
    time.sleep(wait)
    screenshot(name)

send("Page.enable")
send("Runtime.enable")
send("Emulation.setDeviceMetricsOverride", {"width": 390, "height": 844, "deviceScaleFactor": 2, "mobile": True})
send("Emulation.setTouchEmulationEnabled", {"enabled": True})

# 登录页（未登录态）
eval_js("localStorage.clear()")
send("Page.navigate", {"url": BASE + "#/login"})
time.sleep(2.5)
screenshot("01_login.png")

# 找到一位客户 id 用于详情/匹配页
customers = json.loads(urllib.request.urlopen(urllib.request.Request(
    "http://localhost:3001/api/customers", headers={"Authorization": f"Bearer {TOKEN}"})).read())
cid = customers["data"][0]["id"] if customers["data"] else None
products = json.loads(urllib.request.urlopen(urllib.request.Request(
    "http://localhost:3001/api/products", headers={"Authorization": f"Bearer {TOKEN}"})).read())
pid = products["data"][0]["id"] if products["data"] else None

goto("/home", "02_home.png")
goto("/products", "03_products.png")
if pid:
    goto(f"/products/{pid}", "04_product_detail.png")
goto("/products/create", "05_product_create.png")
goto("/customers", "06_customers.png")
goto("/customers/create", "07_customer_create.png")
if cid:
    goto(f"/customers/{cid}", "08_customer_detail.png")
    goto(f"/customers/{cid}/match", "09_match.png")
    goto(f"/customers/{cid}/simulation", "10_simulation.png")
goto("/schedules", "11_schedules.png")
goto("/schedules/create", "12_schedule_create.png")
goto("/assistant", "13_assistant.png")
goto("/profile", "14_profile.png")
goto("/change-password", "15_change_password.png")

print("DONE ->", OUT_DIR)
chrome.terminate()
