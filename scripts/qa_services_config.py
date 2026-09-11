# -*- coding: utf-8 -*-
"""三方服务配置管理回归：预设字段(visionModel)持久化、编辑合并语义、
连通性测试、ASR 必填校验、默认供应商不受影响。
"""
import json
import urllib.request
import urllib.error

API = 'http://127.0.0.1:3001'
PASSED = 0
FAILED = 0


def check(name, cond, detail=''):
    global PASSED, FAILED
    tag = 'PASS' if cond else 'FAIL'
    print(f'[{tag}] {name}' + (f'  | {detail}' if detail and not cond else ''))
    if cond:
        PASSED += 1
    else:
        FAILED += 1


def http(method, path, token=None, payload=None):
    req = urllib.request.Request(f'{API}{path}', method=method)
    if token:
        req.add_header('X-Auth-Token', token)
        req.add_header('Authorization', f'Bearer {token}')
    data = None
    if payload is not None:
        data = json.dumps(payload).encode('utf-8')
        req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, data, timeout=60) as r:
            return json.loads(r.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode('utf-8'))
        except Exception:
            return {'success': False, 'message': f'HTTP {e.code}'}


def find_provider(groups, pid):
    for g in groups:
        for p in g.get('providers', []):
            if p['id'] == pid:
                return p
    return None


def main():
    r = http('POST', '/api/auth/login', payload={'phone': '13800138000', 'password': 'abc123'})
    check('登录', r.get('success') is True)
    token = r['data']['token']

    # 现有默认 LLM（DeepSeek）补充 visionModel 显式值（与内置默认一致，保证后台可见）
    groups = http('GET', '/api/services', token)['data']
    llm_default = next((p for g in groups if g['category'] == 'llm' for p in g['providers'] if p['isDefault']), None)
    check('存在默认 LLM 供应商', llm_default is not None)
    if llm_default:
        http('PUT', f"/api/services/{llm_default['id']}", token,
             {'visionModel': 'deepseek-v4-flash-vision-exp'})

    print('== [1] 创建临时 LLM 供应商（DeepSeek 预设参数 + visionModel） ==')
    r = http('POST', '/api/services', token, {
        'category': 'llm', 'name': 'QA临时-DeepSeek预设', 'providerType': 'openai-compatible',
        'baseUrl': 'https://api.deepseek.com/v1', 'apiKey': 'sk-qa-dummy-key',
        'model': 'deepseek-chat', 'visionModel': 'test-vision-model',
        'enabled': True, 'isDefault': False, 'remark': 'QA 自动创建',
    })
    check('创建成功', r.get('success') is True, str(r)[:150])
    temp_id = r.get('data', {}).get('id')

    groups = http('GET', '/api/services', token)['data']
    temp = find_provider(groups, temp_id)
    check('visionModel 已持久化', temp and temp.get('visionModel') == 'test-vision-model',
          str(temp and temp.get('visionModel')))
    check('model/baseUrl 正确', temp and temp.get('model') == 'deepseek-chat'
          and temp.get('baseUrl') == 'https://api.deepseek.com/v1')
    check('默认供应商未被顶替', llm_default and find_provider(groups, llm_default['id'])['isDefault'] is True)

    print('== [2] 编辑：visionModel 清空再回填（合并语义） ==')
    http('PUT', f'/api/services/{temp_id}', token, {'visionModel': ''})
    groups = http('GET', '/api/services', token)['data']
    check('visionModel 可清空', find_provider(groups, temp_id).get('visionModel') == '')
    http('PUT', f'/api/services/{temp_id}', token, {'visionModel': 'deepseek-v4-flash-vision-exp'})
    groups = http('GET', '/api/services', token)['data']
    check('visionModel 可回填', find_provider(groups, temp_id).get('visionModel') == 'deepseek-v4-flash-vision-exp')

    print('== [3] 连通性测试端点（哑 key 应返回结构化失败而非 500） ==')
    r = http('POST', f'/api/services/{temp_id}/test', token)
    check('测试端点返回结构化结果', r.get('success') is True and isinstance(r.get('data', {}).get('pass'), bool),
          str(r)[:200])
    check('哑 key 测试不通过（pass=false）', r.get('data', {}).get('pass') is False, r.get('data', {}).get('message', ''))

    print('== [4] ASR 阿里云必填校验 ==')
    r = http('POST', '/api/services', token, {
        'category': 'asr', 'name': 'QA临时-阿里云ASR', 'providerType': 'aliyun', 'apiKey': 'dummy-token',
        'enabled': True,
    })
    check('缺 AppKey 被拦截', r.get('success') is False and 'AppKey' in str(r.get('message', '')), str(r)[:150])

    print('== [5] 清理临时供应商 ==')
    r = http('DELETE', f'/api/services/{temp_id}', token)
    check('删除成功', r.get('success') is True)
    groups = http('GET', '/api/services', token)['data']
    check('列表中已不存在', find_provider(groups, temp_id) is None)
    llm_group = next((g for g in groups if g['category'] == 'llm'), None)
    check('默认 LLM 仍在且模式 real', llm_group and llm_group['mode'] == 'real'
          and find_provider(groups, llm_default['id'])['isDefault'] is True)

    print(f'\n===== 结果：{PASSED} passed, {FAILED} failed =====')
    raise SystemExit(0 if FAILED == 0 else 1)


if __name__ == '__main__':
    main()
