// ==================== 客户 360° 路由 ====================
// 客户 CRUD + 材料管理 + 推演记录

import { Router } from 'express'
import { db, rowToCustomer, rowToMaterial, rowToSimulation, getMaterialsByCustomer } from '../db.js'
import { ok, fail, genId, fmtDateTime, BizError } from '../utils.js'
import { applyMasking } from '../rbac.js'
import { writeAudit } from '../audit.js'

const router = Router()

function findCustomerRow(id, userId) {
  const row = db.prepare('SELECT * FROM customers WHERE id = ? AND user_id = ?').get(id, userId)
  if (!row) throw new BizError('客户不存在', 404)
  return row
}

function customerWithMaterials(row) {
  return rowToCustomer(row, getMaterialsByCustomer(row.id))
}

// 读接口统一走脱敏：开关开启且无 unmasked 权限时，手机号/身份证返回掩码
function maskedCustomer(row, role) {
  return applyMasking(customerWithMaterials(row), role)
}

// GET /api/customers  客户列表（含材料）
router.get('/', (req, res) => {
  const rows = db.prepare('SELECT * FROM customers WHERE user_id = ? ORDER BY created_at DESC').all(req.user.id)
  ok(res, rows.map((row) => maskedCustomer(row, req.user.role)))
})

// GET /api/customers/:id  客户详情
router.get('/:id', (req, res) => {
  ok(res, maskedCustomer(findCustomerRow(req.params.id, req.user.id), req.user.role))
})

// POST /api/customers  新建客户
router.post('/', (req, res) => {
  const b = req.body || {}
  if (!b.name?.trim()) throw new BizError('请填写客户姓名')
  const phone = (b.phone || '').replace(/\s/g, '')
  if (phone && !/^1[3-9]\d{9}$/.test(phone) && !phone.includes('*')) {
    throw new BizError('手机号格式不正确')
  }

  // 同手机号查重（允许脱敏格式跳过）
  if (phone && !phone.includes('*')) {
    const dup = db.prepare("SELECT id, name FROM customers WHERE user_id = ? AND replace(phone, ' ', '') = ?")
      .get(req.user.id, phone)
    if (dup) throw new BizError(`该手机号已存在客户档案（${dup.name}）`)
  }

  const id = genId('c')
  const now = fmtDateTime()
  db.prepare(`
    INSERT INTO customers (id, user_id, name, phone, id_card, age, gender, source, city, marital_status,
      education, occupation, remark, monthly_income, housing_fund_base, total_debt, credit_card_usage,
      query_count_1m, query_count_3m, query_count_6m, max_overdue_months, property_value, has_mortgage,
      car_value, expected_amount, expected_rate, employer, position, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`)
    .run(id, req.user.id, b.name.trim(), phone, b.idCard || '', Number(b.age) || 0, b.gender || '',
      b.source || '', b.city || '', b.maritalStatus || '', b.education || '', b.occupation || '',
      b.remark || '', Number(b.monthlyIncome) || 0, Number(b.housingFundBase) || 0,
      Number(b.totalDebt) || 0, Number(b.creditCardUsage) || 0,
      Number(b.queryCount1m) || 0, Number(b.queryCount3m) || 0, Number(b.queryCount6m) || 0,
      Number(b.maxOverdueMonths) || 0, Number(b.propertyValue) || 0, b.hasMortgage ? 1 : 0,
      Number(b.carValue) || 0, Number(b.expectedAmount) || 0, Number(b.expectedRate) || 0,
      b.employer || '', b.position || '', now, now)

  ok(res, maskedCustomer(findCustomerRow(id, req.user.id), req.user.role))
})

