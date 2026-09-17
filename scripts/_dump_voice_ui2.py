# -*- coding: utf-8 -*-
"""切到语音录入后 dump 该步骤的按钮，定位录音入口"""
import json, time, subprocess, urllib.request, websocket

BASE = 'http://127.0.0.1:3001'
PORT = 9364
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
    r = raw('Runtime.evaluate', {'expression': e, 'returnByValue': True, 'awaitPromise': True})
    if r.get('exceptionDetails'): return 'ERR:' + str(r['exceptionDetails'].get('text'))
    return r.get('result', {}).get('value')

tok = json.loads(subprocess.run(['curl','-s','--noproxy','*','-X','POST',BASE+'/api/auth/login',
    '-H','Content-Type: application/json','-d','{"phone":"13800138000","password":"abc123"}'],
    capture_output=True, text=True).stdout)
T, U = tok['data']['token'], json.dumps(tok['data']['user'], ensure_ascii=False)
raw('Page.navigate', {'url': BASE}); time.sleep(2.5)
ev(f"localStorage.setItem('token',{json.dumps(T)});localStorage.setItem('userInfo',{json.dumps(U)});1")

raw('Page.navigate', {'url': BASE + '/#/customers/create'}); time.sleep(3)
print('== 点击「语音录入」 ==')
print(ev("""
  (() => {
    const items = [...document.querySelectorAll('.mode-item')];
    const t = items.find(e => (e.textContent||'').includes('语音录入'));
    return t ? t.click() || 'clicked' : 'not found';
  })()
"""))
for wait in (0.5, 1.5, 3.0):
    time.sleep(wait)
    print(f'--- after {wait}s ---')
    print('mode active:', ev("""
      [...document.querySelectorAll('.mode-item')].map(e=>(e.className+':'+e.textContent.trim())).join(' , ')
    """))
    print('buttons:', ev("""
      [...document.querySelectorAll('button')].map(b=>b.textContent.trim().slice(0,24)).filter(Boolean).join(' | ')
    """))
    print('voice-area classes:', ev("""
      [...document.querySelectorAll('[class*=voice],[class*=record],[class*=mic]')]
        .map(e=>e.tagName+'.'+e.className).slice(0,12).join(' , ')
    """))
    print('text:', (ev("document.body.innerText.replace(/\\n+/g,' | ').slice(0,400)") or ''))

proc.terminate()
