# -*- coding: utf-8 -*-
"""
产品录入 AI 提取 + 匹配引擎 + AI 助理 真实链路验证（DeepSeek）

覆盖：
  1. 文本 → /api/ai/extract/product → DeepSeek 真实提取产品要素
  2. PDF 附件（手工构造、含文本层）→ multipart 上传 → 本地抽文本 + DeepSeek
  3. 图片附件 → 无 OCR 能力 → 应降级演示数据并带 demo/note 标记（而不是幻觉输出）
  4. /api/ai/match → DeepSeek 匹配引擎，approved/rejected 结构完整
  5. /api/ai/assistant → 意图识别
"""
import json
import struct
import sys
import time
import urllib.error
import urllib.request
import zlib

API = 'http://127.0.0.1:3001'
OUT = []


def check(name, cond, detail=''):
    OUT.append((name, bool(cond), detail))
    print(('  [PASS] ' if cond else '  [FAIL] ') + name + (f' :: {detail}' if detail else ''))


def http(method, url, token=None, body=None, form=None, timeout=90):
    if form:
        boundary = '----QAPDF' + str(int(time.time() * 1000))
        data = bytearray()
        for key, val in form:
            if isinstance(val, tuple):  # (filename, content_type, bytes)
                fn, ctype, content = val
                data += f'--{boundary}\r\n'.encode()
                data += f'Content-Disposition: form-data; name="{key}"; filename="{fn}"\r\n'.encode()
                data += f'Content-Type: {ctype}\r\n\r\n'.encode()
                data += content + b'\r\n'
            else:
                data += f'--{boundary}\r\n'.encode()
                data += f'Content-Disposition: form-data; name="{key}"\r\n\r\n{val}\r\n'.encode()
        data += f'--{boundary}--\r\n'.encode()
        req = urllib.request.Request(url, data=bytes(data), method='POST')
        req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
    else:
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


def make_pdf(lines):
    """手工构造一个含文本层的最小 PDF（内容流不压缩，方便本地抽取器验证）"""
    ops = ['BT', '/F1 12 Tf', '72 720 Td']
    for i, line in enumerate(lines):
        esc = line.replace('\\', r'\\').replace('(', r'\(').replace(')', r'\)')
        ops.append(f'({esc}) Tj')
        if i < len(lines) - 1:
            ops.append('0 -20 Td')
    ops.append('ET')
    content = '\n'.join(ops).encode('utf-8')
    objs = [
        b'<< /Type /Catalog /Pages 2 0 R >>',
        b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
        b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>',
        b'<< /Length ' + str(len(content)).encode() + b' >>\nstream\n' + content + b'\nendstream',
    ]
    out = b'%PDF-1.4\n'
    for i, o in enumerate(objs, 1):
        out += f'{i} 0 obj\n'.encode() + o + b'\nendobj\n'
    out += b'trailer << /Root 1 0 R /Size 5 >>\n%%EOF\n'
    return out


def make_png():
    """1x1 红色 PNG"""
    def chunk(typ, data):
        c = struct.pack('>I', len(data)) + typ + data
        return c + struct.pack('>I', zlib.crc32(typ + data) & 0xFFFFFFFF)
    ihdr = struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)
    idat = zlib.compress(b'\x00\xff\x00\x00')
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr)
            + chunk(b'IDAT', idat) + chunk(b'IEND', b''))


