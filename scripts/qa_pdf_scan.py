# -*- coding: utf-8 -*-
"""扫描件 PDF 链路验证：
模拟前端行为 —— PDF 先栅格化成 JPEG 再上传，验证视觉识别真实生效。
同时确认服务端直收扫描件 PDF（旧路径）仍能优雅降级。
"""
import io
import json
import urllib.request
import urllib.error
import uuid

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


def http(method, url, token=None, data=None, headers=None, timeout=120):
    req = urllib.request.Request(url, method=method, data=data)
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    if token:
        req.add_header('X-Auth-Token', token)
        req.add_header('Authorization', f'Bearer {token}')
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode('utf-8'))
        except Exception:
            return {'success': False, 'message': f'HTTP {e.code}'}


def json_req(method, url, token, payload):
    return http(method, url, token, json.dumps(payload).encode('utf-8'),
                {'Content-Type': 'application/json'})


def make_scanned_product_jpeg():
    """用 PIL 画一张产品要素表并输出 JPEG —— 与前端 pdf.js 栅格化产物同性质"""
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new('RGB', (900, 620), 'white')
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 34)
    except Exception:
        font = ImageFont.truetype('C:/Windows/Fonts/simhei.ttf', 34)
    lines = [
        '贷款产品要素确认单',
        '产品名称：建行快易贷',
        '机构：中国建设银行',
        '年利率：3.4%-4.5%',
        '额度：1万-50万',
        '期限：6-36个月',
        '还款方式：先息后本',
        '准入：征信无当前逾期，近2月查询不超6次',
    ]
    y = 40
    for line in lines:
        d.text((50, y), line, fill='black', font=font)
        y += 70
    buf = io.BytesIO()
    img.save(buf, 'JPEG', quality=90)
    return buf.getvalue()


def make_scanned_income_png():
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new('RGB', (900, 620), 'white')
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 34)
    except Exception:
        font = ImageFont.truetype('C:/Windows/Fonts/simhei.ttf', 34)
    lines = [
        '收入证明',
        '兹证明 李小红 系我司正式员工，',
        '工作单位：苏州蓝湾信息技术有限公司',
        '月收入：人民币贰万叁仟元整（23000元）',
        '2026年9月5日',
    ]
    y = 40
    for line in lines:
        d.text((50, y), line, fill='black', font=font)
        y += 70
    buf = io.BytesIO()
    img.save(buf, 'PNG')
    return buf.getvalue()


def multipart(fields):
    """fields: list of (name, filename, content_type, bytes) 或 (name, text_value)"""
    boundary = uuid.uuid4().hex
    body = io.BytesIO()
    for f in fields:
        if len(f) == 2:
            body.write(f'--{boundary}\r\nContent-Disposition: form-data; name="{f[0]}"\r\n\r\n{f[1]}\r\n'.encode())
        else:
            name, fname, ctype, data = f
            body.write(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"; filename="{fname}"\r\nContent-Type: {ctype}\r\n\r\n'.encode())
            body.write(data)
            body.write(b'\r\n')
    body.write(f'--{boundary}--\r\n'.encode())
    return body.getvalue(), f'multipart/form-data; boundary={boundary}'


def main():
    # 登录
    r = json_req('POST', f'{API}/api/auth/login', None,
                 {'phone': '13800138000', 'password': 'abc123'})
    check('登录', r.get('success') is True)
    token = r['data']['token']

    print('== [1] 产品录入：图片型 JPEG（= 前端 PDF 栅格化产物）→ 视觉识别 ==')
    jpeg = make_scanned_product_jpeg()
    body, ctype = multipart([('file', 'kuaiyidai.jpg', 'image/jpeg', jpeg)])
    r = http('POST', f'{API}/api/ai/extract/product', token, body,
             {'Content-Type': ctype})
    d = (r.get('data') or {})
    fd = (d.get('data') or {}) if isinstance(d.get('data'), dict) else {}
    check('产品图片提取成功', r.get('success') is True, json.dumps(r, ensure_ascii=False)[:200])
    check('非演示数据（真实视觉识别）', d.get('demo') is not True, str(d.get('demo')))
    check('产品名称识别', '快易贷' in str(fd.get('productName', '')), str(fd.get('productName')))
    check('利率下限 3.4', abs(float(fd.get('minRate') or 0) - 3.4) < 0.01, str(fd.get('minRate')))
    check('利率上限 4.5', abs(float(fd.get('maxRate') or 0) - 4.5) < 0.01, str(fd.get('maxRate')))
    check('额度上限 50万', abs(float(fd.get('maxAmount') or 0) - 500000) < 1, str(fd.get('maxAmount')))

    print('== [2] 客户材料：收入证明 JPEG → 视觉 OCR ==')
    png = make_scanned_income_png()
    body, ctype = multipart([('file', 'shouru.png', 'image/png', png), ('type', 'income')])
    r = http('POST', f'{API}/api/ai/ocr/income', token, body, {'Content-Type': ctype})
    d2 = r.get('data') or {}
    check('材料识别成功', r.get('success') is True, json.dumps(r, ensure_ascii=False)[:200])
    check('非演示数据', d2.get('demo') is not True, str(d2.get('demo')))
    fields = str(d2.get('data', {}))
    check('姓名识别 李小红', '李小红' in fields, fields[:200])
    check('月收入识别 23000', '23000' in fields, fields[:200])

    print('== [3] 服务端直收扫描件 PDF（旧路径兜底）→ 优雅降级 ==')
    from PIL import Image
    img = Image.new('RGB', (400, 300), 'white')
    img.save(b := io.BytesIO(), 'PDF', resolution=100)
    pdf_bytes = b.getvalue()
    body, ctype = multipart([('file', 'scan.pdf', 'application/pdf', pdf_bytes)])
    r = http('POST', f'{API}/api/ai/extract/product', token, body, {'Content-Type': ctype})
    d3 = r.get('data') or {}
    check('返回成功且带演示标记', r.get('success') is True and d3.get('demo') is True,
          json.dumps(r, ensure_ascii=False)[:200])
    check('note 说明扫描件原因', '扫描件' in str(d3.get('note', '')), str(d3.get('note')))

    print(f'\n===== 结果：{PASSED} passed, {FAILED} failed =====')
    raise SystemExit(0 if FAILED == 0 else 1)


if __name__ == '__main__':
    main()
