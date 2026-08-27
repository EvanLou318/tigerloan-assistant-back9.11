// ==================== 管理后台路由 ====================
// 面向运营/管理角色的聚合接口：全局统计、客户来源分布、近7日趋势、用户管理
// 复用 JWT 鉴权（demo 阶段不区分 admin 角色，正式版可在 middleware 中校验 role）

import { Router } from 'express'
import bcrypt from 'bcryptjs'
import { db } from '../db.js'
import { ok, fail, genId, fmtDateTime, BizError } from '../utils.js'

const router = Router()

// ---------- 全局统计看板 ----------
// GET /api/admin/stats
router.get('/stats', (req, res) => {
  const count = (sql, ...args) => db.prepare(sql).get(...args).n

  const today = fmtDateTime().slice(0, 10)
  const stats = {
    userCount: count('SELECT COUNT(*) AS n FROM users'),
    customerCount: count('SELECT COUNT(*) AS n FROM customers'),
    productCount: count('SELECT COUNT(*) AS n FROM products'),
    productActiveCount: count("SELECT COUNT(*) AS n FROM products WHERE status = 'active'"),
    scheduleCount: count('SELECT COUNT(*) AS n FROM schedules'),
    scheduleTodayCount: count('SELECT COUNT(*) AS n FROM schedules WHERE start_time LIKE ?', `${today}%`),
    simulationCount: count('SELECT COUNT(*) AS n FROM simulations'),
    materialCount: count('SELECT COUNT(*) AS n FROM materials'),
    customerTodayCount: count('SELECT COUNT(*) AS n FROM customers WHERE created_at LIKE ?', `${today}%`),
    totalExpectedAmount: db.prepare('SELECT COALESCE(SUM(expected_amount), 0) AS n FROM customers').get().n,
    totalIncome: db.prepare('SELECT COALESCE(SUM(monthly_income), 0) AS n FROM customers').get().n,
  }

  // 客户来源分布
  const sourceRows = db.prepare('SELECT source, COUNT(*) AS n FROM customers GROUP BY source').all()
  const sourceMap = {
    friend: '朋友介绍',
    telemarketing: '电话营销',
    walkin: '门店进件',
    online: '线上渠道',
    referral: '老客转介绍',
    other: '其他',
  }
  stats.customerSource = sourceRows.map((r) => ({
    key: r.source || 'other',
    name: sourceMap[r.source] || r.source || '其他',
    count: r.n,
  }))

  // 近 7 日新增客户趋势
  const trend = []
  for (let i = 6; i >= 0; i--) {
    const d = new Date(Date.now() - i * 86400000)
    const day = fmtDateTime(d).slice(0, 10)
    trend.push({
      date: day.slice(5), // MM-DD
      count: count('SELECT COUNT(*) AS n FROM customers WHERE created_at LIKE ?', `${day}%`),
    })
  }
  stats.customerTrend = trend

  // 客户风险分布（逾期/高负债/高查询 = 风险）
  stats.riskCount = count(
    'SELECT COUNT(*) AS n FROM customers WHERE max_overdue_months > 0 OR total_debt > 100000 OR query_count_3m > 8'
  )

  // 最近录入的 8 位客户
  stats.recentCustomers = db
    .prepare('SELECT id, name, gender, age, city, source, monthly_income, total_debt, created_at FROM customers ORDER BY created_at DESC LIMIT 8')
    .all()
    .map((r) => ({
      id: r.id,
      name: r.name,
      gender: r.gender,
      age: r.age,
      city: r.city,
      source: sourceMap[r.source] || r.source,
      monthlyIncome: r.monthly_income,
      totalDebt: r.total_debt,
      createdAt: r.created_at,
    }))

  ok(res, stats)
})

// ---------- 用户（贷款经理）管理 ----------

// 用户列表 + 业务量统计
router.get('/users', (req, res) => {
  const rows = db.prepare(`
    SELECT u.id, u.phone, u.name, u.role, u.created_at,
      (SELECT COUNT(*) FROM customers c WHERE c.user_id = u.id) AS customer_count,
      (SELECT COUNT(*) FROM products p WHERE p.user_id = u.id) AS product_count,
      (SELECT COUNT(*) FROM schedules s WHERE s.user_id = u.id) AS schedule_count,
      (SELECT COUNT(*) FROM simulations sim WHERE sim.user_id = u.id) AS simulation_count
    FROM users u ORDER BY u.created_at ASC
  `).all()
  ok(res, rows.map((r) => ({
    id: r.id,
    phone: r.phone,
    name: r.name,
    role: r.role === 'admin' ? '管理员' : '贷款经理',
    customerCount: r.customer_count,
    productCount: r.product_count,
    scheduleCount: r.schedule_count,
    simulationCount: r.simulation_count,
    createdAt: r.created_at,
  })))
})

// 新建用户
router.post('/users', (req, res) => {
  const { phone, name, password, role } = req.body || {}
  if (!/^1[3-9]\d{9}$/.test(phone || '')) throw new BizError('手机号格式不正确')
  if (!name?.trim()) throw new BizError('请填写姓名')
  if (!password || password.length < 6) throw new BizError('密码至少 6 位')

  const exists = db.prepare('SELECT id FROM users WHERE phone = ?').get(phone)
  if (exists) throw new BizError('该手机号已注册', 409)

  const hash = bcrypt.hashSync(password, 10)
  const info = db
    .prepare('INSERT INTO users (phone, password_hash, name, role, created_at) VALUES (?, ?, ?, ?, ?)')
    .run(phone, hash, name.trim(), role === 'admin' ? 'admin' : 'loan_manager', fmtDateTime())
  ok(res, { id: info.lastInsertRowid, phone, name: name.trim() })
})

// 重置密码
router.patch('/users/:id/password', (req, res) => {
  const { password } = req.body || {}
  if (!password || password.length < 6) throw new BizError('密码至少 6 位')
  const user = db.prepare('SELECT id FROM users WHERE id = ?').get(req.params.id)
  if (!user) throw new BizError('用户不存在', 404)
  db.prepare('UPDATE users SET password_hash = ? WHERE id = ?').run(bcrypt.hashSync(password, 10), req.params.id)
  ok(res, { id: Number(req.params.id) })
})

// 删除用户（不能删自己、不能删最后一个账号）
router.delete('/users/:id', (req, res) => {
  const id = Number(req.params.id)
  if (id === req.user.id) throw new BizError('不能删除当前登录账号')
  const user = db.prepare('SELECT id FROM users WHERE id = ?').get(id)
  if (!user) throw new BizError('用户不存在', 404)
  if (db.prepare('SELECT COUNT(*) AS n FROM users').get().n <= 1) throw new BizError('至少保留一个账号')
  db.prepare('DELETE FROM users WHERE id = ?').run(id)
  ok(res, { id })
})

export default router
