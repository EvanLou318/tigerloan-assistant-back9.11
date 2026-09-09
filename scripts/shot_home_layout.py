# -*- coding: utf-8 -*-
# 首页布局检查截图（本地 dev 5173）
import json, time, subprocess, websocket, urllib.request, os, base64

CHROME = r"C:/Program Files/Google/Chrome/Application/chrome.exe"
PORT = 9259
BASE = "http://localhost:5173/"
OUT_DIR = r"C:/Users/madta/WorkBuddy/2026-08-19-12-24-26/loan-assistant/scripts/e2e_shots/home_layout"
os.makedirs(OUT_DIR, exist_ok=True)

req = urllib.request.Request("http://localhost:3001/api/auth/login",
    data=json.dumps({"phone": "13800138000", "password": "abc123"}).encode(),
    headers={"Content-Type": "application/json"})
login = json.loads(urllib.request.urlopen(req).read())
TOKEN = login["data"]["token"]; USER = json.dumps(login["data"]["user"], ensure_ascii=False)

chrome = subprocess.Popen([CHROME, "--headless=new", f"--remote-debugging-port={PORT}",
    "--remote-allow-origins=*", "--disable-gpu", "--no-first-run", "--window-size=390,844", "about:blank"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2.5)
tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json").read())
page = next(t for t in tabs if t["type"] == "page")
ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=30); mid = 0

def send(m, p=None):
    global mid; mid += 1; ws.send(json.dumps({"id": mid, "method": m, "params": p or {}}))
    while True:
        d = json.loads(ws.recv())
        if d.get("id") == mid: return d

def ev(e):
    r = send("Runtime.evaluate", {"expression": e, "returnByValue": True})
    res = r.get("result", {})
    if res.get("subtype") == "error": return "EVAL-ERR: " + str(res.get("description"))[:300]
    return res.get("result", {}).get("value")

def shot(name):
    res = send("Page.captureScreenshot", {"format": "png"})
    with open(os.path.join(OUT_DIR, name), "wb") as f:
        f.write(base64.b64decode(res["result"]["data"]))
    print("shot:", name)

send("Page.enable"); send("Runtime.enable")
send("Emulation.setDeviceMetricsOverride", {"width": 390, "height": 844, "deviceScaleFactor": 2, "mobile": True})
send("Page.navigate", {"url": BASE + "#/login"}); time.sleep(3.5)
ev(f"localStorage.setItem('token',{json.dumps(TOKEN)}); localStorage.setItem('userInfo',{json.dumps(USER)})")
ev("location.hash='#/'"); time.sleep(3)

# 量化间距：stats-card 底边 与 今日日程 section-header 顶边
gap = ev("""(() => {
  const card = document.querySelector('.stats-card');
  const header = document.querySelector('.section-header');
  if (!card || !header) return 'missing';
  const a = card.getBoundingClientRect(), b = header.getBoundingClientRect();
  return JSON.stringify({cardBottom: a.bottom, headerTop: b.top, gap: b.top - a.bottom});
})()""")
print("gap card->header:", gap)
# hero 底边 与 卡片视觉底边
hero = ev("""(() => {
  const h = document.querySelector('.hero'), c = document.querySelector('.stats-card');
  if (!h || !c) return 'missing';
  const a = h.getBoundingClientRect(), b = c.getBoundingClientRect();
  return JSON.stringify({heroBottom: a.bottom, cardBottom: b.bottom, overflow: b.bottom - a.bottom});
})()""")
print("hero/card:", hero)
shot("home_before.png")
print("DONE")
chrome.terminate()
