# -*- coding: utf-8 -*-
# 打开"选择录入方式"弹框，输出每一项的图标数量与结构
import json, time, subprocess, websocket, urllib.request, os, base64

CHROME = r"C:/Program Files/Google/Chrome/Application/chrome.exe"
PORT = 9272
BASE = "https://91fbcd73077147039da3de0cbcf2cc12.app.workbuddy.link/"
OUT = r"C:/Users/madta/WorkBuddy/2026-08-19-12-24-26/loan-assistant/scripts/e2e_shots/cust_arch"
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
msg_id = [0]


def send(method, params=None):
    msg_id[0] += 1
    ws.send(json.dumps({"id": msg_id[0], "method": method, "params": params or {}}))
    while True:
        d = json.loads(ws.recv())
        if d.get("id") == msg_id[0]:
            return d


def eval_js(expr):
    return send("Runtime.evaluate", {"expression": expr, "returnByValue": True}).get("result", {}).get("result", {}).get("value")


def shot(name):
    res = send("Page.captureScreenshot", {"format": "png"})
    with open(os.path.join(OUT, name), "wb") as f:
        f.write(base64.b64decode(res["result"]["data"]))
    print("saved:", name)


send("Page.enable")
send("Page.navigate", {"url": BASE})
time.sleep(2)
eval_js(f"localStorage.setItem('token', {json.dumps(TOKEN)}); localStorage.setItem('userInfo', {json.dumps(USER)});")
send("Page.navigate", {"url": BASE + "#/home"})
time.sleep(4)

clicked = eval_js("""
(() => {
  const nodes = [...document.querySelectorAll('*')].filter(e =>
    e.children.length === 0 && (e.innerText || '').trim() === '新建日程');
  if (nodes.length) { nodes[0].click(); return 'clicked:' + nodes.length; }
  const alt = [...document.querySelectorAll('*')].filter(e => /新建日程/.test(e.innerText||''));
  if (alt.length) { alt[alt.length-1].click(); return 'alt-clicked'; }
  return 'not-found';
})()
""")
print("home click:", clicked)
time.sleep(2)
shot("method_sheet_home.png")

print(eval_js("""
(() => {
  const items = [...document.querySelectorAll('.van-action-sheet__item')];
  return JSON.stringify(items.map(it => ({
    text: (it.innerText||'').replace(/\\n/g,' | '),
    svg: it.querySelectorAll('svg').length,
    vanIcon: it.querySelectorAll('.van-icon, i[class*=van-icon]').length,
    firstSvg: (it.querySelector('svg')||{}).outerHTML ? it.querySelector('svg').outerHTML.slice(0,120) : null
  })), null, 1);
})()
"""))

ws.close()
chrome.terminate()
