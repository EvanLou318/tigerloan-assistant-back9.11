# -*- coding: utf-8 -*-
# 字段级 ASR 语音录入验证：mic 图标渲染 + 完整「录音→转写→填入」链路 + 各页面接入截图
import json, time, subprocess, websocket, urllib.request, os, base64

CHROME = r"C:/Program Files/Google/Chrome/Application/chrome.exe"
PORT = 9242
BASE = "http://localhost:5173/"
OUT_DIR = r"C:/Users/madta/WorkBuddy/2026-08-19-12-24-26/loan-assistant/scripts/e2e_shots/asr_check"
os.makedirs(OUT_DIR, exist_ok=True)

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
    res = send("Runtime.evaluate", {"expression": expr, "returnByValue": True})
    r = res.get("result", {})
    if r.get("exceptionDetails"):
        return "[ERR] " + json.dumps(r["exceptionDetails"].get("text", ""), ensure_ascii=False)
    return r.get("result", {}).get("value")

def screenshot(name):
    res = send("Page.captureScreenshot", {"format": "png"})
    with open(os.path.join(OUT_DIR, name), "wb") as f:
        f.write(base64.b64decode(res["result"]["data"]))
    print("saved:", name)

def goto(path, wait=2.8):
    eval_js(f"localStorage.setItem('token', {json.dumps(TOKEN)}); localStorage.setItem('userInfo', {json.dumps(USER)});")
    send("Page.navigate", {"url": BASE + "#" + path})
    time.sleep(wait)

send("Page.enable")
send("Runtime.enable")
send("Emulation.setDeviceMetricsOverride", {"width": 390, "height": 844, "deviceScaleFactor": 2, "mobile": True})
send("Emulation.setTouchEmulationEnabled", {"enabled": True})

# 先导航到同源页面（about:blank 跨源，localStorage 会丢失），再注入登录态
send("Page.navigate", {"url": BASE + "#/login"})
time.sleep(1.8)
eval_js(f"localStorage.setItem('token', {json.dumps(TOKEN)}); localStorage.setItem('userInfo', {json.dumps(USER)});")

# ---------- 1. 客户建档手动表单：mic 图标 ----------
goto("/customers/create")
# 默认可能落在「语音录入」，切到「手动录入」
eval_js("document.querySelectorAll('.mode-item')[0].click()")
time.sleep(1.2)
mic_n = eval_js("document.querySelectorAll('.voice-mic-btn').length")
print("[customers/create] mic buttons:", mic_n)
screenshot("01_customer_create_mics.png")

# ---------- 2. mic → 面板 → 录音 → 转写 → 填入 全链路 ----------
# 第一个 mic 为姓名输入框
eval_js("document.querySelectorAll('.voice-mic-btn')[0].click()")
time.sleep(1.2)
panel = eval_js("!!document.querySelector('.voice-sheet')")
print("[panel] visible:", panel)
screenshot("02_panel_idle.png")

# 点击开始录音
eval_js("document.querySelector('.mic-circle.idle').click()")
time.sleep(2.2)
print("[recording] timer text:", eval_js("document.querySelector('.vs-timer')?.innerText || 'none'"))
screenshot("03_recording.png")

# 点击停止 → 转写(约2s mock)
eval_js("document.querySelector('.mic-circle.recording').click()")
time.sleep(1.0)
screenshot("04_transcribing.png")
time.sleep(3.0)
rec_text = eval_js("document.querySelector('.vs-textarea')?.value || ''")
print("[transcribed text]:", rec_text[:50])
print("[confidence]:", eval_js("document.querySelector('.vs-conf')?.innerText || ''"))
screenshot("05_done.png")

# 填入 → 校验输入框
eval_js("document.querySelector('.vs-btn.primary').click()")
time.sleep(1.0)
name_val = eval_js("document.querySelectorAll('.van-field input')[0]?.value || ''")
print("[name field after fill]:", name_val)
screenshot("06_filled.png")

# ---------- 3. 产品录入表单（edit 直达 preview 表单） ----------
products = json.loads(urllib.request.urlopen(urllib.request.Request(
    "http://localhost:3001/api/products", headers={"Authorization": f"Bearer {TOKEN}"})).read())
pid = products["data"][0]["id"] if products["data"] else None
if pid:
    goto(f"/products/create?edit={pid}")
    mic_n2 = eval_js("document.querySelectorAll('.voice-mic-btn').length")
    print("[products/create edit] mic buttons:", mic_n2)
    screenshot("07_product_create_mics.png")

# ---------- 4. 日程手动表单 ----------
goto("/schedules/create")
eval_js("document.querySelectorAll('.method')[0].click()")
time.sleep(1.2)
mic_n3 = eval_js("document.querySelectorAll('.voice-mic-btn').length")
print("[schedules/create form] mic buttons:", mic_n3)
screenshot("08_schedule_form_mics.png")

# ---------- 5. 助理聊天输入 ----------
goto("/assistant")
mic_n4 = eval_js("document.querySelectorAll('.voice-mic-btn').length")
print("[assistant] mic buttons:", mic_n4)
screenshot("09_assistant_mic.png")

# ---------- 6. 客户/产品列表搜索 ----------
goto("/customers")
mic_n5 = eval_js("document.querySelectorAll('.voice-mic-btn').length")
print("[customers list search] mic buttons:", mic_n5)
screenshot("10_customer_search_mic.png")

print("DONE ->", OUT_DIR)
chrome.terminate()
