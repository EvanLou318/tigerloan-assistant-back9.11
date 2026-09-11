# -*- coding: utf-8 -*-
"""
DeepSeek 视觉 OCR 端到端回归：
1. 产品图片录入 → 视觉模型真实提取（非 demo，字段值与图片内容一致）
2. 客户材料 OCR（收入证明）→ 视觉模型真实识别
3. 不支持格式（bmp）→ 优雅降级演示数据
"""
import io
import json
import sys
import urllib.request

BASE = 'http://127.0.0.1:3001'
API = BASE + '/api'
DIR = r'C:\Users\madta\WorkBuddy\2026-08-19-12-24-26\loan-assistant\scripts'

results = []


def check(name, cond, detail=''):
    results.append((name, bool(cond), detail))
    print(('PASS' if cond else 'FAIL') + f' | {name}' + (f' | {detail}' if detail and not cond else ''))


def http(method, url, token=None, data=None, raw=None, content_type='application/json'):
    req = urllib.request.Request(url, method=method)
    if token:
        req.add_header('X-Auth-Token', token)
    body = None
    if raw is not None:
        body = raw
        req.add_header('Content-Type', content_type)
    elif data is not None:
        body = json.dumps(data).encode('utf-8')
        req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, body, timeout=120) as resp:
            return resp.status, json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode('utf-8'))
        except Exception:
            return e.code, {}


def multipart(fields, files):
    boundary = '----qaboundary456'
    buf = io.BytesIO()
    for k, v in fields.items():
        buf.write(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
    for k, (fname, blob, ctype) in files.items():
        buf.write(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"; filename="{fname}"\r\n'
            f'Content-Type: {ctype}\r\n\r\n'.encode()
        )
        buf.write(blob)
        buf.write(b'\r\n')
    buf.write(f'--{boundary}--\r\n'.encode())
    return buf.getvalue(), f'multipart/form-data; boundary={boundary}'


def upload(url_path, token, fname, blob, ctype, extra=None):
    body, ct = multipart(extra or {}, {'file': (fname, blob, ctype)})
    return http('POST', f'{API}{url_path}', token, raw=body, content_type=ct)


def main():
    _, login = http('POST', f'{API}/auth/login', data={'phone': '13800138000', 'password': 'abc123'})
    token = login['data']['token']
    check('登录', bool(token))

    product_png = open(DIR + r'\_vision_product.png', 'rb').read()
    income_png = open(DIR + r'\_vision_income.png', 'rb').read()

    # ---------- 1) 产品图片录入：视觉真实提取 ----------
    st, r1 = upload('/ai/extract/product', token, 'product.png', product_png, 'image/png', {'text': ''})
    d1 = r1.get('data', {})
    check('产品图片 200', st == 200, f'st={st} {str(r1)[:200]}')
    check('产品图片 非演示数据', d1.get('success') and d1.get('demo') is None, str(d1)[:150])
    check('产品图片 走视觉模型', 'Vision' in str(d1.get('source', '')), d1.get('source', ''))
    vd = d1.get('data', {})
    check('产品图片 提取到产品名', '公积金信用贷' in str(vd.get('productName', '')), vd.get('productName', ''))
    check('产品图片 提取到机构', '招商银行' in str(vd.get('institution', '')), vd.get('institution', ''))
    check('产品图片 利率下限 3.2', abs(float(vd.get('minRate') or 0) - 3.2) < 0.01, vd.get('minRate'))
    check('产品图片 利率上限 4.8', abs(float(vd.get('maxRate') or 0) - 4.8) < 0.01, vd.get('maxRate'))
    check('产品图片 额度上限 80万', abs(float(vd.get('maxAmount') or 0) - 800000) < 1, vd.get('maxAmount'))

    # ---------- 2) 材料 OCR（收入证明）：视觉真实识别 ----------
    st, r2 = upload('/ai/ocr/income', token, 'income.png', income_png, 'image/png')
    d2 = r2.get('data', {})
    check('收入证明 200', st == 200, f'st={st} {str(r2)[:200]}')
    check('收入证明 非演示数据', d2.get('success') and d2.get('demo') is None, str(d2)[:150])
    check('收入证明 走视觉模型', 'Vision' in str(d2.get('source', '')), d2.get('source', ''))
    od = d2.get('data', {})
    check('收入证明 提取到单位', '星辰科技' in str(od.get('employer', '')), od.get('employer', ''))
    check('收入证明 月收入 15800', int(od.get('monthlyIncome') or 0) == 15800, od.get('monthlyIncome'))
    check('收入证明 存档路径返回', str(r2.get('data', {}).get('filePath', r2.get('filePath', ''))) or str(d2.get('filePath', '')), '')

    # ---------- 3) 不支持格式：优雅降级 ----------
    from PIL import Image
    import os
    bmp_path = DIR + r'\_vision_test.bmp'
    Image.open(DIR + r'\_vision_income.png').save(bmp_path)
    st, r3 = upload('/ai/ocr/income', token, 'income.bmp', open(bmp_path, 'rb').read(), 'image/bmp')
    d3 = r3.get('data', {})
    check('bmp 上传 200', st == 200, f'st={st} {str(r3)[:150]}')
    check('bmp 降级演示数据', d3.get('demo') is True, str(d3)[:150])
    check('bmp note 说明原因', '视觉识别失败' in str(d3.get('note', '')), d3.get('note', ''))
    os.remove(bmp_path)

    failed = [n for n, okk, _ in results if not okk]
    print(f'\n===== {len(results) - len(failed)}/{len(results)} passed =====')
    if failed:
        print('FAILED:', failed)
        sys.exit(1)


if __name__ == '__main__':
    main()