// PUT /api/customers/:id  更新客户（全字段，缺失字段保持原值）
router.put('/:id', (req, res) => {
  const row = findCustomerRow(req.params.id, req.user.id)
  const b = req.body || {}
  const now = fmtDateTime()

  // 防呆：脱敏开启时前端可能回显掩码值（如 138****6688），不能覆盖库里的明文
  if (typeof b.phone === 'string' && b.phone.includes('*')) delete b.phone
  if (typeof b.idCard === 'string' && b.idCard.includes('*')) delete b.idCard

  db.prepare(`
    UPDATE customers SET
      name = ?, phone = ?, id_card = ?, age = ?, gender = ?, source = ?, city = ?, marital_status = ?,
      education = ?, occupation = ?, remark = ?, monthly_income = ?, housing_fund_base = ?, total_debt = ?,
      credit_card_usage = ?, query_count_1m = ?, query_count_3m = ?, query_count_6m = ?,
      max_overdue_months = ?, property_value = ?, has_mortgage = ?, car_value = ?,
      expected_amount = ?, expected_rate = ?, employer = ?, position = ?, updated_at = ?
    WHERE id = ? AND user_id = ?`)
    .run(
      b.name?.trim() || row.name,
      b.phone !== undefined ? String(b.phone) : row.phone,
      b.idCard !== undefined ? String(b.idCard) : row.id_card,
      b.age !== undefined ? Number(b.age) || 0 : row.age,
      b.gender !== undefined ? String(b.gender) : row.gender,
      b.source !== undefined ? String(b.source) : row.source,
      b.city !== undefined ? String(b.city) : row.city,
      b.maritalStatus !== undefined ? String(b.maritalStatus) : row.marital_status,
      b.education !== undefined ? String(b.education) : row.education,
      b.occupation !== undefined ? String(b.occupation) : row.occupation,
      b.remark !== undefined ? String(b.remark) : row.remark,
      b.monthlyIncome !== undefined ? Number(b.monthlyIncome) || 0 : row.monthly_income,
      b.housingFundBase !== undefined ? Number(b.housingFundBase) || 0 : row.housing_fund_base,
      b.totalDebt !== undefined ? Number(b.totalDebt) || 0 : row.total_debt,
      b.creditCardUsage !== undefined ? Number(b.creditCardUsage) || 0 : row.credit_card_usage,
      b.queryCount1m !== undefined ? Number(b.queryCount1m) || 0 : row.query_count_1m,
      b.queryCount3m !== undefined ? Number(b.queryCount3m) || 0 : row.query_count_3m,
      b.queryCount6m !== undefined ? Number(b.queryCount6m) || 0 : row.query_count_6m,
      b.maxOverdueMonths !== undefined ? Number(b.maxOverdueMonths) || 0 : row.max_overdue_months,
      b.propertyValue !== undefined ? Number(b.propertyValue) || 0 : row.property_value,
      b.hasMortgage !== undefined ? (b.hasMortgage ? 1 : 0) : row.has_mortgage,
      b.carValue !== undefined ? Number(b.carValue) || 0 : row.car_value,
      b.expectedAmount !== undefined ? Number(b.expectedAmount) || 0 : row.expected_amount,
      b.expectedRate !== undefined ? Number(b.expectedRate) || 0 : row.expected_rate,
      b.employer !== undefined ? String(b.employer) : row.employer,
      b.position !== undefined ? String(b.position) : row.position,
      now, req.params.id, req.user.id)

  ok(res, maskedCustomer(findCustomerRow(req.params.id, req.user.id), req.user.role))
})

// DELETE /api/customers/:id  删除客户（材料级联删除）
router.delete('/:id', (req, res) => {
  const row = findCustomerRow(req.params.id, req.user.id)
  // 日程不做级联删除（日程本身是经理的工作安排，有价值），只解除关联，
  // 否则会留下指向已删客户的悬空 customer_id，日程卡片继续展示不存在的客户名。
  const orphaningSchedules = db
    .prepare('SELECT COUNT(*) AS n FROM schedules WHERE customer_id = ? AND user_id = ?')
    .get(req.params.id, req.user.id).n
  db.prepare('DELETE FROM materials WHERE customer_id = ?').run(req.params.id)
  db.prepare('DELETE FROM simulations WHERE customer_id = ? AND user_id = ?').run(req.params.id, req.user.id)
  db.prepare('UPDATE schedules SET customer_id = NULL, customer_name = ? WHERE customer_id = ? AND user_id = ?')
    .run('', req.params.id, req.user.id)
  db.prepare('DELETE FROM customers WHERE id = ? AND user_id = ?').run(req.params.id, req.user.id)
  writeAudit(
    req,
    'customer.delete',
    `${row.name}（ID ${row.id}）`,
    `级联删除材料与推演记录${orphaningSchedules ? `；已解除 ${orphaningSchedules} 条关联日程` : ''}`
  )
  ok(res, { deleted: true, detachedSchedules: orphaningSchedules })
})

// ---------- 材料 ----------

