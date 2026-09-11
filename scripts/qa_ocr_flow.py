# -*- coding: utf-8 -*-
"""
材料 OCR / 产品图片识别回归（视觉 LLM 版）：
- 材料 OCR（png）走 DeepSeek Vision 真实识别，非演示数据
- 不支持格式（bmp）优雅降级演示数据并说明原因
- 产品图片录入走视觉真实提取
"""
import io
import json
import os
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
    boundary = '----qaboundary789'
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
    from PIL import Image
    _, login = http('POST', f'{API}/auth/login', data={'phone': '13800138000', 'password': 'abc123'})
    token = login['data']['token']
    check('登录', bool(token))

    income_png = open(DIR + r'\_vision_income.png', 'rb').read()
    product_png = open(DIR + r'\_vision_product.png', 'rb').read()

    # ---------- 1) 材料 OCR：视觉真实识别（收入证明） ----------
    st, r1 = upload('/ai/ocr/income', token, 'income.png', income_png, 'image/png')
    d1 = r1.get('data', {})
    check('材料OCR 200', st == 200, f'st={st} {str(r1)[:150]}')
    check('材料OCR 真实视觉识别', d1.get('demo') is None and 'Vision' in str(d1.get('source', '')), str(d1)[:150])
    check('材料OCR 月收入 15800', int((d1.get('data') or {}).get('monthlyIncome') or 0) == 15800, (d1.get('data') or {}).get('monthlyIncome'))
    check('材料OCR 存档路径返回', str((r1.get('data') or {}).get('filePath', r1.get('filePath', '')) or d1.get('filePath', '')), '')

    # ---------- 2) 不支持格式：优雅降级 ----------
    bmp_path = DIR + r'\_t.bmp'
    Image.open(DIR + r'\_vision_income.png').save(bmp_path)
    st, r2 = upload('/ai/ocr/income', token, 'income.bmp', open(bmp_path, 'rb').read(), 'image/bmp')
    d2 = r2.get('data', {})
    check('bmp 200 且降级演示', st == 200 and d2.get('demo') is True, f'st={st} {str(r2)[:150]}')
    check('bmp note 说明原因', '视觉识别失败' in str(d2.get('note', '')), d2.get('note', ''))
    os.remove(bmp_path)

    # ---------- 3) 产品图片录入：视觉真实提取 ----------
    st, r3 = upload('/ai/extract/product', token, 'product.png', product_png, 'image/png', {'text': ''})
    d3 = r3.get('data', {})
    check('产品图片 200', st == 200, f'st={st} {str(r3)[:150]}')
    check('产品图片 真实视觉识别', d3.get('demo') is None and 'Vision' in str(d3.get('source', '')), str(d3)[:150])
    vd = d3.get('data', {})
    check('产品图片 提取到产品名', '公积金信用贷' in str(vd.get('productName', '')), vd.get('productName', ''))
    check('产品图片 利率 3.2-4.8', abs(float(vd.get('minRate') or 0) - 3.2) < 0.01 and abs(float(vd.get('maxRate') or 0) - 4.8) < 0.01, f"{vd.get('minRate')}-{vd.get('maxRate')}")
    check('产品图片 额度上限 80万', abs(float(vd.get('maxAmount') or 0) - 800000) < 1, vd.get('maxAmount'))

    failed = [n for n, okk, _ in results if not okk]
    print(f'\n===== {len(results) - len(failed)}/{len(results)} passed =====')
    if failed:
        print('FAILED:', failed)
        sys.exit(1)


if __name__ == '__main__':
    main()
