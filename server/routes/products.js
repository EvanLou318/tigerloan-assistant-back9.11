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

  const id = genId('p')
  const now = fmtDateTime()
  db.prepare(`
    INSERT INTO products (id, user_id, product_name, institution, min_rate, max_rate, rate_type, min_amount, max_amount,
      loan_term, repayment_method, conditions, status, source, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`)
    .run(id, req.user.id, b.productName, b.institution,
      Number(b.minRate) || 0, Number(b.maxRate) || 0,
      b.rateType === 'monthly' ? 'monthly' : 'annual',
      Number(b.minAmount) || 0, Number(b.maxAmount) || 0,
      b.loanTerm || '', b.repaymentMethod || '', b.conditions || '',
      'active', b.source || 'text', now)

  ok(res, rowToProduct(findProduct(id, req.user.id)))
})

// PUT /api/products/:id  编辑产品
router.put('/:id', (req, res) => {
  findProduct(req.params.id, req.user.id)
  const b = req.body || {}
  const now = fmtDateTime()

  db.prepare(`
    UPDATE products SET
      product_name = ?, institution = ?, min_rate = ?, max_rate = ?, rate_type = ?, min_amount = ?, max_amount = ?,
      loan_term = ?, repayment_method = ?, conditions = ?, updated_at = ?
    WHERE id = ? AND user_id = ?`)
    .run(b.productName || '', b.institution || '',
      Number(b.minRate) || 0, Number(b.maxRate) || 0,
      b.rateType === 'monthly' ? 'monthly' : 'annual',
      Number(b.minAmount) || 0, Number(b.maxAmount) || 0,
      b.loanTerm || '', b.repaymentMethod || '', b.conditions || '',
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
