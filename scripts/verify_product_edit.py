# -*- coding: utf-8 -*-
# 验证：产品详情 → 编辑，不再闪现「选择录入方式」，直接进表单
import json, time, subprocess, websocket, urllib.request, os

CHROME = r"C:/Program Files/Google/Chrome/Application/chrome.exe"
PORT = 9275
BASE = "https://91fbcd73077147039da3de0cbcf2cc12.app.workbuddy.link/"

raw = subprocess.run(["curl", "-s", "-m", "25", "-X", "POST", BASE + "api/auth/login",
                      "-H", "Content-Type: application/json",
                      "-d", json.dumps({"phone": "13800138000", "password": "abc123"})],
                     capture_output=True, text=True).stdout
login = json.loads(raw)
TOKEN, USER = login["data"]["token"], json.dumps(login["data"]["user"], ensure_ascii=False)

pl = subprocess.run(["curl", "-s", "-m", "20", BASE + "api/products", "-H", f"X-Auth-Token: {TOKEN}"],
                    capture_output=True, text=True).stdout
pid = json.loads(pl)["data"][0]["id"]
print("product:", pid)

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
send("Page.navigate", {"url": BASE + f"#/products/{pid}"})
time.sleep(4)

print("详情页有编辑按钮:", ev("[...document.querySelectorAll('button')].some(b=>b.innerText.trim()==='编辑')"))

# 高频采样：点击编辑后 1.2 秒内每 80ms 检查是否出现「选择录入方式」
ev("""
window.__samples = [];
window.__t0 = 0;
(() => {
  const b = [...document.querySelectorAll('button')].find(b => b.innerText.trim() === '编辑');
  window.__t0 = performance.now();
  b.click();
  const tick = () => {
    window.__samples.push({
      t: Math.round(performance.now() - window.__t0),
      hash: location.hash,
      select: document.body.innerText.includes('选择录入方式'),
      loading: document.body.innerText.includes('加载产品信息'),
      form: !!document.querySelector('.preview-step')
    });
    if (performance.now() - window.__t0 < 1500) setTimeout(tick, 80);
  };
  tick();
})()
""")
time.sleep(2.4)
samples = json.loads(ev("JSON.stringify(window.__samples)"))
sel_hits = [s for s in samples if s["select"]]
print("采样次数:", len(samples))
print("出现「选择录入方式」的采样点:", len(sel_hits))
print("出现 loading 的采样点:", len([s for s in samples if s["loading"]]))
print("出现表单的采样点:", len([s for s in samples if s["form"]]))
print("最终 hash:", samples[-1]["hash"] if samples else "n/a")
print("前 5 采样:", json.dumps(samples[:5], ensure_ascii=False))

ws.close()
chrome.terminate()