def main():
    print('== 登录 ==')
    r = http('POST', f'{API}/api/auth/login', body={'phone': '13800138000', 'password': 'abc123'})
    token = r.get('data', {}).get('token')
    check('登录成功', bool(token))
    if not token:
        return 1

    print('== [1] 文本 → DeepSeek 提取产品要素 ==')
    text = ('产品名称：招行公积金信用贷。机构：招商银行。年利率3.2%-4.8%，'
            '额度5万-80万元，期限12-60个月，等额本息或先息后本。'
            '准入：公积金连续缴存满12个月，月缴存基数不低于4000元，征信无当前逾期，近3个月查询不超过6次。')
    r = http('POST', f'{API}/api/ai/extract/product', token, {'text': text})
    d = (r.get('data') or {}) if isinstance(r.get('data'), dict) else {}
    data = d.get('data') or {}
    check('接口成功且非演示数据', r.get('success') is True and not d.get('demo'), json.dumps(r, ensure_ascii=False)[:200])
    check('提取到产品名称', '公积金' in str(data.get('productName', '')), str(data.get('productName')))
    check('提取到机构', '招商' in str(data.get('institution', '')), str(data.get('institution')))
    check('提取到利率区间', bool(data.get('minRate') and data.get('maxRate')), f"{data.get('minRate')}-{data.get('maxRate')}")
    check('准入条件非空', bool(str(data.get('conditions', '')).strip()), str(data.get('conditions'))[:60])

    print('== [2] PDF 附件 → 本地抽文本 + DeepSeek ==')
    pdf = make_pdf([
        '产品名称：建行公积金装修贷',
        '贷款机构：中国建设银行',
        '年利率：3.45%-5.60%',
        '额度：5万-50万元 期限：6-60个月',
        '还款方式：等额本息/先息后本',
        '准入条件：公积金连续缴存12个月以上，基数3000元以上，征信无当前逾期',
    ])
    r = http('POST', f'{API}/api/ai/extract/product', token,
             form=[('file', ('product.pdf', 'application/pdf', pdf))])
    d = (r.get('data') or {}) if isinstance(r.get('data'), dict) else {}
    data = d.get('data') or {}
    check('接口成功且非演示数据', r.get('success') is True and not d.get('demo'), json.dumps(r, ensure_ascii=False)[:200])
    check('来源标注为 PDF+LLM', 'PDF' in str(d.get('source', '')), str(d.get('source')))
    check('提取到产品名称', '公积金' in str(data.get('productName', '')) or '装修' in str(data.get('productName', '')), str(data.get('productName')))
    check('提取到机构', '建设' in str(data.get('institution', '')) or '建行' in str(data.get('institution', '')), str(data.get('institution')))
    check('提取到利率', bool(data.get('minRate') and data.get('maxRate')), f"{data.get('minRate')}-{data.get('maxRate')}")

    print('== [3] 图片附件 → 视觉模型识别 ==')
    r = http('POST', f'{API}/api/ai/extract/product', token,
             form=[('file', ('poster.png', 'image/png', make_png()))])
    d = (r.get('data') or {}) if isinstance(r.get('data'), dict) else {}
    check('接口成功（视觉链路）', r.get('success') is True, json.dumps(r, ensure_ascii=False)[:160])
    check('走 DeepSeek Vision 且非演示', 'Vision' in str(d.get('source', '')) and not d.get('demo'), str(d.get('source')))

    print('== [4] 匹配引擎（DeepSeek） ==')
    customer = {
        'name': '测试客户', 'city': '上海', 'monthlyIncome': 15000,
        'housingFundBase': 5000, 'creditOverdue': False, 'queryCount3m': 2,
        'expectedAmount': 300000,
    }
    products = [{
        'id': 'p1', 'productName': '公积金信用贷', 'institution': '招商银行',
        'status': 'active', 'minRate': 3.2, 'maxRate': 4.8, 'maxAmount': 800000,
        'loanTerm': '12-60个月', 'conditions': '公积金连续缴存满12个月；月缴存基数不低于4000元；征信无当前逾期',
    }, {
        'id': 'p2', 'productName': '房抵经营贷', 'institution': '某银行',
        'status': 'active', 'minRate': 3.85, 'maxRate': 5.2, 'maxAmount': 5000000,
        'loanTerm': '36-120个月', 'conditions': '名下有房且已取得产权证；经营满2年',
    }]
    r = http('POST', f'{API}/api/ai/match', token, {'customer': customer, 'products': products})
    d = (r.get('data') or {}) if isinstance(r.get('data'), dict) else {}
    approved = d.get('approved') or []
    rejected = d.get('rejected') or []
    check('匹配成功且有分组', r.get('success') is True and approved and rejected,
          f"approved={len(approved)} rejected={len(rejected)}")
    if approved:
        check('公积金贷获批且带理由', approved[0].get('productName') == '公积金信用贷' and bool(approved[0].get('reasons')),
              json.dumps(approved[0], ensure_ascii=False)[:120])
    if rejected:
        check('房抵贷被拒且带未满足条件', rejected[0].get('productName') == '房抵经营贷' and bool(rejected[0].get('failedConditions')),
              json.dumps(rejected[0], ensure_ascii=False)[:160])

    print('== [5] AI 助理意图识别 ==')
    r = http('POST', f'{API}/api/ai/assistant', token, {'text': '明天下午三点提醒我给张总打电话'})
    d = (r.get('data') or {}) if isinstance(r.get('data'), dict) else {}
    check('助理返回意图', r.get('success') is True and bool(d.get('intent')), str(d.get('intent')))
    check('识别为创建日程', d.get('intent') == 'schedule_create', str(d.get('intent')))
    check('带实体', bool(d.get('entities')), json.dumps(d.get('entities'), ensure_ascii=False)[:120])

    passed = sum(1 for _, ok, _ in OUT if ok)
    print(f'\n==== {passed}/{len(OUT)} 通过 ====')
    for n, ok, _d in OUT:
        if not ok:
            print(f'  失败: {n}')
    return 0 if passed == len(OUT) else 1


if __name__ == '__main__':
    sys.exit(main())
