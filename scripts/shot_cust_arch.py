# -*- coding: utf-8 -*-
# 查看客户档案页现状 + 录入方式弹框（定位"文本录入多一个图标"）
import json, time, subprocess, websocket, urllib.request, os, base64

CHROME = r"C:/Program Files/Google/Chrome/Application/chrome.exe"
PORT = 9271
BASE = "https://91fbcd73077147039da3de0cbcf2cc12.app.workbuddy.link/"
OUT = r"C:/Users/madta/WorkBuddy/2026-08-19-12-24-26/loan-assistant/scripts/e2e_shots/cust_arch"
os.makedirs(OUT, exist_ok=True)

raw = subprocess.run([
    "curl", "-s", "-m", "25", "-X", "POST", BASE + "api/auth/login",
    "-H", "Content-Type: application/json",
    "-d", json.dumps({"phone": "13800138000", "password": "abc123"}),
], capture_output=True, text=True).stdout
login = json.loads(raw)
TOKEN = login["data"]["token"]
USER = json.dumps(login["data"]["user"], ensure_ascii=False)

chrome = subprocess.Popen([
    CHROME, "--headless=new", f"--remote-debugging-port={PORT}",
    "--remote-allow-origins=*", "--disable-gpu", "--no-first-run",
    "--window-size=390,1600", "about:blank",
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2.5)

tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json").read())
page = next(t for t in tabs if t["type"] == "page")
ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=40)
msg_id = [0]


def send(method, params=None):
    msg_id[0] += 1
    ws.send(json.dumps({"id": msg_id[0], "method": method, "params": params or {}}))
    while True:
        data = json.loads(ws.recv())
        if data.get("id") == msg_id[0]:
            return data


def eval_js(expr):
    res = send("Runtime.evaluate", {"expression": expr, "returnByValue": True})
    return res.get("result", {}).get("result", {}).get("value")


def shot(name):
    res = send("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": True})
    with open(os.path.join(OUT, name), "wb") as f:
        f.write(base64.b64decode(res["result"]["data"]))
    print("saved:", name)


send("Page.enable")
send("Page.navigate", {"url": BASE})
time.sleep(2)
eval_js(f"localStorage.setItem('token', {json.dumps(TOKEN)}); localStorage.setItem('userInfo', {json.dumps(USER)});")

# 拿第一个客户 id
lst = subprocess.run([
    "curl", "-s", "-m", "20", BASE + "api/customers", "-H", f"X-Auth-Token: {TOKEN}",
], capture_output=True, text=True).stdout
cid = json.loads(lst)["data"][0]["id"]
print("customer id:", cid)

send("Page.navigate", {"url": BASE + f"#/customers/{cid}"})
time.sleep(4)
shot("01_archive_full.png")

# 打开录入方式弹框（点"新建日程"）
clicked = eval_js("""
(() => {
  const el = [...document.querySelectorAll('span,button,div')].find(e =>
    /新建日程|为 TA 安排日程/.test(e.innerText || '') && e.children.length === 0);
  if (el) { el.click(); return el.innerText; }
  return null;
})()
""")
print("clicked:", clicked)
time.sleep(1.5)
shot("02_method_sheet.png")

# 输出弹框每项的 DOM 结构
dom = eval_js("""
(() => {
  const items = [...document.querySelectorAll('.van-action-sheet__item')];
  return JSON.stringify(items.map(it => ({
    text: it.innerText.replace(/\\n/g, ' | '),
    svgCount: it.querySelectorAll('svg').length,
    iconCount: it.querySelectorAll('.van-icon').length,
    html: it.innerHTML.slice(0, 240)
  })), null, 1);
})()
""")
print("sheet items:", dom)

ws.close()
chrome.terminate()
