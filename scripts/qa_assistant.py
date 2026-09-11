# -*- coding: utf-8 -*-
"""
AI 助理意图识别 + 实体提取 验证（DeepSeek 真实调用）

对齐目标：src/views/assistant/Index.vue 的 switch(intent) 分支与各 handler 的
实体字段消费逻辑（mock.js assistantReply 是 schema 参照）。
"""
import json
import sys
import time
import urllib.error
import urllib.request

API = 'http://127.0.0.1:3001'
OUT = []


def check(name, cond, detail=''):
    OUT.append((name, bool(cond), detail))
    print(('  [PASS] ' if cond else '  [FAIL] ') + name + (f' :: {detail}' if detail else ''))


def http(method, url, token=None, body=None, timeout=90):
    req = urllib.request.Request(url, data=json.dumps(body or {}).encode(), method=method)
    req.add_header('Content-Type', 'application/json')
    if token:
        req.add_header('X-Auth-Token', token)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode('utf-8'))
        except Exception:
            return {'success': False, 'message': f'HTTP {e.code}'}


def ask(token, text):
    r = http('POST', f'{API}/api/ai/assistant', token, {'text': text})
    d = (r.get('data') or {}) if isinstance(r.get('data'), dict) else {}
    return r, d.get('intent'), d.get('entities') or {}, d.get('reply') or ''


def is_iso(v):
    try:
        t = time.strptime(v[:19], '%Y-%m-%dT%H:%M:%S')
        return bool(t)
    except Exception:
        return False


def main():
    print('== 登录 ==')
    r = http('POST', f'{API}/api/auth/login', body={'phone': '13800138000', 'password': 'abc123'})
    token = r.get('data', {}).get('token')
    check('登录成功', bool(token))
    if not token:
        return 1

    print('== [1] 创建日程（核心场景） ==')
    r, intent, e, reply = ask(token, '明天下午3点与张总面谈')
    check('意图 = schedule_create', intent == 'schedule_create', intent)
    check('标题已解析', bool(e.get('title')), str(e.get('title')))
    check('startTime 是合法 ISO', is_iso(str(e.get('startTime', ''))), str(e.get('startTime')))
    check('endTime 是合法 ISO', is_iso(str(e.get('endTime', ''))), str(e.get('endTime')))
    check('客户名已提取', '张总' in str(e.get('customerName', '')), str(e.get('customerName')))

    print('== [2] 新建客户 ==')
    r, intent, e, reply = ask(token, '新增客户 王芳 13900139000')
    check('意图 = customer_create', intent == 'customer_create', intent)
    check('姓名 = 王芳', e.get('name') == '王芳', str(e.get('name')))
    check('手机号已提取', str(e.get('phone', '')).startswith('139'), str(e.get('phone')))

    print('== [3] 更新资料 ==')
    r, intent, e, reply = ask(token, '更新张志远的月收入为2万')
    check('意图 = customer_update', intent == 'customer_update', intent)
    check('field = monthlyIncome', e.get('field') == 'monthlyIncome', str(e.get('field')))
    check('fieldLabel 非空', bool(e.get('fieldLabel')), str(e.get('fieldLabel')))
    check('value 数值化为 20000（元）', e.get('value') == 20000 or e.get('value') == '20000', str(e.get('value')))
    check('客户名已提取', '张志远' in str(e.get('name', '')), str(e.get('name')))

    print('== [4] 录入产品 ==')
    r, intent, e, reply = ask(token, '录入产品 平安薪易贷 利率4%起 额度30万')
    check('意图 = product_create', intent == 'product_create', intent)
    check('产品名已提取', '薪易贷' in str(e.get('productName', '')), str(e.get('productName')))
    check('利率数值', float(e.get('minRate') or 0) == 4.0, str(e.get('minRate')))
    check('额度 30（万）', float(e.get('maxAmount') or 0) == 30.0, str(e.get('maxAmount')))

    print('== [5] 查询日程 ==')
    r, intent, e, reply = ask(token, '明天有什么日程')
    check('意图 = query_schedule', intent == 'query_schedule', intent)
    check('scope = tomorrow', e.get('scope') == 'tomorrow', str(e.get('scope')))

    print('== [6] 查客户档案 ==')
    r, intent, e, reply = ask(token, '查张志远的档案')
    check('意图 = query_customer', intent == 'query_customer', intent)
    check('客户名已提取', '张志远' in str(e.get('name', '')), str(e.get('name')))

    print('== [7] 查产品库 ==')
    r, intent, e, reply = ask(token, '有哪些产品')
    check('意图 = query_product', intent == 'query_product', intent)

    print('== [8] 匹配产品 ==')
    r, intent, e, reply = ask(token, '帮张志远匹配合适的产品')
    check('意图 = query_match', intent == 'query_match', intent)
    check('客户名已提取', '张志远' in str(e.get('name', '')), str(e.get('name')))

    print('== [9] 兜底问答 ==')
    r, intent, e, reply = ask(token, '今天上海天气怎么样')
    check('意图 = unknown（走兜底）', intent in ('unknown', 'qa'), intent)
    check('reply 非空', bool(reply.strip()), reply[:60])

    passed = sum(1 for _, ok, _ in OUT if ok)
    print(f'\n==== {passed}/{len(OUT)} 通过 ====')
    for n, ok, _d in OUT:
        if not ok:
            print(f'  失败: {n}')
    return 0 if passed == len(OUT) else 1


if __name__ == '__main__':
    sys.exit(main())
