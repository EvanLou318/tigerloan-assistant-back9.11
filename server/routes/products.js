// ==================== 产品库路由 ====================

import { Router } from 'express'
import { db, rowToProduct } from '../db.js'
import { ok, fail, genId, fmtDateTime, BizError } from '../utils.js'

const router = Router()

function findProduct(id, userId) {
  const row = db.prepare('SELECT * FROM products WHERE id = ? AND user_id = ?').get(id, userId)
  if (!row) throw new BizError('产品不存在', 404)
  return row
}

// 数值字段解析：非法输入必须报错，不能静默兜底成 0
// 旧写法 Number(x) || 0 会把 'abc' 吞成 0、把 '1e999' 吞成 Infinity、把 '' 吞成 0，
// 导致「负利率入库」「额度变成 null」这类脏数据。这里统一走严格校验。
function parseNum(value, label, { required = false, min = 0, max = Number.MAX_SAFE_INTEGER } = {}) {
  const raw = value
  if (raw === '' || raw === null || raw === undefined) {
    if (required) throw new BizError(`请填写${label}`)
    return 0
  }
  const n = typeof raw === 'number' ? raw : Number(String(raw).trim())
  if (!Number.isFinite(n)) throw new BizError(`${label}必须是有效数字`)
  if (n < min) throw new BizError(`${label}不能小于 ${min}`)
  if (n > max) throw new BizError(`${label}数值超出合理范围`)
  return n
}

// 统一解析产品数值字段 + 区间合法性
function parseProductNumbers(b) {
  const minRate = parseNum(b.minRate, '最低利率', { required: true, max: 100 })
  const maxRate = parseNum(b.maxRate, '最高利率', { max: 100 })
  const minAmount = parseNum(b.minAmount, '最低额度', { required: true, max: 1e9 })
  const maxAmount = parseNum(b.maxAmount, '最高额度', { max: 1e9 })

  if (maxRate && minRate > maxRate) throw new BizError('最低利率不能大于最高利率')
  if (maxAmount && minAmount > maxAmount) throw new BizError('最低额度不能大于最高额度')

  return { minRate, maxRate, minAmount, maxAmount }
}

const rateTypeOf = (v) => (v === 'monthly' ? 'monthly' : 'annual')

// GET /api/products  产品列表
router.get('/', (req, res) => {
  const rows = db.prepare('SELECT * FROM products WHERE user_id = ? ORDER BY created_at DESC').all(req.user.id)
  ok(res, rows.map(rowToProduct))
})

// GET /api/products/:id  产品详情
router.get('/:id', (req, res) => {
  ok(res, rowToProduct(findProduct(req.params.id, req.user.id)))
})

// POST /api/products  录入产品
router.post('/', (req, res) => {
  const b = req.body || {}
  if (!b.productName) throw new BizError('请填写产品名称')
  if (!b.institution) throw new BizError('请填写所属机构')

  const { minRate, maxRate, minAmount, maxAmount } = parseProductNumbers(b)

  const id = genId('p')
  const now = fmtDateTime()
  db.prepare(`
    INSERT INTO products (id, user_id, product_name, institution, min_rate, max_rate, rate_type, min_amount, max_amount,
      loan_term, repayment_method, conditions, status, source, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`)
    .run(id, req.user.id, b.productName, b.institution,
      minRate, maxRate, rateTypeOf(b.rateType),
      minAmount, maxAmount,
      b.loanTerm || '', b.repaymentMethod || '', b.conditions || '',
      'active', b.source || 'text', now)

  ok(res, rowToProduct(findProduct(id, req.user.id)))
})

// PUT /api/products/:id  编辑产品
router.put('/:id', (req, res) => {
  const existing = findProduct(req.params.id, req.user.id)
  const b = req.body || {}
  const now = fmtDateTime()

  // 编辑同样走严格校验；缺省字段回退为库中原值，而不是 0
  const merged = {
    minRate: b.minRate !== undefined ? b.minRate : existing.min_rate,
    maxRate: b.maxRate !== undefined ? b.maxRate : existing.max_rate,
    minAmount: b.minAmount !== undefined ? b.minAmount : existing.min_amount,
    maxAmount: b.maxAmount !== undefined ? b.maxAmount : existing.max_amount,
  }
  const { minRate, maxRate, minAmount, maxAmount } = parseProductNumbers(merged)

  db.prepare(`
    UPDATE products SET
      product_name = ?, institution = ?, min_rate = ?, max_rate = ?, rate_type = ?, min_amount = ?, max_amount = ?,
      loan_term = ?, repayment_method = ?, conditions = ?, updated_at = ?
    WHERE id = ? AND user_id = ?`)
    .run(b.productName !== undefined ? b.productName : existing.product_name,
      b.institution !== undefined ? b.institution : existing.institution,
      minRate, maxRate,
      b.rateType !== undefined ? rateTypeOf(b.rateType) : existing.rate_type,
      minAmount, maxAmount,
      b.loanTerm !== undefined ? b.loanTerm : existing.loan_term,
      b.repaymentMethod !== undefined ? b.repaymentMethod : existing.repayment_method,
      b.conditions !== undefined ? b.conditions : existing.conditions,
      now, req.params.id, req.user.id)

  ok(res, rowToProduct(findProduct(req.params.id, req.user.id)))
})

// PATCH /api/products/:id/status  启用/禁用
router.patch('/:id/status', (req, res) => {
  findProduct(req.params.id, req.user.id)
  const status = req.body?.status
  if (!['active', 'disabled'].includes(status)) throw new BizError('状态参数无效')

  db.prepare('UPDATE products SET status = ?, updated_at = ? WHERE id = ? AND user_id = ?')
    .run(status, fmtDateTime(), req.params.id, req.user.id)

  ok(res, rowToProduct(findProduct(req.params.id, req.user.id)))
})

// DELETE /api/products/:id  删除产品
router.delete('/:id', (req, res) => {
  findProduct(req.params.id, req.user.id)
  db.prepare('DELETE FROM products WHERE id = ? AND user_id = ?').run(req.params.id, req.user.id)
  ok(res, { deleted: true })
})

// 统一错误处理（BizError → 4xx）
router.use((err, req, res, next) => {
  if (err instanceof BizError) return fail(res, err.status, err.message)
  next(err)
})

export default router
