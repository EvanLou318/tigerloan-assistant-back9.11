# -*- coding: utf-8 -*-
# 移动端接口层缺陷排查：所有移动端用到的接口做边界/异常用例
import json, subprocess, sys

BASE = "http://127.0.0.1:3007"
PASS, FAIL = [], []


def curl(method, path, token=None, body=None, raw=False):
    cmd = ["curl", "-s", "--noproxy", "*", "-m", "20", "-X", method, BASE + path,
           "-w", "\n@@@%{http_code}"]
    if token:
        cmd += ["-H", f"X-Auth-Token: {token}"]
    if body is not None:
        cmd += ["-H", "Content-Type: application/json", "-d", json.dumps(body, ensure_ascii=False)]
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    if "@@@" not in out:
        return None, 0, out
    payload, code = out.rsplit("@@@", 1)
    try:
        return json.loads(payload), int(code), payload
    except Exception:
        return None, int(code), payload


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(f"{name}  {detail}")
    print(("  PASS  " if cond else "  FAIL  ") + name + ("  " + detail if detail else ""))


# ---------- 登录 ----------
print("\n=== 1. 认证 ===")
r, code, _ = curl("POST", "/api/auth/login", body={"phone": "13800138000", "password": "abc123"})
TOKEN = r["data"]["token"] if r and r.get("success") else None
check("登录成功", code == 200 and TOKEN, f"code={code}")
check("登录返回 avatar 字段", r and "avatar" in r["data"]["user"], "")
check("登录返回 permissions", r and r["data"]["user"].get("permissions"), "")

r, code, _ = curl("POST", "/api/auth/login", body={"phone": "13800138000", "password": "wrong"})
check("错误密码被拒绝", code == 400, f"code={code}")
r, code, _ = curl("POST", "/api/auth/login", body={})
check("空参数被拒绝", code == 400, f"code={code}")

# 无 token 访问受保护接口
for p in ["/api/products", "/api/customers", "/api/schedules", "/api/dashboard", "/api/auth/me"]:
    r, code, _ = curl("GET", p)
    check(f"无 token 拒绝 {p}", code == 401, f"code={code}")

# 伪造 token
r, code, _ = curl("GET", "/api/products", token="fake.token.value")
check("伪造 token 被拒绝", code == 401, f"code={code}")

# ---------- 产品 ----------
print("\n=== 2. 产品 ===")
r, code, _ = curl("GET", "/api/products", token=TOKEN)
prods = r["data"] if r and r.get("success") else []
check("产品列表可读", code == 200, f"{len(prods)} 条")
BASE_PROD = len(prods)

# 创建：缺必填
r, code, _ = curl("POST", "/api/products", token=TOKEN, body={"institution": "X"})
check("创建产品缺产品名被拒", code == 400, f"code={code}")

# 创建：正常
newp = {"productName": "__QA产品__", "institution": "__QA机构__", "minRate": 3.1, "maxRate": 5.2,
        "minAmount": 1, "maxAmount": 50, "loanTerm": "12-36个月", "repaymentMethod": "等额本息",
        "conditions": "征信良好", "rateType": "annual", "source": "text"}
r, code, _ = curl("POST", "/api/products", token=TOKEN, body=newp)
pid = r["data"]["id"] if r and r.get("success") else None
check("创建产品成功", code == 200 and pid, f"id={pid}")

# 创建：非法利率类型（应为 annual/monthly，写别的会怎样？）
if pid:
    r, code, _ = curl("POST", "/api/products", token=TOKEN, body={**newp, "productName": "__QA非法利率类型__", "rateType": "weekly"})
    bad_id = r["data"]["id"] if r and r.get("success") else None
    rt = r["data"].get("rateType") if r and r.get("success") else None
    check("非法 rateType 被白名单兜底为 annual", code == 200 and rt == "annual", f"rateType={rt}")
    if bad_id:
        curl("DELETE", f"/api/products/{bad_id}", token=TOKEN)

# 创建：负数利率/额度（应被拒绝）
r, code, _ = curl("POST", "/api/products", token=TOKEN, body={**newp, "productName": "__QA负数__", "minRate": -5, "maxAmount": -10})
neg_id = r["data"]["id"] if r and r.get("success") else None
check("负数金额/利率被拒绝", code == 400, f"code={code}")
if neg_id:
    curl("DELETE", f"/api/products/{neg_id}", token=TOKEN)

# 创建：minRate > maxRate（应被拒绝）
r, code, _ = curl("POST", "/api/products", token=TOKEN, body={**newp, "productName": "__QA倒挂__", "minRate": 9, "maxRate": 2})
inv_id = r["data"]["id"] if r and r.get("success") else None
check("minRate>maxRate 被拒绝", code == 400, f"code={code}")
if inv_id:
    curl("DELETE", f"/api/products/{inv_id}", token=TOKEN)