// POST /api/customers/:id/materials  添加材料
router.post('/:id/materials', (req, res) => {
  findCustomerRow(req.params.id, req.user.id)
  const b = req.body || {}
  if (!b.type) throw new BizError('请指定材料类型')

  const mid = genId('m')
  const now = fmtDateTime()
  db.prepare(`
    INSERT INTO materials (id, customer_id, type, source, confidence, field_count, source_name, file_path, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`)
    .run(mid, req.params.id, b.type, b.source || 'upload', Number(b.confidence) || 0.9,
      Number(b.fieldCount) || 0, b.sourceName || '', b.filePath || null, now)
  db.prepare('UPDATE customers SET updated_at = ? WHERE id = ?').run(now, req.params.id)

  ok(res, rowToMaterial(db.prepare('SELECT * FROM materials WHERE id = ?').get(mid)))
})

// PUT /api/customers/:id/materials/:mid  更新材料（类型更正等）
router.put('/:id/materials/:mid', (req, res) => {
  findCustomerRow(req.params.id, req.user.id)
  const row = db.prepare('SELECT * FROM materials WHERE id = ? AND customer_id = ?').get(req.params.mid, req.params.id)
  if (!row) throw new BizError('材料不存在', 404)

  const b = req.body || {}
  db.prepare(`
    UPDATE materials SET type = ?, source = ?, confidence = ?, field_count = ?, source_name = ?, file_path = ?
    WHERE id = ?`)
    .run(
      b.type !== undefined ? String(b.type) : row.type,
      b.source !== undefined ? String(b.source) : row.source,
      b.confidence !== undefined ? Number(b.confidence) : row.confidence,
      b.fieldCount !== undefined ? Number(b.fieldCount) : row.field_count,
      b.sourceName !== undefined ? String(b.sourceName) : row.source_name,
      b.filePath !== undefined ? (b.filePath || null) : row.file_path,
      req.params.mid)
  db.prepare('UPDATE customers SET updated_at = ? WHERE id = ?').run(fmtDateTime(), req.params.id)

  ok(res, rowToMaterial(db.prepare('SELECT * FROM materials WHERE id = ?').get(req.params.mid)))
})

// DELETE /api/customers/:id/materials/:mid  删除材料
router.delete('/:id/materials/:mid', (req, res) => {
  findCustomerRow(req.params.id, req.user.id)
  const row = db.prepare('SELECT * FROM materials WHERE id = ? AND customer_id = ?').get(req.params.mid, req.params.id)
  if (!row) throw new BizError('材料不存在', 404)

  db.prepare('DELETE FROM materials WHERE id = ?').run(req.params.mid)
  db.prepare('UPDATE customers SET updated_at = ? WHERE id = ?').run(fmtDateTime(), req.params.id)
  ok(res, { deleted: true })
})

// ---------- 推演记录 ----------

// GET /api/customers/:id/simulations  推演历史
router.get('/:id/simulations', (req, res) => {
  findCustomerRow(req.params.id, req.user.id)
  const rows = db.prepare(
    'SELECT * FROM simulations WHERE customer_id = ? AND user_id = ? ORDER BY created_at DESC'
  ).all(req.params.id, req.user.id)
  ok(res, rows.map(rowToSimulation))
})

// POST /api/customers/:id/simulations  保存推演
router.post('/:id/simulations', (req, res) => {
  findCustomerRow(req.params.id, req.user.id)
  const b = req.body || {}
  if (!b.matchResult) throw new BizError('缺少匹配结果')

  const id = genId('s')
  db.prepare(`
    INSERT INTO simulations (id, user_id, customer_id, name, adjustments, match_result, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)`)
    .run(id, req.user.id, req.params.id, b.name || '未命名推演',
      JSON.stringify(b.adjustments || {}), JSON.stringify(b.matchResult), fmtDateTime())

  ok(res, rowToSimulation(db.prepare('SELECT * FROM simulations WHERE id = ?').get(id)))
})

// DELETE /api/customers/:id/simulations/:sid  删除推演
router.delete('/:id/simulations/:sid', (req, res) => {
  findCustomerRow(req.params.id, req.user.id)
  const row = db.prepare('SELECT * FROM simulations WHERE id = ? AND customer_id = ? AND user_id = ?')
    .get(req.params.sid, req.params.id, req.user.id)
  if (!row) throw new BizError('推演记录不存在', 404)
  db.prepare('DELETE FROM simulations WHERE id = ?').run(req.params.sid)
  ok(res, { deleted: true })
})

// 统一错误处理
router.use((err, req, res, next) => {
  if (err instanceof BizError) return fail(res, err.status, err.message)
  next(err)
})

export default router
