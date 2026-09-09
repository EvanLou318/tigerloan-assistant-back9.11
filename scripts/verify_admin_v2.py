# -*- coding: utf-8 -*-
# 安全页(审计面板) + 三方服务页 浏览器端到端验证
import json, time, subprocess, websocket, urllib.request, os, base64

CHROME = r"C:/Program Files/Google/Chrome/Application/chrome.exe"
PORT = 9233
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
print("login ok, role =", login["data"]["user"]["role"])

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
errors = []

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

def goto(path, wait, check, label):
    eval_js(f"localStorage.setItem('token', {json.dumps(TOKEN)}); localStorage.setItem('userInfo', {json.dumps(USER)});")
    send("Page.navigate", {"url": BASE + "#" + path})
    time.sleep(wait)
    val = eval_js(check)
    ok = val and not str(val).startswith("FAIL")
    print(f"  [{'OK' if ok else 'FAIL'}] {label} => {val}")
    if not ok:
        errors.append(f"{path}: {val}")

send("Page.enable")
send("Runtime.enable")
send("Emulation.setDeviceMetricsOverride", {"width": 1440, "height": 900, "deviceScaleFactor": 1, "mobile": False})

send("Page.navigate", {"url": BASE + "#/login"})
time.sleep(3)

# 1. 权限与安全页：角色矩阵 + 操作审计
goto("/admin/security", wait=3.5, check="""(() => {
    const t = document.body.innerText;
    const miss = [];
    if (!t.includes('角色权限矩阵')) miss.push('缺矩阵标题');
    if (!t.includes('管理员') || !t.includes('团队主管')) miss.push('缺角色Tab');
    if (!t.includes('admin.roles.manage')) miss.push('缺权限码列表');
    if (!t.includes('操作审计')) miss.push('缺审计面板');
    if (!t.includes('创建用户') || !t.includes('删除用户')) miss.push('缺审计动作记录');
    if (!t.includes('李经理')) miss.push('缺审计操作人');
    return miss.length ? 'FAIL:' + miss.join(',') : 'OK: 矩阵+审计面板+留痕数据';
})()""", label="权限与安全页(含审计)")
screenshot("verify_security_audit.png")

# 2. 三方服务页
goto("/admin/services", wait=3, check="""(() => {
    const t = document.body.innerText;
    const miss = [];
    if (!t.includes('大模型（LLM）')) miss.push('缺LLM卡片');
    if (!t.includes('文字识别（OCR）')) miss.push('缺OCR卡片');
    if (!t.includes('语音识别（ASR）')) miss.push('缺ASR卡片');
    if (!t.includes('模拟模式')) miss.push('缺模式徽标');
    if (!t.includes('真实调用') && !t.includes('Mock')) miss.push('顶栏徽标未更新');
    return miss.length ? 'FAIL:' + miss.join(',') : 'OK: 三分类卡片+徽标';
})()""", label="三方服务页")
screenshot("verify_services.png")

print("\n==== 结果 ====")
print("FAILED:", errors) if errors else print("ALL PASS")
chrome.terminate()
