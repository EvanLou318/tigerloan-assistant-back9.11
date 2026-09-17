# -*- coding: utf-8 -*-
# A 组安全修复 API 验证
import json, urllib.request, urllib.error, time

BASE = "http://localhost:3001"
PASS, FAIL = [], []

def api(method, path, body=None, token=None, form=None, raw=False):
    url = BASE + path
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode(); headers["Content-Type"] = "application/json"
    if token:
        headers["X-Auth-Token"] = token
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            payload = r.read()
            if raw: return r.status, payload
            return r.status, json.loads(payload)
    except urllib.error.HTTPError as e:
        payload = e.read()
        if raw: return e.code, payload
        try: return e.code, json.loads(payload)
        except: return e.code, {"raw": payload[:100].decode('utf-8', 'ignore')}

def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("PASS " if cond else "FAIL ") + name + ((" | " + str(detail)[:150]) if not cond else ""))

# ---------- 1. 登录统一文案 ----------
st, r = api("POST", "/api/auth/login", {"phone": "13800138000", "password": "wrongpass"})
check("错误密码返回统一文案", st == 400 and r.get("message") == "手机号或密码错误", r)
st, r = api("POST", "/api/auth/login", {"phone": "13999990000", "password": "whatever"})
check("不存在账号返回同一文案", st == 400 and r.get("message") == "手机号或密码错误", r)

# ---------- 2. 正常登录 ----------
st, r = api("POST", "/api/auth/login", {"phone": "13800138000", "password": "abc123"})
check("正常登录成功", st == 200 and r.get("success"), r)
TOKEN = r["data"]["token"]

# ---------- 3. token_version：改密吊销旧 token（改回还原） ----------
# 注：登录限流测试在文件末尾执行（避免同键拒绝影响本项登录）
st, r = api("POST", "/api/auth/change-password", {"oldPassword": "abc123", "newPassword": "Qa9x2w7m"}, token=TOKEN)
check("修改密码成功", st == 200 and r.get("success"), (st, r))
st, r = api("GET", "/api/auth/me", token=TOKEN)
check("改密后旧 token 立即失效", st == 401, (st, r))
st, r = api("POST", "/api/auth/login", {"phone": "13800138000", "password": "Qa9x2w7m"})
check("新密码可登录", st == 200, (st, r))
TOKEN2 = r["data"]["token"]
st, r = api("POST", "/api/auth/change-password", {"oldPassword": "Qa9x2w7m", "newPassword": "abc123"}, token=TOKEN2)
check("密码还原成功", st == 200, (st, r))
st, r = api("POST", "/api/auth/login", {"phone": "13800138000", "password": "abc123"})
check("还原后登录正常", st == 200, (st, r))
TOKEN = r["data"]["token"]

# ---------- 4. /uploads 鉴权（使用还原后的 token） ----------
import os, struct
# 找一个已存在的上传文件
st, r = api("GET", "/api/customers", token=TOKEN)
up_file = None
for c in r.get("data", []):
    for m in c.get("materials", []):
        fp = m.get("filePath") or m.get("file_path")
        if fp:
            up_file = fp; break
    if up_file: break
if not up_file:
    # 用头像字段兜底
    for c in r.get("data", []):
        pass
if not up_file:
    # 直接创建一个：走 OCR 上传
    import uuid
    png = open(os.path.join(os.path.dirname(__file__), "e2e_shots", "mobile_bfix", "01_login.png"), "rb").read()
    boundary = uuid.uuid4().hex
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"qa.png\"\r\n"
            f"Content-Type: image/png\r\n\r\n").encode() + png + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(BASE + "/api/ai/ocr/idcard", data=body, method="POST",
        headers={"X-Auth-Token": TOKEN, "Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        r2 = json.loads(resp.read())
    up_file = r2["data"].get("filePath")
print("uploads test file:", up_file)
st, body = api("GET", up_file, raw=True)
check("/uploads 无凭证 → 401", st == 401, (st, body[:80]))
st, body = api("GET", up_file + "?token=" + TOKEN, raw=True)
check("/uploads ?token= → 200", st == 200 and len(body) > 0, (st, body[:80]))
st, body = api("GET", up_file, token=TOKEN, raw=True)
check("/uploads 请求头 → 200", st == 200, (st, body[:80]))
st, body = api("GET", up_file + "?token=invalid.jwt.token", raw=True)
check("/uploads 伪造 token → 401", st == 401, (st, body[:80]))

# ---------- 5. services 掩码回显（加密存储后） ----------
st, r = api("GET", "/api/services", token=TOKEN)
groups = r["data"]
llm = [g for g in groups if g["category"] == "llm"][0]["providers"][0]
asr_g = [g for g in groups if g["category"] == "asr"][0]["providers"]
check("LLM key 掩码回显正常（解密链路通）", llm["hasKey"] and llm["apiKeyMasked"].startswith("sk-d"), llm["apiKeyMasked"])
check("ASR key 掩码回显正常", asr_g and asr_g[0]["hasKey"] and asr_g[0]["apiKeyMasked"].startswith("6918"), asr_g[0]["apiKeyMasked"] if asr_g else "none")

# ---------- 6. LLM 真实链路（解密后调用） ----------
st, r = api("POST", "/api/ai/assistant", {"text": "查询今天的日程"}, token=TOKEN)
check("AI 助理真实 LLM 调用正常", st == 200 and r.get("success"), (st, r))

# ---------- 7. ASR 失败提示保留（expose 标记） ----------
st, r = api("POST", "/api/ai/extract/schedule", {"text": "明天上午九点开会"}, token=TOKEN)
check("extract/schedule LLM 正常", st == 200 and r.get("success"), (st, r))

# ---------- 8. 登录限流（放最后：同键失败会连带拒绝后续同账号登录）----------
codes = []
for i in range(6):
    st, r = api("POST", "/api/auth/login", {"phone": "13800138000", "password": "bad" + str(i)})
    codes.append(st)
check("前 5 次失败为 400", all(c == 400 for c in codes[:5]), codes)
check("第 6 次失败触发 429 限流", codes[5] == 429, codes)

print(f"\n===== {len(PASS)} PASS / {len(FAIL)} FAIL =====")
for f in FAIL: print("FAILED:", f)
