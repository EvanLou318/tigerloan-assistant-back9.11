# -*- coding: utf-8 -*-
# 验证产品编辑/录入表单：无多余语音输入、机构联想、期限区间、还款方式枚举
import json, time, subprocess, websocket, urllib.request

CHROME = r"C:/Program Files/Google/Chrome/Application/chrome.exe"
PORT = 9277
BASE = "https://91fbcd73077147039da3de0cbcf2cc12.app.workbuddy.link/"

raw = subprocess.run(["curl", "-s", "-m", "25", "-X", "POST", BASE + "api/auth/login",
                      "-H", "Content-Type: application/json",
                      "-d", json.dumps({"phone": "13800138000", "password": "abc123"})],
                     capture_output=True, text=True).stdout
login = json.loads(raw)
TOKEN, USER = login["data"]["token"], json.dumps(login["data"]["user"], ensure_ascii=False)
pl = subprocess.run(["curl", "-s", "-m", "20", BASE + "api/products", "-H", f"X-Auth-Token: {TOKEN}"],
                    capture_output=True, text=True).stdout
prods = json.loads(pl)["data"]
pid = prods[0]["id"]
print("产品原始 loanTerm:", prods[0].get("loanTerm"), "| 机构:", prods[0].get("institution"))

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


send("Page.enable")
send("Page.navigate", {"url": BASE})
time.sleep(2)
ev(f"localStorage.setItem('token', {json.dumps(TOKEN)}); localStorage.setItem('userInfo', {json.dumps(USER)});")

# 进入编辑页
send("Page.navigate", {"url": BASE + f"#/products/create?edit={pid}"})
time.sleep(4)

print("== 表单结构 ==")
print(ev("""
(() => {
  const rows = [...document.querySelectorAll('.van-cell')].map(c => {
    const label = (c.querySelector('.van-field__label')||{}).innerText || '';
    const inp = c.querySelector('input,textarea');
    return label.trim() + '=' + (inp ? (inp.value||'') : '(readonly)');
  }).filter(Boolean);
  return JSON.stringify({
    rows,
    voiceBtnCount: document.querySelectorAll('[class*=voice-mic], .voice-mic-btn').length,
    rangeFields: document.querySelectorAll('.range-field').length,
  }, null, 1);
})()
"""))

# 点击还款方式
ev("""
(() => {
  const f = [...document.querySelectorAll('.van-cell')].find(c => (c.querySelector('.van-field__label')||{}).innerText?.includes('还款方式'));
  if (f) f.click();
})()
""")
time.sleep(1.5)
print("还款方式弹层:", ev("""
(() => {
  const items = [...document.querySelectorAll('.van-action-sheet__item')].map(i => i.innerText.trim());
  return JSON.stringify(items);
})()
"""))
ev("""
(() => {
  const it = [...document.querySelectorAll('.van-action-sheet__item')].find(i => i.innerText.includes('等额本金'));
  if (it) it.click();
})()
""")
time.sleep(1)
print("选中后还款方式值:", ev("""
(() => {
  const f = [...document.querySelectorAll('.van-cell')].find(c => (c.querySelector('.van-field__label')||{}).innerText?.includes('还款方式'));
  const inp = f && f.querySelector('input');
  return inp ? inp.value : 'none';
})()
"""))

# 机构联想：聚焦所属机构
ev("""
(() => {
  const f = [...document.querySelectorAll('.van-cell')].find(c => (c.querySelector('.van-field__label')||{}).innerText?.includes('所属机构'));
  const inp = f && f.querySelector('input');
  if (inp) {
    inp.focus();
    inp.value = '浦';
    inp.dispatchEvent(new Event('input', {bubbles:true}));
    inp.dispatchEvent(new Event('focus', {bubbles:true}));
  }
})()
""")
time.sleep(1)
print("机构联想 chips:", ev("""
JSON.stringify([...document.querySelectorAll('.suggest-chip')].map(c=>c.innerText.trim()))
"""))

ws.close()
chrome.terminate()
