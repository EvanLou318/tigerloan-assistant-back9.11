# -*- coding: utf-8 -*-
"""dump 客户建档页的语音入口 DOM，用于写准确定位器"""
import json, time, subprocess, urllib.request, websocket

BASE = 'http://127.0.0.1:3001'
PORT = 9363
CHROME = r'C:/Program Files/Google/Chrome/Application/chrome.exe'

proc = subprocess.Popen([CHROME, '--headless=new', f'--remote-debugging-port={PORT}',
                         '--remote-allow-origins=*', '--window-size=390,844', '--disable-gpu',
                         '--no-first-run', '--use-fake-ui-for-media-stream',
                         '--use-fake-device-for-media-stream', 'about:blank'],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2)
for _ in range(60):
    try:
        urllib.request.urlopen(f'http://127.0.0.1:{PORT}/json/version', timeout=2); break
    except Exception: time.sleep(0.5)
tgt = json.loads(urllib.request.urlopen(urllib.request.Request(
    f'http://127.0.0.1:{PORT}/json/new?about:blank', method='PUT'), timeout=5).read())
ws = websocket.create_connection(tgt['webSocketDebuggerUrl'], timeout=40)
n = [0]
def raw(m, p=None):
    n[0] += 1; mid = n[0]
    ws.send(json.dumps({'id': mid, 'method': m, 'params': p or {}}))
    while True:
        r = json.loads(ws.recv())
        if r.get('id') == mid: return r.get('result', {})
def ev(e):
    return raw('Runtime.evaluate', {'expression': e, 'returnByValue': True, 'awaitPromise': True}).get('result', {}).get('value')

tok = json.loads(subprocess.run(['curl','-s','--noproxy','*','-X','POST',BASE+'/api/auth/login',
    '-H','Content-Type: application/json','-d','{"phone":"13800138000","password":"abc123"}'],
    capture_output=True, text=True).stdout)
T, U = tok['data']['token'], json.dumps(tok['data']['user'], ensure_ascii=False)
raw('Page.navigate', {'url': BASE}); time.sleep(2.5)
ev(f"localStorage.setItem('token',{json.dumps(T)});localStorage.setItem('userInfo',{json.dumps(U)});1")

for route in ['/#/customers/create']:
    raw('Page.navigate', {'url': BASE + route}); time.sleep(3)
    print(f'=== {route} ===')
    print('URL:', ev('location.href'))
    print('--- 可点击文本 ---')
    print(ev("""
      [...document.querySelectorAll('button, .method-item, .mode-item, [class*=mode], [class*=method], .van-radio, label')]
        .map(e => (e.tagName + '|' + (e.className||'') + '|' + (e.textContent||'').trim().slice(0,30)))
        .filter(s => s.length > 4).slice(0, 40).join('\\n')
    """))
    print('--- body 前 800 字符文本 ---')
    print((ev("document.body.innerText.replace(/\\n+/g,' | ').slice(0,800)") or ''))

proc.terminate()
