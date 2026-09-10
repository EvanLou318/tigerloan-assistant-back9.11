# -*- coding: utf-8 -*-
# 前端渲染层缺陷排查：真实浏览器跑通核心链路 + 检查控制台错误 / 异常边界
import json, time, subprocess, websocket, urllib.request, os, base64

CHROME = r"C:/Program Files/Google/Chrome/Application/chrome.exe"
PORT = 9293
BASE = "http://127.0.0.1:3007/"
OUT = r"C:/Users/madta/WorkBuddy/2026-08-19-12-24-26/loan-assistant/scripts/e2e_shots/qa"
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
mid = [0]
console_errors = []


def send(method, params=None, wait=True):
    mid[0] += 1
    ws.send(json.dumps({"id": mid[0], "method": method, "params": params or {}}))
    if not wait:
        return
    while True:
        d = json.loads(ws.recv())
        if d.get("method") == "Runtime.consoleAPICalled" and d["params"]["type"] in ("error", "warning"):
            txt = " ".join(str(a.get("value", a.get("description", ""))) for a in d["params"]["args"])
            console_errors.append(txt[:200])
        if d.get("method") == "Runtime.exceptionThrown":
            console_errors.append("UNCAUGHT: " + str(d["params"]["exceptionDetails"].get("text"))[:200])
        if d.get("id") == mid[0]:
            return d


def ev(expr):
    return send("Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True}) \
        .get("result", {}).get("result", {}).get("value")


def shot(name):
    res = send("Page.captureScreenshot", {"format": "png"})
    with open(os.path.join(OUT, name), "wb") as f:
        f.write(base64.b64decode(res["result"]["data"]))


send("Runtime.enable")
send("Page.enable")
send("Emulation.setDeviceMetricsOverride", {"width": 390, "height": 844, "deviceScaleFactor": 2, "mobile": True})
send("Page.navigate", {"url": BASE})
time.sleep(2)
ev(f"localStorage.setItem('token', {json.dumps(TOKEN)}); localStorage.setItem('userInfo', {json.dumps(USER)});")

# 登录后直接调 AI 匹配接口（正确契约）
print("=== AI 匹配接口（正确契约）===")
print(ev("""
(async () => {
  const cust = (await (await fetch('/api/customers', {headers:{'X-Auth-Token': localStorage.getItem('token')}})).json()).data[0];
  const r = await fetch('/api/ai/match', {
    method: 'POST',
    headers: {'Content-Type':'application/json','X-Auth-Token': localStorage.getItem('token')},
    body: JSON.stringify({ customer: cust, products: [] })
  });
  const d = await r.json();
  return JSON.stringify({ status: r.status, ok: d.success, approved: d.data?.approved?.length, rejected: d.data?.rejected?.length });
})()
"""))

routes = ["#/home", "#/products", "#/customers", "#/schedules", "#/profile", "#/assistant"]
print("\n=== 页面遍历（捕获控制台错误）===")
for r in routes:
    before = len(console_errors)
    send("Page.navigate", {"url": BASE + r})
    time.sleep(3)
    txt = ev("document.body.innerText.slice(0, 60).replace(/\\n/g,' | ')")
    errs = console_errors[before:]
    status = "OK" if not errs else f"{len(errs)} errors"
    print(f"  {r:16s} {status:12s} {txt[:50]}")
    for e in errs[:3]:
        print("      !", e)

# 空数据 / 极值渲染
print("\n=== 边界渲染 ===")
print("产品名超长是否溢出卡片:")
print(ev("""
(async () => {
  const r = await fetch('/api/products', {method:'POST', headers:{'Content-Type':'application/json','X-Auth-Token': localStorage.getItem('token')},
    body: JSON.stringify({productName:'这是一个非常非常非常非常非常非常长的产品名称用来测试布局是否会溢出容器',institution:'测试机构名称也特别长特别长特别长',minRate:3,maxRate:5,minAmount:1,maxAmount:10,loanTerm:'12-36个月',repaymentMethod:'等额本息',rateType:'annual',source:'text'})});
  const d = await r.json();
  window.__longp = d.data.id;
  return 'created ' + d.data.id;
})()
"""))
send("Page.navigate", {"url": BASE + "#/products"})
time.sleep(3.5)
print(ev("""
(() => {
  const cards = [...document.querySelectorAll('.product-card')];
  const over = cards.map(c => {
    const name = c.querySelector('.product-name');
    return name ? { text: name.innerText.slice(0,20), sw: name.scrollWidth, cw: name.clientWidth, overflow: name.scrollWidth > name.clientWidth + 1 } : null;
  }).filter(Boolean);
  return JSON.stringify(over.filter(o => o.overflow), null, 1);
})()
"""))
shot("01_product_long.png")

print("\n产品详情页超长渲染:")
ev("window.location.hash = '#/products/' + window.__longp")
time.sleep(3)
shot("02_product_detail_long.png")
print("  bodyText是否有横向溢出:", ev("document.body.scrollWidth > window.innerWidth ? document.body.scrollWidth : 'none'"))

# 清理
ev("fetch('/api/products/' + window.__longp, {method:'DELETE', headers:{'X-Auth-Token': localStorage.getItem('token')}})")

# 会话过期处理
print("\n=== 会话与异常 ===")
print("清空 token 后访问受保护页:")
ev("localStorage.removeItem('token'); localStorage.removeItem('userInfo');")
send("Page.navigate", {"url": BASE + "#/products"})
time.sleep(3)
print("  最终路由:", ev("location.hash"))
print("  是否跳登录页:", "是" if ev("location.hash.includes('/login')") else "否")

chrome.terminate()
print("\n=== 控制台错误汇总 ===")
for e in console_errors[:15]:
    print(" -", e)
print("总计:", len(console_errors))
