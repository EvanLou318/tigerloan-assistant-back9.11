# -*- coding: utf-8 -*-
"""后台三类 AI 服务配置功能 API 层全量检查（只读 + 可还原的写操作）"""
import json, urllib.request

BASE = 'http://127.0.0.1:3001'
urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))

P = F = 0
def check(name, cond, extra=''):
    global P, F
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + extra) if extra else ''))
    P += bool(cond); F += (not cond)

def req(url, data=None, tok=None, method=None):
    h = {'Content-Type': 'application/json'}
    if tok: h['X-Auth-Token'] = tok
    r = urllib.request.Request(BASE + url, json.dumps(data).encode() if data is not None else None, h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try: return e.code, json.loads(e.read())
        except Exception: return e.code, {}

s, b = req('/api/auth/login', {'phone': '13800138000', 'password': 'abc123'})
tok = b['data']['token']
check('登录', s == 200)

# ---- 1. 列表与回显 ----
s, b = req('/api/services', tok=tok)
groups = b['data']['groups'] if isinstance(b['data'], dict) and 'groups' in b['data'] else b['data']
gmap = {}
for g in groups:
    gmap[g['category']] = g
check('三个分类齐全(llm/ocr/asr)', set(gmap) == {'llm', 'ocr', 'asr'})

llm = gmap['llm']['providers']
asr = gmap['asr']['providers']
deep = next((p for p in llm if p.get('isDefault')), None)
ali = next((p for p in asr if p.get('isDefault')), None)
check('LLM 有默认供应商(DeepSeek)', deep and 'DeepSeek' in deep['name'])
check('LLM 关键字段回显', deep and deep.get('model') == 'deepseek-chat' and deep.get('visionModel') == 'deepseek-v4-flash-vision-exp', f"model={deep.get('model') if deep else None}")
check('LLM key 掩码不泄明文', deep and deep.get('apiKeyMasked') and 'sk-d41cd29d' not in json.dumps(deep), deep.get('apiKeyMasked') if deep else '')
check('ASR 有默认供应商(阿里云)', ali and 'aliyun' in str(ali.get('providerType')))
check('ASR 双掩码回显', ali and ali.get('apiKeyMasked') and ali.get('appKeyMasked'), f"{ali.get('apiKeyMasked') if ali else ''} / {ali.get('appKeyMasked') if ali else ''}")
check('OCR 分类无供应商(走LLM Vision设计)', len(gmap['ocr']['providers']) == 0)

# ---- 2. 测试连通（实际路由为 POST /:id/test，前端 Services.vue「测试连通」同款） ----
for pid, name in [(deep['id'], 'LLM/DeepSeek'), (ali['id'], 'ASR/阿里云')]:
    s, b = req('/api/services/%d/test' % pid, {}, tok=tok, method='POST')
    d = b.get('data', {}) if isinstance(b.get('data'), dict) else {}
    check(f'test[{name}] 接口可达且返回结论', s == 200 and 'pass' in d, f"pass={d.get('pass')} msg={str(d.get('message'))[:80]}")

s, b = req('/api/services/999/test', {}, tok=tok, method='POST')
check('test 不存在供应商返回明确错误', s in (404, 400), str(s))

# ---- 3. 编辑保存：掩码保持、字段合并 ----
# 记录原值，PUT 只改 remark，验证 key/appkey/visionModel 不丢
orig = {k: deep[k] for k in ('name', 'model', 'visionModel', 'baseUrl', 'remark', 'enabled')}
s, b = req('/api/services/%d' % deep['id'], {'name': deep['name'], 'providerType': deep['providerType'],
          'baseUrl': deep['baseUrl'], 'model': deep['model'], 'visionModel': deep.get('visionModel', ''),
          'remark': (deep.get('remark') or '') + '', 'enabled': deep['enabled'], 'isDefault': True}, tok=tok, method='PUT')
check('PUT(不带key) 保存成功', s == 200, str(s))

s, b = req('/api/services', tok=tok)
groups = b['data']['groups'] if isinstance(b['data'], dict) and 'groups' in b['data'] else b['data']
deep2 = next(p for g in groups if g['category'] == 'llm' for p in g['providers'] if p['id'] == deep['id'])
check('PUT 后 model/visionModel 保持', deep2.get('model') == 'deepseek-chat' and deep2.get('visionModel') == 'deepseek-v4-flash-vision-exp')
check('PUT 不带 key 后掩码仍在(未清空)', bool(deep2.get('apiKeyMasked')), deep2.get('apiKeyMasked'))

# ---- 4. 新建 + 删除临时供应商（OCR 分类验证建/删闭环）----
s, b = req('/api/services', {'category': 'ocr', 'name': '__qa临时OCR__', 'providerType': 'custom',
          'baseUrl': 'https://example.invalid', 'apiKey': 'sk-test-1234567890', 'enabled': False}, tok=tok, method='POST')
check('POST 新建供应商', s in (200, 201), str(s))
new_id = b['data']['id'] if s in (200, 201) and isinstance(b.get('data'), dict) else None

if new_id:
    s, b = req('/api/services', tok=tok)
    groups = b['data']['groups'] if isinstance(b['data'], dict) and 'groups' in b['data'] else b['data']
    ocrp = next((p for g in groups if g['category'] == 'ocr' for p in g['providers'] if p['id'] == new_id), None)
    check('新建供应商已出现在 OCR 分类', bool(ocrp))
    check('新建供应商 key 已掩码存储', ocrp and ocrp.get('apiKeyMasked') and 'sk-test-1234567890' not in json.dumps(ocrp))
    s, b = req('/api/services/%d/test' % new_id, {}, tok=tok, method='POST')
    d = b.get('data', {})
    # 设计行为：custom OCR 未接 SDK，test 仅校验配置存在，并明确提示"识别会以演示数据代替"
    check('test[custom OCR] 返回配置确认与未接入提示', s == 200 and d.get('pass') is True and '演示数据' in str(d.get('message')), f"msg={str(d.get('message'))[:60]}")
    s, b = req('/api/services/%d' % new_id, tok=tok, method='DELETE')
    check('DELETE 清理临时供应商', s in (200, 204), str(s))
    s, b = req('/api/services', tok=tok)
    groups = b['data']['groups'] if isinstance(b['data'], dict) and 'groups' in b['data'] else b['data']
    still = any(p['id'] == new_id for g in groups for p in g['providers'])
    check('删除后列表已无该供应商', not still)
else:
    F += 1
    print('FAIL POST 未返回 id，无法继续建删闭环')

# ---- 5. 业务链路抽查：真实 LLM 意图接口（依赖 llm 配置，入参字段为 text）----
s, b = req('/api/ai/assistant', {'text': '明天下午3点提醒我给张三打电话'}, tok=tok)
d = b.get('data', {})
demo = d.get('demo', False)
intent = d.get('intent') or d.get('action')
check('AI助理链路走真实LLM(非demo)', s == 200 and not demo, f"intent={intent} demo={demo}")

# ASR 无有效内容时应返回明确中文错误（上游 40000001 参数有误归一为 500+可读信息，临时文件已回收）
boundary = '----qaboundary917'
wav = b'RIFF' + (36).to_bytes(4, 'little') + b'WAVEfmt ' + (16).to_bytes(4, 'little') + (1).to_bytes(2, 'little') + (1).to_bytes(2, 'little') + (16000).to_bytes(4, 'little') + (32000).to_bytes(4, 'little') + (2).to_bytes(2, 'little') + (16).to_bytes(2, 'little') + b'data' + (0).to_bytes(4, 'little')
body = (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="t.wav"\r\nContent-Type: audio/wav\r\n\r\n').encode() + wav + f'\r\n--{boundary}--\r\n'.encode()
h = {'Content-Type': f'multipart/form-data; boundary={boundary}', 'X-Auth-Token': tok}
r = urllib.request.Request(BASE + '/api/ai/asr', body, h, method='POST')
try:
    with urllib.request.urlopen(r, timeout=30) as resp:
        s, jb = resp.status, json.loads(resp.read())
except urllib.error.HTTPError as e:
    s = e.code
    try: jb = json.loads(e.read())
    except Exception: jb = {}
msg = str(jb.get('message') or jb.get('data', {}).get('message') or jb)
check('ASR 无效音频返回可读中文错误(非堆栈崩溃)',
      msg.startswith('阿里云') and ('ASR 识别失败' in msg or 'AccessToken 已失效' in msg) and 'at ' not in msg[:30],
      f"http={s} msg={msg[:70]}")

print(f"\n{P} passed, {F} failed")
raise SystemExit(1 if F else 0)
