# -*- coding: utf-8 -*-
# 深度缺陷排查：数据一致性 / 越权 / 边界时序 / 状态残留
import json, subprocess, time

BASE = "http://127.0.0.1:3007"
ISSUES = []


def curl(method, path, token=None, body=None):
    cmd = ["curl", "-s", "--noproxy", "*", "-m", "20", "-X", method, BASE + path, "-w", "\n@@@%{http_code}"]
    if token:
        cmd += ["-H", f"X-Auth-Token: {token}"]
    if body is not None:
        cmd += ["-H", "Content-Type: application/json", "-d", json.dumps(body, ensure_ascii=False)]
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    if "@@@" not in out:
        return None, 0
    payload, code = out.rsplit("@@@", 1)
    try:
        return json.loads(payload), int(code)
    except Exception:
        return None, int(code)


def report(level, title, detail):
    ISSUES.append((level, title, detail))
    print(f"  [{level}] {title}\n         {detail}")


r, _ = curl("POST", "/api/auth/login", body={"phone": "13800138000", "password": "abc123"})
TOKEN = r["data"]["token"]
UID = r["data"]["user"]["id"]

print("=== A. 数据一致性 ===")

# A1. 产品禁用后，AI 匹配是否还会推荐它？
r, _ = curl("GET", "/api/products", token=TOKEN)
prods = r["data"]
dis = [p for p in prods if p["status"] != "active"]
if dis:
    dp = dis[0]
    print(f"  取一个禁用产品: {dp['productName']} (status={dp['status']})")
    r, _ = curl("GET", "/api/customers", token=TOKEN)
    cust = r["data"][0]
    r, code = curl("POST", "/api/ai/match", token=TOKEN, body={"customer": cust, "products": []})
    matched_ids = []
    if r and r.get("success"):
        matched_ids = [x["productId"] for x in r["data"]["approved"]] + [x["productId"] for x in r["data"]["rejected"]]
    if dp["id"] in matched_ids:
        report("高", "禁用产品仍参与 AI 匹配", f"产品 {dp['productName']} 状态为禁用，但出现在匹配结果中")
    else:
        print(f"  OK: 禁用产品未参与匹配（匹配到 {len(matched_ids)} 款）")

# A2. 删除客户后，其关联日程的 customerName 是否残留？
r, _ = curl("POST", "/api/customers", token=TOKEN, body={"name": "__QA待删客户__", "phone": "13900000000"})
qc = r["data"]["id"] if r and r.get("success") else None
if qc:
    r, _ = curl("POST", "/api/schedules", token=TOKEN, body={
        "title": "__QA关联日程__", "startTime": "2026-12-01T10:00",
        "customerId": qc, "customerName": "__QA待删客户__"})
    qs = r["data"]["id"] if r and r.get("success") else None
    curl("DELETE", f"/api/customers/{qc}", token=TOKEN)
    if qs:
        r, code = curl("GET", f"/api/schedules/{qs}", token=TOKEN)
        if r and r.get("success"):
            leftover = r["data"].get("customerId"), r["data"].get("customerName")
            if leftover[0] or leftover[1]:
                report("中", "删除客户后日程残留客户关联", f"日程仍指向已删除客户 customerId={leftover[0]}, customerName={leftover[1]}（脏数据）")
            else:
                print("  OK: 日程客户关联已清空")
        curl("DELETE", f"/api/schedules/{qs}", token=TOKEN)

# A3. 产品 rateType 月利率时，AI 匹配是否做了换算？（此前已提示 TODO）
r, _ = curl("GET", "/api/products", token=TOKEN)
for p in r["data"]:
    if p.get("rateType") == "monthly":
        report("中", "月利率产品未做年化换算", f"产品「{p['productName']}」rateType=monthly ({p['minRate']}%~{p['maxRate']}%)，匹配/展示若与其他年利率产品直接比较会失真")
        break
else:
    print("  OK: 当前无月利率产品")

print("\n=== B. 越权与权限 ===")

