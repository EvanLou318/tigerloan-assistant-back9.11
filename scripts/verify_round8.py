# -*- coding: utf-8 -*-
# 第八轮校验：日程卡片"逾期"移到时间列、标题行只留优先级
import json, time, subprocess, websocket, urllib.request, os, base64

CHROME = r"C:/Program Files/Google/Chrome/Application/chrome.exe"
PORT = 9292
BASE = "http://127.0.0.1:3007/"
OUT = r"C:/Users/madta/WorkBuddy/2026-08-19-12-24-26/loan-assistant/scripts/e2e_shots/round8"
os.makedirs(OUT, exist_ok=True)

raw = subprocess.run([
    "curl", "-s", "--noproxy", "*", "-m", "25", "-X", "POST", BASE + "api/auth/login",
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

send("Page.navigate", {"url": BASE + "#/schedules"})
time.sleep(4)
ev("""
(() => {
  const t = [...document.querySelectorAll('.tab-item')].find(e => e.innerText.includes('全部'));
  if (t) t.click();
})()
""")
time.sleep(1.5)

print("=== 卡片状态位分布 ===")
print(ev("""
(() => {
  const cards = [...document.querySelectorAll('.schedule-card')];
  const hs = cards.map(c => Math.round(c.getBoundingClientRect().height));
  const tcw = cards[0] ? Math.round(cards[0].querySelector('.time-col').getBoundingClientRect().width) : null;
  return JSON.stringify({
    count: cards.length,
    heights: hs,
    uniform: new Set(hs).size <= 2,
    timeColWidth: tcw,
    timeColOverflow: cards.some(c => {
      const el = c.querySelector('.time-col');
      return el.scrollWidth > el.clientWidth + 1;
    }),
    rows: cards.map(c => ({
      titleRow: [...c.querySelectorAll('.title > span')].map(e => e.innerText.trim()).filter(Boolean),
      overdueInTimeCol: !!c.querySelector('.t-overdue'),
      overdueInTitle: !!c.querySelector('.title .overdue-tag'),
    })),
  }, null, 1);
})()
"""))
shot("01_schedule_all.png")

# 已完成 tab 也应正常
ev("""
(() => {
  const t = [...document.querySelectorAll('.tab-item')].find(e => e.innerText.includes('已完成'));
  if (t) t.click();
})()
""")
time.sleep(1.2)
shot("02_schedule_done.png")
chrome.terminate()
print("DONE")