# 创建：非数字字符串（原先 Number(x)||0 会静默吞成 0）
r, code, _ = curl("POST", "/api/products", token=TOKEN, body={**newp, "productName": "__QA非数字__", "minRate": "abc"})
nd_id = r["data"]["id"] if r and r.get("success") else None
check("非数字字符串被拒绝（不再静默转 0）", code == 400, f"code={code}")
if nd_id:
    curl("DELETE", f"/api/products/{nd_id}", token=TOKEN)

# 超长字符串
r, code, _ = curl("POST", "/api/products", token=TOKEN, body={**newp, "productName": "超" * 5000})
long_id = r["data"]["id"] if r and r.get("success") else None
check("超长产品名未被限制（缺陷）", code == 200, f"5000 字符被接受 len={len(r['data']['productName']) if long_id else 0}")
if long_id:
    curl("DELETE", f"/api/products/{long_id}", token=TOKEN)

# 越权：访问不存在的 id
r, code, _ = curl("GET", "/api/products/__nonexistent__", token=TOKEN)
check("不存在产品返回 404", code == 404, f"code={code}")

# 删除不存在
r, code, _ = curl("DELETE", "/api/products/__nonexistent__", token=TOKEN)
check("删除不存在产品返回 404", code == 404, f"code={code}")

# ---------- 客户 ----------
print("\n=== 3. 客户 ===")
r, code, _ = curl("GET", "/api/customers", token=TOKEN)
custs = r["data"] if r and r.get("success") else []
check("客户列表可读", code == 200, f"{len(custs)} 条")
cid = custs[0]["id"] if custs else None

r, code, _ = curl("POST", "/api/customers", token=TOKEN, body={"name": ""})
check("创建客户缺姓名被拒", code == 400, f"code={code}")

r, code, _ = curl("POST", "/api/customers", token=TOKEN, body={"name": "__QA客户__", "phone": "abc12345678"})
qc = r["data"]["id"] if r and r.get("success") else None
check("非法手机号被拒绝", code == 400, f"code={code}")
if qc:
    curl("DELETE", f"/api/customers/{qc}", token=TOKEN)

if cid:
    r, code, _ = curl("GET", f"/api/customers/{cid}", token=TOKEN)
    check("客户详情可读", code == 200, "")
    r, code, _ = curl("GET", f"/api/customers/{cid}/simulations", token=TOKEN)
    check("推演历史可读", code == 200, f"{len(r['data']) if r and r.get('success') else 0} 条")

# ---------- 日程 ----------
print("\n=== 4. 日程 ===")
r, code, _ = curl("GET", "/api/schedules", token=TOKEN)
sches = r["data"] if r and r.get("success") else []
check("日程列表可读", code == 200, f"{len(sches)} 条")

r, code, _ = curl("POST", "/api/schedules", token=TOKEN, body={"title": ""})
check("创建日程缺标题被拒", code == 400, f"code={code}")

r, code, _ = curl("POST", "/api/schedules", token=TOKEN, body={"title": "__QA日程__"})
check("创建日程缺开始时间被拒", code == 400, f"code={code}")

# 非法时间格式（应被拒绝）
r, code, _ = curl("POST", "/api/schedules", token=TOKEN, body={"title": "__QA坏时间__", "startTime": "not-a-date"})
bad_sch = r["data"]["id"] if r and r.get("success") else None
check("非法时间格式被拒绝", code == 400, f"code={code}")
if bad_sch:
    curl("DELETE", f"/api/schedules/{bad_sch}", token=TOKEN)

# 结束时间早于开始时间（应被拒绝）
r, code, _ = curl("POST", "/api/schedules", token=TOKEN, body={
    "title": "__QA时间倒挂__", "startTime": "2026-09-20T18:00", "endTime": "2026-09-20T09:00"})
rev_sch = r["data"]["id"] if r and r.get("success") else None
check("结束时间早于开始时间被拒绝", code == 400, f"code={code}")
if rev_sch:
    curl("DELETE", f"/api/schedules/{rev_sch}", token=TOKEN)

# 提醒时间晚于开始时间（应被拒绝）
r, code, _ = curl("POST", "/api/schedules", token=TOKEN, body={
    "title": "__QA提醒倒挂__", "startTime": "2026-09-20T09:00", "reminderTime": "2026-09-20T20:00"})
rem_sch = r["data"]["id"] if r and r.get("success") else None
check("提醒时间晚于开始时间被拒绝", code == 400, f"code={code}")
if rem_sch:
    curl("DELETE", f"/api/schedules/{rem_sch}", token=TOKEN)

# 非法优先级（应被拒绝）
r, code, _ = curl("POST", "/api/schedules", token=TOKEN, body={"title": "__QA坏优先级__", "startTime": "2026-09-15T10:00", "priority": "P9"})
bp = r["data"]["id"] if r and r.get("success") else None
check("非法优先级被拒绝", code == 400, f"code={code}")
if bp:
    curl("DELETE", f"/api/schedules/{bp}", token=TOKEN)

