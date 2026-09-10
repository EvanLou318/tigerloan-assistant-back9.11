# -*- coding: utf-8 -*-
# 校验：日程卡片布局 / 无标记完成 / 详情弹框底部留白 / 产品列表无录入方式 / 利率类型
import json, time, subprocess, websocket, urllib.request, os, base64

CHROME = r"C:/Program Files/Google/Chrome/Application/chrome.exe"
PORT = 9291
BASE = "http://127.0.0.1:3007/"
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

# ---------- 1. 日程页 ----------
send("Page.navigate", {"url": BASE + "#/schedules"})
time.sleep(4)
shot("01_schedule_list.png")
print("=== 日程卡片 ===")
print(ev("""
(() => {
  const c = document.querySelector('.schedule-card');
  if (!c) return 'no card';
  const col = c.querySelector('.time-col');
  const info = c.querySelector('.info');
  const start = c.querySelector('.t-start');
  const r = (e) => e ? Math.round(e.getBoundingClientRect().width) + 'x' + Math.round(e.getBoundingClientRect().height) : 'none';
  return JSON.stringify({
    card: r(c), timeCol: r(col), info: r(info), start: r(start),
    startTime: start && start.innerText,
    endTime: (c.querySelector('.t-end')||{}).innerText,
    date: (c.querySelector('.t-date')||{}).innerText || '(none)',
    prioChip: (c.querySelector('.prio-chip')||{}).innerText || '(none)',
    checkBox: document.querySelectorAll('.check-box').length,
    timeBlock: document.querySelectorAll('.time-block').length,
  }, null, 1);
})()
"""))

# 打开详情
ev("document.querySelector('.schedule-card').click()")
time.sleep(1.2)
shot("02_schedule_detail.png")
print("=== 详情弹框 ===")
print(ev("""
(() => {
  const p = document.querySelector('.detail-popup');
  const acts = document.querySelector('.dp-actions');
  const del = document.querySelector('.dp-delete');
  const btns = [...document.querySelectorAll('.dp-actions button')].map(b => b.innerText.trim());
  const cs = p ? getComputedStyle(p) : null;
  return JSON.stringify({
    buttons: btns,
    popupPaddingBottom: cs && cs.paddingBottom,
    gapToBottom: (del && p) ? Math.round(p.getBoundingClientRect().bottom - del.getBoundingClientRect().bottom) : null,
  }, null, 1);
})()
"""))

# ---------- 2. 新建日程方式弹框 ----------
ev("document.querySelector('.detail-popup .dp-close')?.click()")
time.sleep(0.8)
send("Page.navigate", {"url": BASE + "#/schedules"})
time.sleep(3)
ev("document.querySelector('.fab')?.click()")
time.sleep(1.2)
shot("03_schedule_method.png")
print("=== 新建日程方式 ===")
print(ev("""
JSON.stringify([...document.querySelectorAll('.van-action-sheet__name')].map(e => e.innerText.trim()))
"""))

# ---------- 3. 产品列表 ----------
send("Page.navigate", {"url": BASE + "#/products"})
time.sleep(4)
shot("04_product_list.png")
print("=== 产品列表 ===")
print(ev("""
(() => {
  const c = document.querySelector('.product-card');
  const rows = [...document.querySelectorAll('.product-card .info-row')].map(r => r.innerText.replace(/\\n/g, '='));
  return JSON.stringify({
    firstCardLabels: rows.slice(0, 3),
    sourceTagCount: document.querySelectorAll('.source-tag').length,
    footer: c ? c.querySelector('.card-footer').innerText.trim() : 'none',
  }, null, 1);
})()
"""))

# ---------- 4. 利率类型 ----------
send("Page.navigate", {"url": BASE + "#/products/create?edit=p005"})
time.sleep(4)
shot("05_product_edit.png")
print("=== 编辑产品：利率类型 ===")
print(ev("""
(() => {
  const cell = (t) => [...document.querySelectorAll('.van-cell')].find(c => (c.querySelector('.van-field__label')||{}).innerText?.includes(t));
  const rt = cell('利率类型');
  return JSON.stringify({
    rateTypeCell: rt ? rt.innerText.replace(/\\n/g, '=') : 'none',
    minRateLabel: (cell('最低')?.querySelector('.van-field__label')||{}).innerText || 'none',
    maxRateLabel: (cell('最高年')?.querySelector('.van-field__label')||{}).innerText
      || ((cell('最高')?.querySelector('.van-field__label')||{}).innerText) || 'none',
    labels: [...document.querySelectorAll('.van-field__label')].map(e => e.innerText.trim()),
  }, null, 1);
})()
"""))

# 切换为月利率
ev("""
(() => {
  const cell = [...document.querySelectorAll('.van-cell')].find(c => (c.querySelector('.van-field__label')||{}).innerText?.includes('利率类型'));
  if (cell) cell.click();
})()
""")
time.sleep(1)
shot("06_rate_type_sheet.png")
print("=== 利率类型弹层 ===")
print(ev("JSON.stringify([...document.querySelectorAll('.van-action-sheet__name')].map(e => e.innerText.trim()))"))
ev("""
(() => {
  const it = [...document.querySelectorAll('.van-action-sheet__item')].find(i => i.innerText.includes('月利率'));
  if (it) it.click();
})()
""")
time.sleep(1)
shot("07_monthly_selected.png")
print("=== 选月利率后 ===")
print(ev("""
(() => {
  const cell = (t) => [...document.querySelectorAll('.van-cell')].find(c => (c.querySelector('.van-field__label')||{}).innerText?.includes(t));
  return JSON.stringify({
    rateType: (cell('利率类型')||{}).innerText.replace(/\\n/g,'='),
    labels: [...document.querySelectorAll('.van-field__label')].map(e => e.innerText.trim()),
    hint: (document.querySelector('.rate-hint')||{}).innerText || '(no hint)',
    units: [...document.querySelectorAll('.term-inputs .unit, .van-field__button .unit, .van-button__text')].length,
  }, null, 1);
})()
"""))

ws.close()
chrome.terminate()
