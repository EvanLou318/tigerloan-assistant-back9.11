# -*- coding: utf-8 -*-
# 三方服务管理页端到端验证：真实 JWT -> 渲染检查 + 截图
import json
import time
import subprocess
import websocket
import urllib.request
import os
import base64

CHROME = r"C:/Program Files/Google/Chrome/Application/chrome.exe"
PORT = 9231
BASE = "http://localhost:5173/"
OUT_DIR = r"C:/Users/madta/WorkBuddy/2026-08-19-12-24-26/loan-assistant/scripts/e2e_shots"
os.makedirs(OUT_DIR, exist_ok=True)

req = urllib.request.Request(
    "http://localhost:3001/api/auth/login",
    data=json.dumps({"phone": "13800138000", "password": "abc123"}).encode(),
    headers={"Content-Type": "application/json"},
)
login = json.loads(urllib.request.urlopen(req).read())
TOKEN = login["data"]["token"]
USER = json.dumps(login["data"]["user"], ensure_ascii=False)
print("login ok, role =", login["data"]["user"]["role"], "perms =", len(login["data"]["user"]["permissions"]))

chrome = subprocess.Popen([
    CHROME, "--headless=new", f"--remote-debugging-port={PORT}",
    "--remote-allow-origins=*", "--disable-gpu", "--no-first-run",
    "--window-size=1440,900", "about:blank",
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2.5)

tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json").read())
page = next(t for t in tabs if t["type"] == "page")
ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=30)
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
    return res.get("result", {}).get("result", {}).get("value")

def screenshot(name):
    res = send("Page.captureScreenshot", {"format": "png"})
    with open(os.path.join(OUT_DIR, name), "wb") as f:
        f.write(base64.b64decode(res["result"]["data"]))
    print("saved:", name)

errors = []

def goto(path, wait=2.5, check=None, label=""):
    eval_js(f"localStorage.setItem('token', {json.dumps(TOKEN)}); localStorage.setItem('userInfo', {json.dumps(USER)});")
    send("Page.navigate", {"url": BASE + "#" + path})
    time.sleep(wait)
    if check:
        val = eval_js(check)
        ok = val and not str(val).startswith("FAIL")
        print(f"  [{'OK' if ok else 'FAIL'}] {label} => {val}")
        if not ok:
            errors.append(f"{path}: {val}")

send("Page.enable")
send("Runtime.enable")
send("Emulation.setDeviceMetricsOverride", {"width": 1440, "height": 900, "deviceScaleFactor": 1, "mobile": False})

send("Page.navigate", {"url": BASE + "#/login"})
time.sleep(2.5)

# 1. 服务管理页：三个分类卡片 + 模拟模式徽标 + 侧边栏菜单
goto("/admin/services", wait=3.5,
     check="""(() => {
        const t = document.body.innerText;
        const miss = [];
        if (!t.includes('大模型（LLM）')) miss.push('缺LLM分类');
        if (!t.includes('文字识别（OCR）')) miss.push('缺OCR分类');
        if (!t.includes('语音识别（ASR）')) miss.push('缺ASR分类');
        if (!t.includes('模拟模式')) miss.push('缺模拟徽标');
        if (!t.includes('三方服务')) miss.push('缺页面标题');
        const nav = document.querySelector('.admin-sidebar');
        if (nav && !nav.innerText.includes('三方服务')) miss.push('侧边栏缺菜单');
        return miss.length ? 'FAIL:' + miss.join(',') : 'OK: 三分类+徽标+菜单';
     })()""",
     label="三方服务页渲染")
screenshot("admin_services_empty.png")

# 2. 新增供应商弹窗交互
eval_js("""(() => {
   const btns = [...document.querySelectorAll('.add-btn')];
   if (!btns.length) return 'FAIL:无添加按钮';
   btns[0].click();
   return 'OK';
})()""")
time.sleep(1)
val = eval_js("""(() => {
   const modal = document.querySelector('.modal');
   if (!modal) return 'FAIL:弹窗未出现';
   return modal.innerText.includes('供应商') ? 'OK: 弹窗正常' : 'FAIL:弹窗内容异常';
})()""")
print(f"  [{'OK' if str(val).startswith('OK') else 'FAIL'}] 新增供应商弹窗 => {val}")
screenshot("admin_services_modal.png")
if not str(val).startswith("OK"):
    errors.append("modal: " + str(val))

# 3. 已配置供应商的"真实调用"态（对库里真实存在的默认供应商断言）
goto("/admin/services", wait=3,
     check="""(() => {
        const t = document.body.innerText;
        if (!t.includes('真实调用')) return 'FAIL: 未出现真实调用徽标';
        if (!t.includes('DeepSeek')) return 'FAIL: 未渲染 DeepSeek 供应商行';
        if (!t.includes('sk-d****')) return 'FAIL: API Key 未脱敏显示';
        return 'OK: 真实调用态 + key脱敏';
     })()""",
     label="配置后真实调用态")
screenshot("admin_services_configured.png")

print("\n==== 结果 ====")
if errors:
    print("FAILED:", errors)
else:
    print("ALL PASS")

chrome.terminate()
