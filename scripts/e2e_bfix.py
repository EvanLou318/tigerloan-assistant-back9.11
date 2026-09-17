# -*- coding: utf-8 -*-
# B组修复 e2e：AI 助理执行链路（await 修复后 id 应为真实值，非 undefined）
import json, time, subprocess, websocket, urllib.request, os, base64, sys

CHROME = r"C:/Program Files/Google/Chrome/Application/chrome.exe"
PORT = 9241
BASE = "http://localhost:5173/"
OUT_DIR = r"C:/Users/madta/WorkBuddy/2026-08-19-12-24-26/loan-assistant/scripts/e2e_shots/bfix_flow"
os.makedirs(OUT_DIR, exist_ok=True)
PASS, FAIL = [], []

req = urllib.request.Request(
    "http://localhost:3001/api/auth/login",
    data=json.dumps({"phone": "13800138000", "password": "abc123"}).encode(),
    headers={"Content-Type": "application/json"},
)
login = json.loads(urllib.request.urlopen(req).read())
TOKEN = login["data"]["token"]
USER = json.dumps(login["data"]["user"], ensure_ascii=False)

chrome = subprocess.Popen([
    CHROME, "--headless=new", f"--remote-debugging-port={PORT}",
    "--remote-allow-origins=*", "--disable-gpu", "--no-first-run",
    "--window-size=390,844", "about:blank",
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2.5)

tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json").read())
page = next(t for t in tabs if t["type"] == "page")
ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=60)
msg_id = 0

def send(method, params=None):
    global msg_id
    msg_id += 1
    ws.send(json.dumps({"id": msg_id, "method": method, "params": params or {}}))
    while True:
        data = json.loads(ws.recv())
        if data.get("id") == msg_id:
            return data

def eval_js(expr):
    res = send("Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True})
    r = res.get("result", {}).get("result", {})
    if r.get("subtype") == "error" or res.get("exceptionDetails"):
        return f"__JS_ERROR__ {json.dumps(res.get('exceptionDetails', {}).get('exception', {}).get('description', r.get('description', '')), ensure_ascii=False)}"
    return r.get("value")

def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(f"{name} {detail}")
    print(("PASS " if cond else "FAIL ") + name + (" | " + str(detail)[:120] if detail and not cond else ""))

def shot(name):
    res = send("Page.captureScreenshot", {"format": "png"})
    with open(os.path.join(OUT_DIR, name), "wb") as f:
        f.write(base64.b64decode(res["result"]["data"]))

send("Page.enable")
send("Runtime.enable")
send("Emulation.setDeviceMetricsOverride", {"width": 390, "height": 844, "deviceScaleFactor": 2, "mobile": True})

# ============ 1. AI 助理：新增客户 → 确认执行 → 链接非 undefined ============
send("Page.navigate", {"url": BASE + "#/login"})
time.sleep(2)
eval_js(f"localStorage.setItem('token', {json.dumps(TOKEN)}); localStorage.setItem('userInfo', {json.dumps(USER)});")
send("Page.navigate", {"url": BASE + "#/assistant"})
time.sleep(2.5)

eval_js("""
(() => {
  const input = document.querySelector('.input-bar input.van-field__control');
  if (!input) return 'no input';
  const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
  setter.call(input, '新增客户 王芳 13900139000');
  input.dispatchEvent(new Event('input', { bubbles: true }));
  return 'ok';
})()
""")
time.sleep(0.5)
# 点击输入框右侧区域之外的发送按钮（向上箭头圆形按钮）
send_clicked = eval_js("""
(() => {
  const btn = [...document.querySelectorAll('.input-bar button, .input-bar [role=button], button')].find(b => {
    const cls = b.className || '';
    return (cls.includes('send') || cls.includes('up')) && !cls.includes('voice');
  });
  if (btn) { btn.click(); return 'btn:' + btn.className; }
  // 兜底：在 input 上回车
  const input = document.querySelector('.input-bar input.van-field__control');
  if (input) {
    input.dispatchEvent(new KeyboardEvent('keyup', { key: 'Enter', bubbles: true }));
    return 'enter';
  }
  return 'none';
})()
""")
print("send:", send_clicked)
# 等待 AI 回复（真实 LLM 1~3s）+ 确认卡出现
time.sleep(6)
btns = eval_js("[...document.querySelectorAll('button')].filter(b => b.textContent.includes('确认执行')).length")
check("助理确认卡出现", btns and btns > 0, f"确认执行按钮数={btns}")
shot("01_assistant_action_card.png")

before = eval_js("JSON.parse(localStorage.getItem('userInfo') || '{}').name || 'x'")
eval_js("[...document.querySelectorAll('button')].find(b => b.textContent.includes('确认执行')).click()")
time.sleep(2.5)
# 检查消息链接是否为真实 id（/customers/数字）而非 /customers/undefined
link_info = eval_js("""
(() => {
  const links = [...document.querySelectorAll('.card-link')].map(e => e.textContent.trim());
  const done = [...document.querySelectorAll('.card-done')].map(e => e.textContent.trim());
  return JSON.stringify({ links, done });
})()
""")
try:
    li = json.loads(link_info)
except Exception:
    li = {}
check("执行完成徽标出现", any("已执行" in d for d in li.get("done", [])), link_info)
bad_link = [l for l in li.get("links", []) if "undefined" in l]
check("跳转链接不含 undefined", len(li.get("links", [])) > 0 and not bad_link, link_info)
shot("02_assistant_done.png")

# ============ 2. 客户详情：推演记录渲染不崩溃（可选链兜底） ============
send("Page.navigate", {"url": BASE + "#/customers"})
time.sleep(2.5)
first_id = eval_js("window.__pinia_customer_first ? '' : (document.querySelector('.customer-card, [class*=card]') ? 'has-card' : 'no-card')")
# 直接取列表第一个客户 id 跳详情
eval_js("""
(() => {
  const c = document.querySelector('.page-container');
  return c ? 'page-ok' : 'no-page';
})()
""")
# 用 store 数据取第一个客户 id：通过 URL 进入列表后点击第一张卡
clicked = eval_js("""
(() => {
  const card = document.querySelector('.customer-card, .cust-card, [class*="customer"] [class*="card"]');
  if (card) { card.click(); return 'clicked'; }
  return 'no-card';
})()
""")
time.sleep(2.5)
url_now = eval_js("location.hash")
if "/customers/" in str(url_now):
    err = eval_js("document.body.innerText.includes('TypeError') || document.body.innerText.trim() === '' ? 'render-issue' : 'render-ok'")
    check("客户详情页正常渲染", err == "render-ok", f"hash={url_now}")
    shot("03_customer_detail.png")
else:
    check("客户详情页正常渲染", False, f"未进入详情, hash={url_now}, click={clicked}")

# ============ 3. 场景推演：空结果保存被拦截 ============
m = eval_js("location.hash")
print("detail hash:", m)

print(f"\n===== 结果: {len(PASS)} PASS / {len(FAIL)} FAIL =====")
for f in FAIL:
    print("FAIL:", f)
