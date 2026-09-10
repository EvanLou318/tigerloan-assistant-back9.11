# -*- coding: utf-8 -*-
# 第六轮校验：产品卡片时间内联 / 日程详情标记完成 / 个人中心精简+头像 / 推演自动下滑
import json, time, subprocess, websocket, urllib.request, os, base64

CHROME = r"C:/Program Files/Google/Chrome/Application/chrome.exe"
PORT = 9292
BASE = "https://91fbcd73077147039da3de0cbcf2cc12.app.workbuddy.link/"
OUT = r"C:/Users/madta/WorkBuddy/2026-08-19-12-24-26/loan-assistant/scripts/e2e_shots/round6"
os.makedirs(OUT, exist_ok=True)

def curl_login():
    raw = subprocess.run([
        "curl", "-s", "-m", "25", "-X", "POST", BASE + "api/auth/login",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({"phone": "13800138000", "password": "abc123"}),
    ], capture_output=True, text=True).stdout
    return json.loads(raw)

login = curl_login()
TOKEN, USER = login["data"]["token"], json.dumps(login["data"]["user"], ensure_ascii=False)

# 取一个客户 id（用于进入推演页）
cust = subprocess.run([
    "curl", "-s", "-m", "25", BASE + "api/customers",
    "-H", f"X-Auth-Token: {TOKEN}",
], capture_output=True, text=True).stdout
cust_data = json.loads(cust)
cid = cust_data["data"][0]["id"]
print("customer id:", cid)

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
    r = send("Runtime.evaluate", {"expression": expr, "returnByValue": True})
    return r.get("result", {}).get("result", {}).get("value")

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

# 1) 产品列表：时间是否内联到额度行（不再有独立 footer）
send("Page.navigate", {"url": BASE + "#/products"})
time.sleep(3.5)
print("=== 产品卡片 ===")
print(ev("""
(() => {
  const card = document.querySelector('.product-card');
  if (!card) return 'no card';
  const footer = card.querySelector('.card-footer');
  const time = card.querySelector('.card-time');
  const row = time ? time.closest('.info-row') : null;
  return JSON.stringify({
    hasFooter: !!footer,
    timeText: time ? time.innerText : null,
    timeInInfoRow: !!row,
    rowText: row ? row.innerText : null,
  });
})()
"""))
shot("01_products.png")

# 2) 日程详情弹框：标记完成按钮
send("Page.navigate", {"url": BASE + "#/schedules"})
time.sleep(3.5)
ev("""
(() => {
  const t = [...document.querySelectorAll('.tab-item')].find(e => e.innerText.includes('全部'));
  if (t) t.click();
})()
""")
time.sleep(1.2)
ev("""
(() => {
  const card = document.querySelector('.schedule-card');
  if (card) card.click();
})()
""")
time.sleep(1.2)
print("=== 日程详情弹框 ===")
print(ev("""
(() => {
  const btns = [...document.querySelectorAll('.detail-popup .van-button')].map(b => b.innerText.trim());
  return JSON.stringify({ btns, hasMarkDone: btns.some(t => t.includes('标记完成') || t.includes('恢复未完成')) });
})()
"""))
shot("02_schedule_detail.png")
ev("document.querySelector('.dp-close')?.click()")

# 3) 个人中心：意见反馈/关于已删，头像编辑入口存在
send("Page.navigate", {"url": BASE + "#/profile"})
time.sleep(3)
print("=== 个人中心 ===")
print(ev("""
(() => {
  const txt = document.body.innerText;
  const liTexts = [...document.querySelectorAll('.list-item .li-text')].map(e => e.innerText);
  return JSON.stringify({
    hasFeedback: txt.includes('意见反馈'),
    hasAbout: txt.includes('关于智贷助手'),
    listItems: liTexts,
    avatarEdit: !!document.querySelector('.avatar-edit'),
    avatarImg: !!document.querySelector('.avatar-img'),
  });
})()
"""))
shot("03_profile.png")

# 4) 推演自动下滑：进入推演页 -> 点重新匹配 -> 观察 scrollY
send("Page.navigate", {"url": BASE + f"#/customers/{cid}/simulation"})
time.sleep(4)
y0 = ev("window.scrollY")
print("初始 scrollY:", y0)
ev("""
(() => {
  const b = [...document.querySelectorAll('.action-bar .van-button')].find(e => e.innerText.includes('重新匹配'));
  if (b) b.click();
})()
""")
time.sleep(7)
y1 = ev("window.scrollY")
print("匹配后 scrollY:", y1)
print("=== 滚动位置 ===")
print(ev("(() => JSON.stringify({ sy: window.scrollY, dTop: document.documentElement.scrollTop, bTop: document.body.scrollTop }))()"))
print(ev("(() => JSON.stringify({ scrollHeight: document.documentElement.scrollHeight, bodyHeight: document.body.scrollHeight, vh: window.innerHeight }))()"))
print("=== 推演滚动 ===")
print(ev("""
(() => {
  const sec = document.querySelector('.result-section');
  const r = sec ? sec.getBoundingClientRect() : null;
  return JSON.stringify({ scrolled: window.scrollY > 0, resultTop: r ? Math.round(r.top) : null });
})()
"""))
shot("04_simulation.png")

chrome.terminate()
print("DONE")
