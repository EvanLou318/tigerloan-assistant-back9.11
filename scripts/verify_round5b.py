# -*- coding: utf-8 -*-
# 补充校验：日程"全部"tab 卡片布局 + 详情弹框
import json, time, subprocess, websocket, urllib.request, os, base64

CHROME = r"C:/Program Files/Google/Chrome/Application/chrome.exe"
PORT = 9292
BASE = "https://91fbcd73077147039da3de0cbcf2cc12.app.workbuddy.link/"
OUT = r"C:/Users/madta/WorkBuddy/2026-08-19-12-24-26/loan-assistant/scripts/e2e_shots/round5"
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
msg_id = [0]


def send(method, params=None):
    msg_id[0] += 1
    ws.send(json.dumps({"id": msg_id[0], "method": method, "params": params or {}}))
    while True:
        d = json.loads(ws.recv())
        if d.get("id") == msg_id[0]:
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

# 切到"全部"
ev("""
(() => {
  const t = [...document.querySelectorAll('.tab-item')].find(e => e.innerText.includes('全部'));
  if (t) t.click();
})()
""")
time.sleep(1.5)
shot("08_schedule_all.png")
print("=== 日程卡片（全部） ===")
print(ev("""
(() => {
  const c = document.querySelector('.schedule-card');
  if (!c) return 'no card';
  const r = (e) => e ? Math.round(e.getBoundingClientRect().width) + 'x' + Math.round(e.getBoundingClientRect().height) : 'none';
  return JSON.stringify({
    card: r(c), timeCol: r(c.querySelector('.time-col')), info: r(c.querySelector('.info')),
    start: (c.querySelector('.t-start')||{}).innerText,
    end: (c.querySelector('.t-end')||{}).innerText,
    date: (c.querySelector('.t-date')||{}).innerText || '(none)',
    prioChip: (c.querySelector('.prio-chip')||{}).innerText || '(none)',
    title: (c.querySelector('.title-text')||{}).innerText,
    checkBox: document.querySelectorAll('.check-box').length,
    timeBlock: document.querySelectorAll('.time-block').length,
    meta: (c.querySelector('.meta')||{}).innerText.replace(/\\n/g, ' | '),
  }, null, 1);
})()
"""))

ev("document.querySelector('.schedule-card').click()")
time.sleep(1.2)
shot("09_schedule_detail.png")
print("=== 详情弹框 ===")
print(ev("""
(() => {
  const p = document.querySelector('.detail-popup');
  const del = document.querySelector('.dp-delete');
  const btns = [...document.querySelectorAll('.dp-actions .van-button')].map(b => b.innerText.trim());
  const cs = p ? getComputedStyle(p) : null;
  return JSON.stringify({
    popupOpen: !!p && p.getBoundingClientRect().height > 0,
    buttons: btns,
    markDoneBtns: btns.filter(t => t.includes('完成')).length,
    popupPaddingBottom: cs && cs.paddingBottom,
    gapDeleteToPopupBottom: (del && p) ? Math.round(p.getBoundingClientRect().bottom - del.getBoundingClientRect().bottom) : null,
  }, null, 1);
})()
"""))

ws.close()
chrome.terminate()
