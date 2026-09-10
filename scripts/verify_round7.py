# -*- coding: utf-8 -*-
# 第七轮校验：日程创建页卡片边距 + 日程卡片统一版式
import json, time, subprocess, websocket, urllib.request, os, base64

CHROME = r"C:/Program Files/Google/Chrome/Application/chrome.exe"
PORT = 9292
BASE = "https://91fbcd73077147039da3de0cbcf2cc12.app.workbuddy.link/"
OUT = r"C:/Users/madta/WorkBuddy/2026-08-19-12-24-26/loan-assistant/scripts/e2e_shots/round7"
os.makedirs(OUT, exist_ok=True)

raw = subprocess.run([
    "curl", "-s", "-m", "25", "-X", "POST", BASE + "api/auth/login",
    "-H", "Content-Type: application/json",
    "-d", json.dumps({"phone": "13800138000", "password": "abc123"}),
], capture_output=True, text=True).stdout
login = json.loads(raw)
TOKEN, USER = login["data"]["token"], json.dumps(login["data"]["user"], ensure_ascii=False)

chrome = subprocess.Popen([
    CHROME, "--headless=new", f"--remote-debugging-port={PORT}",
    "--remote-allow-origins=*", "--disable-gpu", "--no-first-run",
    "--window-size=390,844", "about:blank",
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2.5)
tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json").read())
page = next(t for t in tabs if t["type"] == "page")
ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=40)
mid = [0]

def send(method, params=None):
    mid[0] += 1
    ws.send(json.dumps({"id": mid[0], "method": method, "params": params or {}}))
    while True:
        d = json.loads(ws.recv())
        if d.get("id") == mid[0]:
            return d

def ev(expr):
    return send("Runtime.evaluate", {"expression": expr, "returnByValue": True}).get("result", {}).get("result", {}).get("value")

def shot(name):
    res = send("Page.captureScreenshot", {"format": "png"})
    with open(os.path.join(OUT, name), "wb") as f:
        f.write(base64.b64decode(res["result"]["data"]))
    print("saved:", name)

send("Page.enable")
send("Emulation.setDeviceMetricsOverride", {"width": 390, "height": 844, "deviceScaleFactor": 2, "mobile": True})
send("Page.navigate", {"url": BASE})
time.sleep(2)
ev(f"localStorage.setItem('token', {json.dumps(TOKEN)}); localStorage.setItem('userInfo', {json.dumps(USER)});")

# 1) 日程创建页（文本直达表单）：cell-group 左右边距
send("Page.navigate", {"url": BASE + "#/schedules/create"})
time.sleep(4)
print("=== 创建页卡片边距 ===")
print(ev("""
(() => {
  const g = document.querySelector('.form-step .van-cell-group--inset');
  if (!g) return 'no group';
  const r = g.getBoundingClientRect();
  const cs = getComputedStyle(g);
  return JSON.stringify({ left: Math.round(r.left), width: Math.round(r.width), ml: cs.marginLeft, mr: cs.marginRight });
})()
"""))
shot("01_create_form.png")

# 2) 日程列表：卡片版式一致性（全部 tab）
send("Page.navigate", {"url": BASE + "#/schedules"})
time.sleep(4)
ev("""
(() => {
  const t = [...document.querySelectorAll('.tab-item')].find(e => e.innerText.includes('全部'));
  if (t) t.click();
})()
""")
time.sleep(1.5)
print("=== 日程卡片结构 ===")
print(ev("""
(() => {
  const cards = [...document.querySelectorAll('.schedule-card')];
  const hs = cards.map(c => Math.round(c.getBoundingClientRect().height));
  const detail = cards.slice(0, 5).map(c => {
    const date = c.querySelector('.t-date');
    const meta = c.querySelector('.meta-text');
    const od = c.querySelector('.overdue-tag');
    return {
      date: date ? date.innerText.trim() : null,
      meta: meta ? meta.innerText.slice(0, 30) : null,
      overdue: !!od,
      metaSingleLine: meta ? getComputedStyle(meta).whiteSpace === 'nowrap' : false,
    };
  });
  return JSON.stringify({ count: cards.length, heights: hs, uniform: new Set(hs).size <= 2, detail }, null, 1);
})()
"""))
shot("02_schedule_all.png")
chrome.terminate()
print("DONE")
