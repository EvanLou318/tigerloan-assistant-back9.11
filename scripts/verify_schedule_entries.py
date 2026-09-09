# -*- coding: utf-8 -*-
# 冒烟：首页快捷入口/客户详情「新建日程」均弹底弹框；选文本后携客户信息进创建页
import json, time, subprocess, websocket, urllib.request, os, base64

CHROME = r"C:/Program Files/Google/Chrome/Application/chrome.exe"
PORT = 9257
BASE = "http://localhost:5173/"
OUT_DIR = r"C:/Users/madta/WorkBuddy/2026-08-19-12-24-26/loan-assistant/scripts/e2e_shots/sched_entries"
os.makedirs(OUT_DIR, exist_ok=True)

req = urllib.request.Request("http://localhost:3001/api/auth/login",
    data=json.dumps({"phone": "13800138000", "password": "abc123"}).encode(),
    headers={"Content-Type": "application/json"})
login = json.loads(urllib.request.urlopen(req).read())
TOKEN = login["data"]["token"]; USER = json.dumps(login["data"]["user"], ensure_ascii=False)

chrome = subprocess.Popen([CHROME, "--headless=new", f"--remote-debugging-port={PORT}",
    "--remote-allow-origins=*", "--disable-gpu", "--no-first-run", "--window-size=390,844", "about:blank"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2.5)
tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json").read())
page = next(t for t in tabs if t["type"] == "page")
ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=30); mid = 0

def send(m, p=None):
    global mid; mid += 1; ws.send(json.dumps({"id": mid, "method": m, "params": p or {}}))
    while True:
        d = json.loads(ws.recv())
        if d.get("id") == mid: return d

def ev(e):
    r = send("Runtime.evaluate", {"expression": e, "returnByValue": True})
    res = r.get("result", {})
    if res.get("subtype") == "error": return "EVAL-ERR: " + str(res.get("description"))[:300]
    return res.get("result", {}).get("value")

def shot(name):
    res = send("Page.captureScreenshot", {"format": "png"})
    with open(os.path.join(OUT_DIR, name), "wb") as f:
        f.write(base64.b64decode(res["result"]["data"]))
    print("shot:", name)

def click_leaf_text(text):
    return ev(f"""
(() => {{
  const els = Array.from(document.querySelectorAll('div,span,button,li,p,a'));
  const matches = els.filter(n => n.textContent.trim() === '{text}');
  if (!matches.length) return 'not-found:' + '{text}';
  const inner = matches.find(n => !matches.some(m => m !== n && n.contains(m)));
  inner.click(); return 'clicked';
}})()
""")

send("Page.enable"); send("Runtime.enable")
send("Emulation.setDeviceMetricsOverride", {"width": 390, "height": 844, "deviceScaleFactor": 2, "mobile": True})
send("Emulation.setTouchEmulationEnabled", {"enabled": True})
send("Page.navigate", {"url": BASE + "#/login"}); time.sleep(3.5)
ev(f"localStorage.setItem('token',{json.dumps(TOKEN)}); localStorage.setItem('userInfo',{json.dumps(USER)})")

# ---- 1) 首页快捷入口「新建日程」→ 底弹框 ----
ev("location.hash='#/'"); time.sleep(2.8)
print("home entry click:", click_leaf_text("新建日程"))
time.sleep(1.3)
print("A sheet:", ev("!!document.querySelector('.van-action-sheet')"),
      "| title:", ev("(document.querySelector('.van-action-sheet__header')||{}).textContent"))
shot("A1_home_entry_sheet.png")
# 取消关闭
ev("(document.querySelector('.van-action-sheet__cancel')||{}).click ? document.querySelector('.van-action-sheet__cancel').click() : ''"); time.sleep(1)

# ---- 2) 客户详情「新建日程」→ 底弹框 → 文本录入携带客户 ----
cust_req = urllib.request.Request("http://localhost:3001/api/customers", headers={"Authorization": "Bearer " + TOKEN})
cid = json.loads(urllib.request.urlopen(cust_req).read())["data"][0]["id"]
print("first customer id:", cid)
ev(f"location.hash='#/customers/{cid}'"); time.sleep(3)
print("detail entry click:", click_leaf_text("新建日程"))
time.sleep(1.3)
print("B sheet:", ev("!!document.querySelector('.van-action-sheet')"))
shot("B1_detail_entry_sheet.png")
print("pick text:", ev("(()=>{const n=Array.from(document.querySelectorAll('.van-action-sheet__item')).find(x=>x.textContent.includes('文本录入')); if(n){n.click();return 'clicked'}return 'nf'})()"))
time.sleep(2.2)
hash_ = ev("location.hash") or ""
print("hash:", hash_)
print("form step:", ev("!!document.querySelector('.form-step')"))
# 关联客户预填值（van-field label=关联客户 的输入值）
cust_val = ev("""(() => {
  const cells = Array.from(document.querySelectorAll('.van-cell,.van-field'));
  const c = cells.find(x => (x.querySelector('.van-field__label, .van-cell__title')||{}).textContent === '关联客户');
  const inp = c && (c.querySelector('.van-field__control')||c.querySelector('.van-cell__value'));
  return inp ? inp.value || inp.textContent.trim() : 'none';
})()""")
print("linked customer shown:", cust_val)
shot("C1_create_form_prefill.png")

print("DONE")
chrome.terminate()
