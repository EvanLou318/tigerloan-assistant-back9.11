# -*- coding: utf-8 -*-
# 端到端验证：线上真实登录流程，确认登录后不会自动登出
import json, time, subprocess, websocket, urllib.request, os, base64

CHROME = r"C:/Program Files/Google/Chrome/Application/chrome.exe"
PORT = 9263
BASE = "https://91fbcd73077147039da3de0cbcf2cc12.app.workbuddy.link/"
OUT = r"C:/Users/madta/WorkBuddy/2026-08-19-12-24-26/loan-assistant/scripts/e2e_shots/live_login"
os.makedirs(OUT, exist_ok=True)

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
        data = json.loads(ws.recv())
        if data.get("id") == msg_id[0]:
            return data


def eval_js(expr):
    res = send("Runtime.evaluate", {"expression": expr, "returnByValue": True})
    return res.get("result", {}).get("result", {}).get("value")


def shot(name):
    res = send("Page.captureScreenshot", {"format": "png"})
    with open(os.path.join(OUT, name), "wb") as f:
        f.write(base64.b64decode(res["result"]["data"]))
    print("saved:", name)


send("Page.enable")
send("Page.navigate", {"url": BASE + "#/login"})
time.sleep(3)
eval_js("localStorage.clear();")
send("Page.navigate", {"url": BASE + "#/login"})
time.sleep(3)

# 填写表单（触发 Vue 的 input 事件）
eval_js("""
(() => {
  const inputs = [...document.querySelectorAll('input')];
  const set = (el, v) => {
    el.focus();
    el.value = v;
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
    el.blur();
  };
  if (inputs[0]) set(inputs[0], '13800138000');
  if (inputs[1]) set(inputs[1], 'abc123');
  return inputs.map(i => i.type + ':' + i.value);
})()
""")
time.sleep(1)
shot("01_login_filled.png")

# 点击登录按钮
clicked = eval_js("""
(() => {
  const btn = [...document.querySelectorAll('button')].find(b => /登\\s*录/.test(b.innerText));
  if (btn) { btn.click(); return btn.innerText.trim(); }
  return null;
})()
""")
print("clicked button:", clicked)
time.sleep(5)

state = eval_js("""
JSON.stringify({
  hash: location.hash,
  hasToken: !!localStorage.getItem('token'),
  toast: (document.querySelector('.van-toast') || {}).innerText || '',
  body: document.body.innerText.slice(0, 120).replace(/\\n/g, ' | ')
})
""")
print("after login:", state)
shot("02_after_login.png")

# 再等 5 秒看是否被踢回登录页
time.sleep(5)
state2 = eval_js("""
JSON.stringify({
  hash: location.hash,
  hasToken: !!localStorage.getItem('token'),
  toast: (document.querySelector('.van-toast') || {}).innerText || '',
  body: document.body.innerText.slice(0, 120).replace(/\\n/g, ' | ')
})
""")
print("after 10s:", state2)
shot("03_after_10s.png")

# 切到其它 tab 验证接口仍可用
for p in ["products", "customers", "schedules"]:
    send("Page.navigate", {"url": BASE + "#/" + p})
    time.sleep(3)
    s = eval_js("JSON.stringify({hash: location.hash, body: document.body.innerText.slice(0,60).replace(/\\n/g,' | ')})")
    print(p, "->", s)
    shot(f"04_{p}.png")

ws.close()
chrome.terminate()
