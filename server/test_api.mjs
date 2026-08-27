// 后端全接口联调测试（mock provider）
const BASE = 'http://localhost:3001/api'
let token = ''
const log = (...a) => console.log(...a)
const j = (r) => r.json()

async function call(method, path, body, auth = true, isForm = false) {
  const headers = {}
  if (auth) headers.Authorization = `Bearer ${token}`
  let init = { method, headers }
  if (body !== undefined) {
    if (isForm) { init.body = body } // FormData
    else { headers['Content-Type'] = 'application/json'; init.body = JSON.stringify(body) }
  }
  const res = await fetch(BASE + path, init)
  const text = await res.text()
  let data
  try { data = JSON.parse(text) } catch { data = text }
  return { status: res.status, data }
}

let pass = 0, fail = 0
function check(name, cond, extra = '') {
  if (cond) { pass++; log(`  ✓ ${name}`) }
  else { fail++; log(`  ✗ ${name}  ${extra}`) }
}

async function main() {
  log('\n=== 1. 认证 ===')
  let r = await call('POST', '/auth/login', { phone: '13800138000', password: 'abc123' }, false)
  check('登录成功', r.data.success && r.data.data.token, JSON.stringify(r.data).slice(0, 120))
  token = r.data.data.token
  check('无 token 被拒', (await call('GET', '/products', undefined, false)).status === 401)

  log('\n=== 2. 产品库 ===')
  r = await call('GET', '/products')
  check('产品列表返回', r.data.success && Array.isArray(r.data.data) && r.data.data.length >= 5, 'len=' + (r.data.data?.length))
  const pid = r.data.data[0].id
  r = await call('GET', `/products/${pid}`)
  check('产品详情', r.data.success && r.data.data.id === pid)
  r = await call('POST', '/products', { productName: '测试产品A', institution: '测试银行', minRate: 4, maxRate: 6, minAmount: 1, maxAmount: 10 })
  check('新建产品', r.data.success && r.data.data.productName === '测试产品A')
  const newPid = r.data.data.id
  r = await call('PATCH', `/products/${newPid}/status`, { status: 'disabled' })
  check('启用/禁用', r.data.success && r.data.data.status === 'disabled')
  r = await call('PUT', `/products/${newPid}`, { productName: '测试产品A改', institution: '测试银行', conditions: '年龄22-55周岁；负债率≤50%' })
  check('编辑产品', r.data.success && r.data.data.productName === '测试产品A改')

  log('\n=== 3. 客户360 ===')
  r = await call('GET', '/customers')
  check('客户列表', r.data.success && Array.isArray(r.data.data) && r.data.data.length >= 3)
  const cid = r.data.data[0].id
  r = await call('GET', `/customers/${cid}`)
  check('客户详情含材料', r.data.success && Array.isArray(r.data.data.materials) && r.data.data.materials.length > 0)
  r = await call('POST', '/customers', { name: '测试客户B', phone: '13700137000', monthlyIncome: 12000, totalDebt: 30000 })
  check('新建客户', r.data.success && r.data.data.name === '测试客户B')
  const newCid = r.data.data.id
  r = await call('PUT', `/customers/${newCid}`, { monthlyIncome: 20000, hasMortgage: true })
  check('编辑客户(含布尔)', r.data.success && r.data.data.monthlyIncome === 20000 && r.data.data.hasMortgage === true)
  r = await call('POST', `/customers/${newCid}/materials`, { type: '身份证', source: 'upload', confidence: 0.99 })
  check('添加材料', r.data.success && r.data.data.type === '身份证')
  const mid = r.data.data.id
  r = await call('PUT', `/customers/${newCid}/materials/${mid}`, { type: '银行流水' })
  check('编辑材料类型', r.data.success && r.data.data.type === '银行流水')
  r = await call('DELETE', `/customers/${newCid}/materials/${mid}`)
  check('删除材料', r.data.success && r.data.data.deleted)

  log('\n=== 4. 推演记录 ===')
  r = await call('GET', `/customers/${cid}/simulations`)
  check('推演历史', r.data.success && Array.isArray(r.data.data))
  r = await call('POST', `/customers/${cid}/simulations`, {
    name: '测试推演', adjustments: { monthlyIncome: { old: 15000, new: 25000 } },
    matchResult: { approved: [{ productId: pid, productName: 'x' }], rejected: [] },
  })
  check('保存推演', r.data.success && r.data.data.name === '测试推演')

  log('\n=== 5. 日程 ===')
  r = await call('GET', '/schedules')
  check('日程列表', r.data.success && Array.isArray(r.data.data) && r.data.data.length >= 5)
  r = await call('POST', '/schedules', { title: '测试日程', startTime: new Date(Date.now() + 3600000).toISOString(), priority: 'P0', type: 'meeting', customerId: cid, customerName: '测试' })
  check('新建日程', r.data.success && r.data.data.title === '测试日程')
  const sid = r.data.data.id
  r = await call('PATCH', `/schedules/${sid}`, { done: true })
  check('完成日程(布尔)', r.data.success && r.data.data.done === true)
  r = await call('DELETE', `/schedules/${sid}`)
  check('删除日程', r.data.success && r.data.data.deleted)

  log('\n=== 6. 仪表盘 ===')
  r = await call('GET', '/dashboard')
  check('仪表盘统计', r.data.success && typeof r.data.data.customerCount === 'number' && r.data.data.todaySchedules.length >= 0)
  check('今日日程预览', Array.isArray(r.data.data.todaySchedules))

  log('\n=== 7. AI 匹配（核心，mock 延迟3s）===')
  const cust = r.data // reuse
  r = await call('POST', '/ai/match', { customer: r.customer || { age: 32, monthlyIncome: 15000, queryCount3m: 5, housingFundBase: 3500, maxOverdueMonths: 0, totalDebt: 80000 } })
  check('匹配返回', r.data.success && Array.isArray(r.data.data.approved) && Array.isArray(r.data.data.rejected))
  log('    准入数=' + r.data.data.approved.length + ' 拒贷数=' + r.data.data.rejected.length)

  log('\n=== 8. AI 助理 / 提取（轻量）===')
  r = await call('POST', '/ai/assistant', { text: '新增客户 张三 13800138000' })
  check('助理意图识别', r.data.success && r.data.data.intent === 'customer_create')
  r = await call('POST', '/ai/extract/schedule', { text: '明天下午3点与张总面谈讨论方案' })
  check('日程提取', r.data.success && r.data.data.data && r.data.data.data.title)
  r = await call('POST', '/ai/asr', { text: '这是一段模拟语音' })
  check('ASR', r.data.success && r.data.data.text)

  log('\n=== 9. 清理测试数据 ===')
  await call('DELETE', `/products/${newPid}`)
  await call('DELETE', `/customers/${newCid}`)
  log('    已清理测试产品/客户')

  log(`\n========== 结果：通过 ${pass} / 失败 ${fail} ==========`)
  process.exit(fail > 0 ? 1 : 0)
}
main().catch(e => { console.error('测试异常中断：', e); process.exit(2) })
