# -*- coding: utf-8 -*-
# 端到端：切月利率 → 保存 → 校验 API rateType → 详情页展示 → 还原
import json, time, subprocess, websocket, urllib.request, os, base64

CHROME = r"C:/Program Files/Google/Chrome/Application/chrome.exe"
PORT = 9293
BASE = "http://127.0.0.1:3007/"
OUT = r"C:/Users/madta/WorkBuddy/2026-08-19-12-24-26/loan-assistant/scripts/e2e_shots/round5"
os.makedirs(OUT, exist_ok=True)

def api(method, path, body=None):
    cmd = ["curl", "-s", "--noproxy", "*", "-m", "15", "-X", method, BASE.rstrip("/") + path,
           "-H", "X-Auth-Token: " + TOKEN, "-H", "Content-Type: application/json"]
    if body is not None:
        cmd += ["-d", json.dumps(body)]
    return json.loads(subprocess.run(cmd, capture_output=True, text=True).stdout or "{}")

raw = subprocess.run([
    "curl", "-s", "--noproxy", "*", "-m", "25", "-X", "POST", BASE + "api/auth/login",
    "-H", "Content-Type: application/json",
    "-d", json.dumps({"phone": "13800138000", "password": "abc123"}),
], capture_output=True, text=True).stdout
login = json.loads(raw)
TOKEN, USER = login["data"]["token"], json.dumps(login["data"]["user"], ensure_ascii=False)
orig = api("GET", "/api/products/p005")["data"]
print("原产品:", orig["productName"], orig["minRate"], "-", orig["maxRate"], orig.get("rateType"))

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
send("Page.navigate", {"url": BASE + "#/products/create?edit=p005"})
time.sleep(4)

# 切月利率 + 改值
ev("""
(() => {
  const cell = (t) => [...document.querySelectorAll('.van-cell')].find(c => (c.querySelector('.van-field__label')||{}).innerText?.includes(t));
  const setVal = (t, v) => {
    const c = cell(t); const inp = c && c.querySelector('input');
    if (inp) { inp.value = v; inp.dispatchEvent(new Event('input', {bubbles:true})); }
  };
  cell('利率类型').click();
})()
""")
time.sleep(1)
ev("""
(() => {
  const it = [...document.querySelectorAll('.van-action-sheet__item')].find(i => i.innerText.includes('月利率'));
  if (it) it.click();
})()
""")
time.sleep(0.8)
ev("""
(() => {
  const cell = (t) => [...document.querySelectorAll('.van-cell')].find(c => (c.querySelector('.van-field__label')||{}).innerText?.includes(t));
  const setVal = (t, v) => {
    const c = cell(t); const inp = c && c.querySelector('input');
    if (inp) { inp.value = v; inp.dispatchEvent(new Event('input', {bubbles:true})); }
  };
  setVal('最低月', '0.29');
  setVal('最高月', '0.47');
})()
""")
time.sleep(0.5)
shot("10_monthly_filled.png")

# 保存
ev("""
(() => {
  const btn = [...document.querySelectorAll('button')].find(b => b.innerText.includes('确认保存'));
  if (btn) btn.click();
})()
""")
time.sleep(3)
after = api("GET", "/api/products/p005")["data"]
print("保存后:", after["minRate"], "-", after["maxRate"], "rateType =", after.get("rateType"))

# 详情页展示
send("Page.navigate", {"url": BASE + "#/products/p005"})
time.sleep(3)
shot("11_detail_monthly.png")
print("=== 详情页利率展示 ===")
print(ev("""
JSON.stringify({
  labels: [...document.querySelectorAll('.rate-label')].map(e => e.innerText.trim()),
  units: [...document.querySelectorAll('.rate-unit')].map(e => e.innerText.trim()),
})
"""))

# 还原为年利率
api("PUT", "/api/products/p005", {
    "productName": orig["productName"], "institution": orig["institution"],
    "minRate": orig["minRate"], "maxRate": orig["maxRate"], "rateType": "annual",
    "minAmount": orig["minAmount"], "maxAmount": orig["maxAmount"],
    "loanTerm": orig["loanTerm"], "repaymentMethod": orig["repaymentMethod"], "conditions": orig["conditions"],
})
restored = api("GET", "/api/products/p005")["data"]
print("还原后:", restored["minRate"], "-", restored["maxRate"], "rateType =", restored.get("rateType"))

ws.close()
chrome.terminate()
