# -*- coding: utf-8 -*-
# 校验：客户档案页配色已收敛 + 录入方式弹框无多余图标
import json, time, subprocess, websocket, urllib.request, os

CHROME = r"C:/Program Files/Google/Chrome/Application/chrome.exe"
PORT = 9273
BASE = "https://91fbcd73077147039da3de0cbcf2cc12.app.workbuddy.link/"

raw = subprocess.run(["curl", "-s", "-m", "25", "-X", "POST", BASE + "api/auth/login",
                      "-H", "Content-Type: application/json",
                      "-d", json.dumps({"phone": "13800138000", "password": "abc123"})],
                     capture_output=True, text=True).stdout
login = json.loads(raw)
TOKEN, USER = login["data"]["token"], json.dumps(login["data"]["user"], ensure_ascii=False)

lst = subprocess.run(["curl", "-s", "-m", "20", BASE + "api/customers", "-H", f"X-Auth-Token: {TOKEN}"],
                     capture_output=True, text=True).stdout
cid = json.loads(lst)["data"][0]["id"]

chrome = subprocess.Popen([CHROME, "--headless=new", f"--remote-debugging-port={PORT}",
                           "--remote-allow-origins=*", "--disable-gpu", "--no-first-run",
                           "--window-size=390,844", "about:blank"],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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


send("Page.enable")
send("Page.navigate", {"url": BASE})
time.sleep(2)
ev(f"localStorage.setItem('token', {json.dumps(TOKEN)}); localStorage.setItem('userInfo', {json.dumps(USER)});")
send("Page.navigate", {"url": BASE + f"#/customers/{cid}"})
time.sleep(4)

print("== 客户档案页配色 ==")
print(ev("""
(() => {
  const g = (sel, props) => {
    const el = document.querySelector(sel);
    if (!el) return sel + ': NOT FOUND';
    const cs = getComputedStyle(el);
    return sel + ' -> ' + props.map(p => p + '=' + cs[p]).join(' , ');
  };
  return JSON.stringify([
    g('.customer-avatar', ['backgroundColor','color']),
    g('.header-meta', ['fontSize','color']),
    g('.stat', ['backgroundColor']),
    g('.stat-value', ['color','fontSize']),
    g('.material-entry', ['backgroundColor']),
    g('.entry-icon', ['backgroundColor']),
    g('.mat-icon', ['backgroundColor']),
    g('.completeness-fill', ['backgroundColor','boxShadow']),
    g('.risk-badge', ['backgroundColor','color']),
  ], null, 1);
})()
"""))
print(ev("""
(() => {
  const box = (sel) => {
    const el = document.querySelector(sel);
    if (!el) return sel + ': none';
    const r = el.getBoundingClientRect();
    return sel + ' w=' + Math.round(r.width) + ' h=' + Math.round(r.height);
  };
  const stats = [...document.querySelectorAll('.stat')].map(e => Math.round(e.getBoundingClientRect().width));
  return JSON.stringify([box('.material-item'), box('.header-stats'), box('.customer-header'), 'stat widths: ' + stats.join(','), 'stat rows y: ' + [...document.querySelectorAll('.stat')].map(e=>Math.round(e.getBoundingClientRect().top)).join(',')], null, 1);
})()
"""))
print("tag 元素残留:", ev("document.querySelectorAll('.customer-header .tag').length"))
print("头部 svg 数:", ev("document.querySelectorAll('.customer-header svg').length"))

# 打开录入方式弹框
send("Page.navigate", {"url": BASE + "#/home"})
time.sleep(3.5)
ev("""
(() => {
  const n = [...document.querySelectorAll('*')].find(e => e.children.length===0 && (e.innerText||'').trim()==='新建日程');
  if (n) n.click();
})()
""")
time.sleep(2)
print("== 录入方式弹框 ==")
print(ev("""
(() => {
  const items = [...document.querySelectorAll('.van-action-sheet__item')];
  return JSON.stringify(items.map(it => ({
    name: (it.innerText||'').split('\\n')[0],
    svg: it.querySelectorAll('svg').length,
    vantFontIcon: it.querySelectorAll('i[class*="van-icon"]').length
  })), null, 1);
})()
"""))

ws.close()
chrome.terminate()