# B1. 普通用户能否访问 admin 接口
r, _ = curl("POST", "/api/admin/users", token=TOKEN, body={"phone": "13800000001", "name": "__QA普通用户__", "password": "abc12345", "role": "loan_manager"})
newu = r["data"]["id"] if r and r.get("success") else None
if newu:
    r, _ = curl("POST", "/api/auth/login", body={"phone": "13800000001", "password": "abc12345"})
    UTOKEN = r["data"]["token"] if r and r.get("success") else None
    if UTOKEN:
        # 无权限用户访问 admin
        for p in ["/api/admin/stats", "/api/admin/users", "/api/admin/audit-logs"]:
            r, code = curl("GET", p, token=UTOKEN)
            if code == 200:
                report("高", f"越权访问 {p}", f"loan_manager 角色可读取管理员接口，返回 200")
            else:
                print(f"  OK: {p} -> {code}")
        # 普通用户看别的用户数据（数据隔离）
        r, code = curl("GET", "/api/customers", token=UTOKEN)
        n = len(r["data"]) if r and r.get("success") else 0
        print(f"  普通用户客户数: {n}（自己账号的数据隔离）")
        r, _ = curl("GET", "/api/customers", token=TOKEN)
        print(f"  管理员客户数: {len(r['data'])}")
        if n > 0:
            r2, _ = curl("GET", "/api/products", token=UTOKEN)
            print(f"  普通用户产品数: {len(r2['data']) if r2 and r2.get('success') else 0}")
    curl("DELETE", f"/api/admin/users/{newu}", token=TOKEN)

print("\n=== C. 状态与时序 ===")

# C1. 结束时间早于开始时间
r, code = curl("POST", "/api/schedules", token=TOKEN, body={
    "title": "__QA时间倒挂__", "startTime": "2026-12-05T18:00", "endTime": "2026-12-05T09:00"})
if code == 200:
    sid = r["data"]["id"]
    sh, eh = r["data"]["startTime"], r["data"]["endTime"]
    report("中", "结束时间早于开始时间未被校验", f"start={sh} end={eh} 被接受，列表会显示异常时段")
    curl("DELETE", f"/api/schedules/{sid}", token=TOKEN)

# C2. 提醒时间晚于开始时间
r, code = curl("POST", "/api/schedules", token=TOKEN, body={
    "title": "__QA提醒晚于开始__", "startTime": "2026-12-06T09:00", "reminderTime": "2026-12-06T20:00"})
if code == 200:
    sid = r["data"]["id"]
    report("低", "提醒时间晚于开始时间未被校验", f"reminder={r['data']['reminderTime']} start={r['data']['startTime']}")
    curl("DELETE", f"/api/schedules/{sid}", token=TOKEN)

# C3. 并行创建（重复提交防护？）
import threading
results = []
def mk(i):
    r, c = curl("POST", "/api/products", token=TOKEN, body={
        "productName": f"__QA并发{i}__", "institution": "并发测试",
        "minRate": 3, "maxRate": 5, "minAmount": 1, "maxAmount": 10, "rateType": "annual"})
    results.append(r["data"]["id"] if r and r.get("success") else None)

ts = [threading.Thread(target=mk, args=(i,)) for i in range(5)]
for t in ts: t.start()
for t in ts: t.join()
ids = [x for x in results if x]
uniq = len(set(ids))
print(f"  并发创建 5 条产品: 得到 {len(ids)} 个 id，去重后 {uniq} 个")
if uniq != len(ids):
    report("中", "并发创建产生重复 ID", f"{len(ids)} 次创建只有 {uniq} 个唯一 id")
for i in ids:
    curl("DELETE", f"/api/products/{i}", token=TOKEN)

# C4. 超长/非法数字字段
r, code = curl("POST", "/api/products", token=TOKEN, body={
    "productName": "__QA超范围__", "institution": "X", "minRate": "abc", "maxAmount": "1e999", "rateType": "annual"})
if code == 200:
    pid = r["data"]["id"]
    report("中", "非数字字符串被静默转成 0", f"minRate='abc' 存为 {r['data']['minRate']}（用户输入被无声吞掉）")
    curl("DELETE", f"/api/products/{pid}", token=TOKEN)

print("\n" + "=" * 60)
by_level = {}
for lv, t, d in ISSUES:
    by_level.setdefault(lv, []).append(t)
print(f"共发现 {len(ISSUES)} 个问题")
for lv in ["高", "中", "低"]:
    if lv in by_level:
        print(f"  {lv}危: {len(by_level[lv])} 个 -> {'; '.join(by_level[lv])}")
