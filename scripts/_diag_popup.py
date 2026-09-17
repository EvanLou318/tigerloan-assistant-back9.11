# -*- coding: utf-8 -*-
# 诊断：Vant popup 关闭后 DOM 是否残留
import json, time, subprocess, urllib.request, websocket

CHROME = r'C:/Program Files/Google/Chrome/Application/chrome.exe'
P = 9345
proc = subprocess.Popen([CHROME, '--headless=new', f'--remote-debugging-port={P}',
                         '--remote-allow-origins=*', '--window-size=390,844',
                         '--disable-gpu', '--no-first-run', 'about:blank'],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
for _ in range(60):
    try:
        urllib.request.urlopen(f'http://127.0.0.1:{P}/json/version', timeout=2)
        break
    except Exception:
        time.sleep(0.5)
tgt = json.loads(urllib.request.urlopen(urllib.request.Request(
    f'http://127.0.0.1:{P}/json/new?about:blank', method='PUT'), timeout=5).read())
ws = websocket.create_connection(tgt['webSocketDebuggerUrl'], timeout=30)
n = [0]


def raw(method, params=None):
    n[0] += 1
    mid = n[0]
    ws.send(json.dumps({'id': mid, 'method': method, 'params': params or {}}))
    while True:
        m = json.loads(ws.recv())
        if m.get('id') == mid:
            return m.get('result', {})


def ev(e):
    r = raw('Runtime.evaluate', {'expression': e, 'returnByValue': True, 'awaitPromise': True})
    return r.get('result', {}).get('value')


tok = json.loads(subprocess.run(
    ['curl', '-s', '--noproxy', '*', '-X', 'POST', 'http://127.0.0.1:3001/api/auth/login',
     '-H', 'Content-Type: application/json',
     '-d', '{"phone":"13800138000","password":"abc123"}'],
    capture_output=True, text=True).stdout)
T, U = tok['data']['token'], json.dumps(tok['data']['user'], ensure_ascii=False)

raw('Page.navigate', {'url': 'http://127.0.0.1:5173/'})
time.sleep(2)
ev(f"localStorage.setItem('token',{json.dumps(T)});localStorage.setItem('userInfo',{json.dumps(U)});1")
raw('Page.navigate', {'url': 'http://127.0.0.1:5173/#/home'})
time.sleep(3)

print('rows                =', ev("document.querySelectorAll('.schedule-row').length"))
print('popup in DOM before =', ev("!!document.querySelector('.detail-popup')"))

ev("document.querySelector('.schedule-row').click(); 1")
time.sleep(1.5)
print('--- 点击卡片后 ---')
print('popup in DOM        =', ev("!!document.querySelector('.detail-popup')"))
print('popup style         =', ev(
    "(()=>{const p=document.querySelector('.detail-popup');if(!p)return null;"
    "const s=getComputedStyle(p);return JSON.stringify({display:s.display,vis:s.visibility,"
    "op:s.opacity,z:s.zIndex,pos:s.position});})()"))
print('overlay count       =', ev("document.querySelectorAll('.van-overlay').length"))
print('overlay style       =', ev(
    "(()=>{const o=document.querySelector('.van-overlay');if(!o)return null;"
    "const s=getComputedStyle(o);return JSON.stringify({display:s.display,vis:s.visibility,op:s.opacity});})()"))
print('body last children  =', ev(
    "[...document.body.children].map(c=>c.className||c.tagName).slice(-4).join(' | ')"))
print('popup parent        =', ev(
    "(()=>{const p=document.querySelector('.detail-popup');return p?(p.parentElement.className||p.parentElement.tagName):null})()"))

ev("document.querySelector('.dp-actions .van-button').click(); 1")
time.sleep(3.5)
print('--- 标记完成后 ---')
print('popup in DOM        =', ev("!!document.querySelector('.detail-popup')"))
print('popup style         =', ev(
    "(()=>{const p=document.querySelector('.detail-popup');if(!p)return 'REMOVED';"
    "const s=getComputedStyle(p);return JSON.stringify({display:s.display,vis:s.visibility,op:s.opacity});})()"))
print('overlay count       =', ev("document.querySelectorAll('.van-overlay').length"))
print('rows                =', ev("document.querySelectorAll('.schedule-row').length"))

proc.terminate()
