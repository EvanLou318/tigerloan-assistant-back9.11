# -*- coding: utf-8 -*-
# 截图：产品编辑页卡片布局 + 语音录入底弹框
import json, time, subprocess, websocket, urllib.request, os, base64

CHROME = r"C:/Program Files/Google/Chrome/Application/chrome.exe"
PORT = 9288
BASE = "http://127.0.0.1:3007/"
OUT = r"C:/Users/madta/WorkBuddy/2026-08-19-12-24-26/loan-assistant/scripts/e2e_shots/layout_check"
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
send("Page.navigate", {"url": BASE + "#/products/create?edit=p005"})
time.sleep(5)

print("URL:", ev("location.hash"))

# 整页截图
send("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": True})
res = send("Page.captureScreenshot", {"format": "png"})
with open(os.path.join(OUT, "01_edit_full.png"), "wb") as f:
    f.write(base64.b64decode(res["result"]["data"]))

# 测量编辑页各元素
m = ev("""
(() => {
  const out = [];
  const g = document.querySelector('.van-cell-group');
  if (g) { const r = g.getBoundingClientRect(); out.push('cell-group w=' + Math.round(r.width) + ' left=' + Math.round(r.left)); }
  const fields = [...document.querySelectorAll('.van-field')];
  out.push('field count=' + fields.length);
  fields.forEach(f => {
    const lab = (f.querySelector('.van-field__label')||{}).innerText || '(no label)';
    const r = f.getBoundingClientRect();
    out.push('  ' + lab.replace(/\\n/g,'') + ' w=' + Math.round(r.width) + ' h=' + Math.round(r.height));
  });
  const rr = document.querySelector('.range-row');
  if (rr) { const r = rr.getBoundingClientRect(); out.push('range-row w=' + Math.round(r.width) + ' h=' + Math.round(r.height));
    [...rr.querySelectorAll('.range-field')].forEach(e => { const b = e.getBoundingClientRect(); out.push('  range-field w=' + Math.round(b.width) + ' left=' + Math.round(b.left)); });
  }
  const cl = document.querySelector('.conditions-label');
  if (cl) { const r = cl.getBoundingClientRect(); out.push('conditions-label left=' + Math.round(r.left) + ' w=' + Math.round(r.width)); }
  return out.join('\\n');
})()
""")
print("=== 编辑页测量 ===")
print(m)

# 打开语音录入
ev("""
(() => {
  const btn = document.querySelector('.voice-mic-btn');
  if (btn) btn.click();
})()
""")
time.sleep(1.5)
shot("02_voice_sheet.png")

m2 = ev("""
(() => {
  const out = [];
  const t = document.querySelector('.vs-title');
  if (t) { const r = t.getBoundingClientRect(); out.push('vs-title w=' + Math.round(r.width) + ' h=' + Math.round(r.height) + ' lines~' + Math.round(r.height/24)); }
  const s = document.querySelector('.vs-sub');
  if (s) { const r = s.getBoundingClientRect(); out.push('vs-sub w=' + Math.round(r.width) + ' h=' + Math.round(r.height) + ' text=' + s.innerText); }
  const h = document.querySelector('.vs-header');
  if (h) { const r = h.getBoundingClientRect(); out.push('vs-header w=' + Math.round(r.width) + ' h=' + Math.round(r.height)); }
  const sh = document.querySelector('.voice-sheet');
  if (sh) { const r = sh.getBoundingClientRect(); out.push('voice-sheet w=' + Math.round(r.width) + ' h=' + Math.round(r.height)); }
  const tag = document.querySelector('.vs-field-tag');
  if (tag) { const r = tag.getBoundingClientRect(); out.push('field-tag top=' + Math.round(r.top) + ' left=' + Math.round(r.left) + ' text=' + tag.innerText); }
  return out.join('\\n');
})()
""")
print("=== 语音弹框测量 ===")
print(m2)

ws.close()
chrome.terminate()
