# -*- coding: utf-8 -*-
# 日程交互 e2e：方式弹层直达三种录入模式 + 详情面板标记完成
import json, time, subprocess, websocket, urllib.request, os, base64

CHROME = r"C:/Program Files/Google/Chrome/Application/chrome.exe"
PORT = 9253
BASE = "http://localhost:5173/"
OUT_DIR = r"C:/Users/madta/WorkBuddy/2026-08-19-12-24-26/loan-assistant/scripts/e2e_shots/sched_check"
os.makedirs(OUT_DIR, exist_ok=True)

req = urllib.request.Request("http://localhost:3001/api/auth/login",
    data=json.dumps({"phone":"13800138000","password":"abc123"}).encode(),
    headers={"Content-Type":"application/json"})
login = json.loads(urllib.request.urlopen(req).read())
TOKEN = login["data"]["token"]; USER = json.dumps(login["data"]["user"], ensure_ascii=False)

chrome = subprocess.Popen([CHROME,"--headless=new",f"--remote-debugging-port={PORT}","--remote-allow-origins=*","--disable-gpu","--no-first-run","--window-size=390,844","about:blank"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2.5)
tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json").read())
page = next(t for t in tabs if t["type"]=="page")
ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=30); mid=0
def send(m,p=None):
    global mid; mid+=1; ws.send(json.dumps({"id":mid,"method":m,"params":p or {}}))
    while True:
        d=json.loads(ws.recv())
        if d.get("id")==mid: return d
def ev(e):
    r=send("Runtime.evaluate",{"expression":e,"returnByValue":True})
    res=r.get("result",{})
    if res.get("subtype")=="error": return "EVAL-ERR: "+str(res.get("description"))[:200]
    return res.get("result",{}).get("value")
def shot(name):
    res = send("Page.captureScreenshot", {"format":"png"})
    with open(os.path.join(OUT_DIR,name),"wb") as f:
        f.write(base64.b64decode(res["result"]["data"]))
    print("shot:", name)
def click_text(sel, text):
    return ev(f"""
(() => {{
  const nodes = Array.from(document.querySelectorAll('{sel}'));
  const t = nodes.find(n => n.textContent.trim().includes('{text}'));
  if (t) {{ t.click(); return 'clicked'; }}
  return 'not-found';
}})()
""")

send("Page.enable"); send("Runtime.enable")
send("Emulation.setDeviceMetricsOverride",{"width":390,"height":844,"deviceScaleFactor":2,"mobile":True})
send("Emulation.setTouchEmulationEnabled",{"enabled":True})
send("Page.navigate",{"url":BASE+"#/login"}); time.sleep(3.5)
ev(f"localStorage.setItem('token',{json.dumps(TOKEN)}); localStorage.setItem('userInfo',{json.dumps(USER)})")

# ---- 1) 列表页 FAB -> 弹层 ----
ev("location.hash='#/schedules'"); time.sleep(2.5)
print("fab click:", ev("document.querySelector('.fab') && (document.querySelector('.fab').click(),'ok')"))
time.sleep(1.2)
print("sheet visible:", ev("!!document.querySelector('.van-action-sheet')"))
shot("01_method_sheet.png")

# ---- 2) 选语音 -> voice step ----
print("pick voice:", click_text(".van-action-sheet__item", "语音录入"))
time.sleep(2)
print("voice step:", ev("!!document.querySelector('.voice-step')"), "| hash:", ev("location.hash"))
shot("02_voice_step.png")

# ---- 3) 返回 -> 弹层 -> 手写 ----
ev("history.back()"); time.sleep(2)
print("fab click 2:", ev("document.querySelector('.fab') && (document.querySelector('.fab').click(),'ok')"))
time.sleep(1)
print("pick hw:", click_text(".van-action-sheet__item", "手写录入"))
time.sleep(2)
print("hw step:", ev("!!document.querySelector('.handwriting-step')"), "| canvas:", ev("!!document.querySelector('.hw-canvas')"))
shot("03_handwriting_step.png")

# ---- 4) 返回 -> 弹层 -> 文本表单 ----
ev("history.back()"); time.sleep(2)
ev("document.querySelector('.fab').click()"); time.sleep(1)
print("pick text:", click_text(".van-action-sheet__item", "文本录入"))
time.sleep(2)
print("form step:", ev("!!document.querySelector('.form-step')"), "| title:", ev("document.querySelector('.van-nav-bar__title').textContent"))
shot("04_text_form.png")

# ---- 5) 列表点卡片 -> 详情面板 -> 标记完成 ----
ev("location.hash='#/schedules'"); time.sleep(2)
# 切到全部 tab 确保有卡片
click_text(".tab-item", "全部"); time.sleep(0.8)
n = ev("document.querySelectorAll('.schedule-card').length")
print("cards:", n)
if n and n != '0':
    ev("document.querySelector('.schedule-card').click()"); time.sleep(1.2)
    print("detail popup:", ev("!!document.querySelector('.detail-popup')"))
    shot("05_detail_panel.png")
    r = click_text(".dp-actions button", "标记完成")
    print("mark done:", r)
    time.sleep(1.5)
    print("popup closed:", ev("!document.querySelector('.detail-popup, .van-popup:visible')"))
    shot("06_after_done.png")

print("DONE")
chrome.terminate()