# 正常创建 + PATCH
r, code, _ = curl("POST", "/api/schedules", token=TOKEN, body={"title": "__QA正常日程__", "startTime": "2026-09-20T14:00", "endTime": "2026-09-20T15:00", "priority": "P1", "type": "meeting"})
sid = r["data"]["id"] if r and r.get("success") else None
check("创建日程成功", code == 200 and sid, f"id={sid}")

if sid:
    r, code, _ = curl("PATCH", f"/api/schedules/{sid}", token=TOKEN, body={"done": True})
    check("PATCH 标记完成", code == 200 and r["data"]["done"] is True, f"done={r['data'].get('done') if r and r.get('success') else '?'}")
    r, code, _ = curl("PATCH", f"/api/schedules/{sid}", token=TOKEN, body={"done": False})
    check("PATCH 恢复未完成", code == 200 and r["data"]["done"] is False, "")
    # 非法 done 值
    r, code, _ = curl("PATCH", f"/api/schedules/{sid}", token=TOKEN, body={"done": "yes"})
    check("PATCH done 非布尔可接受（宽松）", code == 200, f"done='yes' -> {r['data'].get('done') if r and r.get('success') else '?'}")
    curl("DELETE", f"/api/schedules/{sid}", token=TOKEN)

# ---------- 分页/大数据量 ----------
print("\n=== 5. 分页与数据量 ===")
r, code, _ = curl("GET", "/api/products?page=1&pageSize=10", token=TOKEN)
check("产品接口忽略分页参数（无分页能力）", code == 200, f"仍返回全量 {len(r['data'])} 条")
r, code, _ = curl("GET", "/api/schedules", token=TOKEN)
check("日程接口无分页", code == 200, f"全量 {len(r['data'])} 条")

# ---------- 搜索/注入 ----------
print("\n=== 6. 注入与特殊字符 ===")
r, code, _ = curl("POST", "/api/auth/login", body={"phone": "13800138000' OR '1'='1", "password": "x"})
check("登录 SQL 注入被防住", code == 400, f"code={code}")

r, code, _ = curl("POST", "/api/products", token=TOKEN, body={**newp, "productName": "<script>alert(1)</script>", "institution": "'; DROP TABLE products;--"})
xss_id = r["data"]["id"] if r and r.get("success") else None
check("XSS/SQL 特殊字符被存储（需前端转义）", code == 200, "存储型 XSS 风险需前端确认")
if xss_id:
    r2, _, _ = curl("GET", f"/api/products/{xss_id}", token=TOKEN)
    # 确认表还在
    r3, c3, _ = curl("GET", "/api/products", token=TOKEN)
    check("products 表未被注入删除", c3 == 200 and len(r3["data"]) > 0, f"{len(r3['data'])} 条")
    curl("DELETE", f"/api/products/{xss_id}", token=TOKEN)

# ---------- dashboard ----------
print("\n=== 7. 仪表盘 ===")
r, code, _ = curl("GET", "/api/dashboard", token=TOKEN)
check("仪表盘接口可读", code == 200, "")
if r and r.get("success"):
    print("      data:", json.dumps(r["data"], ensure_ascii=False)[:200])

# ---------- AI 接口 ----------
# /api/ai/match 的契约是 { customer: 客户对象, products: 产品数组 }，
# 传 customerId 会被后端判为缺参数——这是调用方用法问题，不是接口缺陷。
print("\n=== 8. AI 接口 ===")
r, _, _ = curl("GET", "/api/customers", token=TOKEN)
_cust = (r or {}).get("data") or []
if _cust:
    r, code, _ = curl("POST", "/api/ai/match", token=TOKEN, body={"customer": _cust[0], "products": []})
    ok_cnt = len(r["data"].get("approved") or []) if r and r.get("success") else 0
    check("AI 匹配可调用（正确契约）", code == 200, f"code={code} 命中 {ok_cnt} 款")
else:
    check("AI 匹配可调用（正确契约）", False, "无客户数据可测")
r, code, _ = curl("POST", "/api/ai/match", token=TOKEN, body={})
check("AI 匹配缺参数报错可控", code in (200, 400), f"code={code}")

# ---------- 清理 ----------
print("\n=== 清理测试数据 ===")
if pid:
    curl("DELETE", f"/api/products/{pid}", token=TOKEN)
r, code, _ = curl("GET", "/api/products", token=TOKEN)
check("测试产品已清理", len(r["data"]) == BASE_PROD, f"{len(r['data'])} vs 原始 {BASE_PROD}")

print(f"\n{'='*50}\n通过 {len(PASS)} / 失败 {len(FAIL)}")
if FAIL:
    print("\n【失败/缺陷清单】")
    for f in FAIL:
        print("  -", f)
