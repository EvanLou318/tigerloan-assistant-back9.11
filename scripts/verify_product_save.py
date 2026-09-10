# -*- coding: utf-8 -*-
# 端到端：编辑产品 → 改期限/还款方式 → 保存 → 校验存储格式 → 还原
import json, time, subprocess, websocket, urllib.request

CHROME = r"C:/Program Files/Google/Chrome/Application/chrome.exe"
PORT = 9279
BASE = "https://91fbcd73077147039da3de0cbcf2cc12.app.workbuddy.link/"
H = ["-H", "X-Auth-Token: {}"]

raw = subprocess.run(["curl", "-s", "-m", "25", "-X", "POST", BASE + "api/auth/login",
                      "-H", "Content-Type: application/json",
                      "-d", json.dumps({"phone": "13800138000", "password": "abc123"})],
                     capture_output=True, text=True).stdout
login = json.loads(raw)
TOKEN, USER = login["data"]["token"], json.dumps(login["data"]["user"], ensure_ascii=False)


def api(path, method="GET", body=None):
    cmd = ["curl", "-s", "-m", "20", "-X", method, BASE + path, "-H", f"X-Auth-Token: {TOKEN}"]
    if body:
        cmd += ["-H", "Content-Type: application/json", "-d", json.dumps(body, ensure_ascii=False)]
    return json.loads(subprocess.run(cmd, capture_output=True, text=True).stdout)


prods = api("api/products")["data"]
p0 = prods[0]
pid = p0["id"]
orig = {"loanTerm": p0.get("loanTerm"), "repaymentMethod": p0.get("repaymentMethod")}
print("原始:", orig)

chrome = subprocess.Popen([CHROME, "--headless=new", f"--remote-debugging-port={PORT}",
                           "--remote-allow-origins=*", "--disable-gpu", "--no-first-run",
                           "--window-size=390,844", "about:blank"],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2.5)
tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json").read())
page = next(t for t in tabs if t["type"] == "page")
ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=40)
mid = [0]


def send(m, p=None):
    mid[0] += 1
    ws.send(json.dumps({"id": mid[0], "method": m, "params": p or {}}))
    while True:
        d = json.loads(ws.recv())
        if d.get("id") == mid[0]:
            return d


def ev(e):
    return send("Runtime.evaluate", {"expression": e, "returnByValue": True}).get("result", {}).get("result", {}).get("value")


def edit_via_ui(min_t, max_t, repay):
    send("Page.navigate", {"url": BASE + f"#/products/create?edit={pid}"})
    time.sleep(4)
    js = """
    (() => {
      const cell = (t) => [...document.querySelectorAll('.van-cell')].find(c => (c.querySelector('.van-field__label')||{}).innerText?.includes(t));
      const setVal = (t, v) => {
        const c = cell(t); const inp = c && c.querySelector('input');
        if (inp) { inp.value = v; inp.dispatchEvent(new Event('input', {bubbles:true})); }
      };
      setVal('最短', '__MIN__');
      setVal('最长', '__MAX__');
      const rc = cell('还款方式'); if (rc) rc.click();
    })()
    """.replace('__MIN__', str(min_t)).replace('__MAX__', str(max_t))
    ev(js)
    time.sleep(1.2)
    ev("""
    (() => {
      const it = [...document.querySelectorAll('.van-action-sheet__item')].find(i => i.innerText.includes('__REPAY__'));
      if (it) it.click();
    })()
    """.replace('__REPAY__', repay))
    time.sleep(1)
    ev("""
    (() => {
      const b = [...document.querySelectorAll('button')].find(b => b.innerText.includes('确认保存'));
      if (b) b.click();
    })()
    """)
    time.sleep(3.5)


send("Page.enable")
send("Page.navigate", {"url": BASE})
time.sleep(2)
ev(f"localStorage.setItem('token', {json.dumps(TOKEN)}); localStorage.setItem('userInfo', {json.dumps(USER)});")

edit_via_ui(12, 24, "随借随还")
after = api(f"api/products/{pid}")
d = after.get("data", after)
print("保存后:", {k: d.get(k) for k in ["loanTerm", "repaymentMethod"]})
ok = d.get("loanTerm") == "12-24个月" and d.get("repaymentMethod") == "随借随还"
print("格式校验:", "PASS" if ok else "FAIL")

# 还原
edit_via_ui(6, 36, "等额本息")
back = api(f"api/products/{pid}")
bd = back.get("data", back)
print("还原后:", {k: bd.get(k) for k in ["loanTerm", "repaymentMethod"]})

ws.close()
chrome.terminate()
