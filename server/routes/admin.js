// ==================== 管理后台路由（RBAC 保护） ====================
// 面向管理角色的聚合接口，每个端点都挂 requirePerm 权限校验
// 另含角色-权限矩阵维护、系统设置（脱敏开关）

import { Router } from 'express'
import bcrypt from 'bcryptjs'
import { db } from '../db.js'
import { ok, fail, genId, fmtDateTime, BizError } from '../utils.js'
import { requirePerm } from '../middleware/auth.js'
import { writeAudit } from '../audit.js'
import {
  PERMISSION_CATALOG,
  getRolePermissions,
  hasPerm,
  roleName,
  getSetting,
  setSetting,
  applyMasking,
} from '../rbac.js'

const router = Router()

const wrap = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next)

// ---------- 全局统计看板 ----------
// 权限分两层：
//   admin.dashboard.view   能进看板（管理员/主管/贷款经理）
//   admin.dashboard.global 能看全局经营数据与客户明细（管理员/主管）
// 贷款经理只拿到有限的个人视角数据（自己名下的客户/产品/日程计数），
// 全站用户数、全库收入负债合计、最近客户明细一律不下发，避免越权与 PII 泄露。
router.get('/stats', requirePerm('admin.dashboard.view'), (req, res) => {
  const count = (sql, ...args) => db.prepare(sql).get(...args).n
  const global = hasPerm(req.user.role, 'admin.dashboard.global')

  const today = fmtDateTime().slice(0, 10)
  const stats = {}

  if (global) {
    stats.userCount = count('SELECT COUNT(*) AS n FROM users')
    stats.customerCount = count('SELECT COUNT(*) AS n FROM customers')
    stats.productCount = count('SELECT COUNT(*) AS n FROM products')
    stats.productActiveCount = count("SELECT COUNT(*) AS n FROM products WHERE status = 'active'")
    stats.scheduleCount = count('SELECT COUNT(*) AS n FROM schedules')
    stats.scheduleTodayCount = count('SELECT COUNT(*) AS n FROM schedules WHERE start_time LIKE ?', `${today}%`)
    stats.simulationCount = count('SELECT COUNT(*) AS n FROM simulations')
    stats.materialCount = count('SELECT COUNT(*) AS n FROM materials')
    stats.customerTodayCount = count('SELECT COUNT(*) AS n FROM customers WHERE created_at LIKE ?', `${today}%`)
    stats.totalExpectedAmount = db.prepare('SELECT COALESCE(SUM(expected_amount), 0) AS n FROM customers').get().n
    stats.totalIncome = db.prepare('SELECT COALESCE(SUM(monthly_income), 0) AS n FROM customers').get().n
  } else {
    // 个人视角：仅统计本人数据
    const uid = req.user.id
    stats.userCount = null
    stats.customerCount = count('SELECT COUNT(*) AS n FROM customers WHERE user_id = ?', uid)
    stats.productCount = count('SELECT COUNT(*) AS n FROM products WHERE user_id = ?', uid)
    stats.productActiveCount = count("SELECT COUNT(*) AS n FROM products WHERE status = 'active' AND user_id = ?", uid)
    stats.scheduleCount = count('SELECT COUNT(*) AS n FROM schedules WHERE user_id = ?', uid)
    stats.scheduleTodayCount = count('SELECT COUNT(*) AS n FROM schedules WHERE user_id = ? AND start_time LIKE ?', uid, `${today}%`)
    stats.simulationCount = count('SELECT COUNT(*) AS n FROM simulations WHERE user_id = ?', uid)
    stats.materialCount = count(
      'SELECT COUNT(*) AS n FROM materials m JOIN customers c ON c.id = m.customer_id WHERE c.user_id = ?',
      uid
    )
    stats.customerTodayCount = count('SELECT COUNT(*) AS n FROM customers WHERE user_id = ? AND created_at LIKE ?', uid, `${today}%`)
    stats.totalExpectedAmount = db.prepare('SELECT COALESCE(SUM(expected_amount), 0) AS n FROM customers WHERE user_id = ?').get(uid).n
    stats.totalIncome = db.prepare('SELECT COALESCE(SUM(monthly_income), 0) AS n FROM customers WHERE user_id = ?').get(uid).n
  }

  // 客户来源分布
  const sourceRows = global
    ? db.prepare('SELECT source, COUNT(*) AS n FROM customers GROUP BY source').all()
    : db.prepare('SELECT source, COUNT(*) AS n FROM customers WHERE user_id = ? GROUP BY source').all(req.user.id)
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
      date: day.slice(5),
      count: global
        ? count('SELECT COUNT(*) AS n FROM customers WHERE created_at LIKE ?', `${day}%`)
        : count('SELECT COUNT(*) AS n FROM customers WHERE user_id = ? AND created_at LIKE ?', req.user.id, `${day}%`),
    })
  }
  stats.customerTrend = trend

  stats.riskCount = global
    ? count(
        'SELECT COUNT(*) AS n FROM customers WHERE max_overdue_months > 0 OR total_debt > 100000 OR query_count_3m > 8'
      )
    : count(
        'SELECT COUNT(*) AS n FROM customers WHERE user_id = ? AND (max_overdue_months > 0 OR total_debt > 100000 OR query_count_3m > 8)',
        req.user.id
      )

  // 最近录入的 8 位客户：仅全局视角下发，且必须走脱敏（无 customers.unmasked 的角色看到掩码）
  if (global) {
    stats.recentCustomers = db
      .prepare('SELECT id, user_id, name, phone, id_card, gender, age, city, source, monthly_income, total_debt, created_at FROM customers ORDER BY created_at DESC LIMIT 8')
      .all()
      .map((r) => {
        // 复用统一的脱敏规则：开关 ON 且无 customers.unmasked 时掩码手机号 / 身份证
        const masked = applyMasking({ phone: r.phone, idCard: r.id_card }, req.user.role)
        return {
          id: r.id,
          name: r.name,
          gender: r.gender,
          age: r.age,
          city: r.city,
          source: sourceMap[r.source] || r.source,
          monthlyIncome: r.monthly_income,
          totalDebt: r.total_debt,
          createdAt: r.created_at,
        }
      })
  } else {
    stats.recentCustomers = []
  }

  ok(res, stats)
})

// ---------- 用户（贷款经理）管理 ----------

router.get('/users', requirePerm('admin.users.view'), (req, res) => {
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
    phone: r.phone, // 管理后台用户手机号同样遵守脱敏开关
    name: r.name,
    role: r.role,
    roleName: roleName(r.role),
    customerCount: r.customer_count,
    productCount: r.product_count,
    scheduleCount: r.schedule_count,
    simulationCount: r.simulation_count,
    createdAt: r.created_at,
  })))
})

router.post('/users', requirePerm('admin.users.manage'), (req, res) => {
  const { phone, name, password, role } = req.body || {}
  if (!/^1[3-9]\d{9}$/.test(phone || '')) throw new BizError('手机号格式不正确')
  if (!name?.trim()) throw new BizError('请填写姓名')
  if (!password || password.length < 6) throw new BizError('密码至少 6 位')

  if (!db.prepare('SELECT 1 FROM roles WHERE code = ?').get(role || '')) {
    throw new BizError('角色不存在')
  }
  const exists = db.prepare('SELECT id FROM users WHERE phone = ?').get(phone)
  if (exists) throw new BizError('该手机号已注册', 409)

  const hash = bcrypt.hashSync(password, 10)
  const info = db
    .prepare('INSERT INTO users (phone, password_hash, name, role, created_at) VALUES (?, ?, ?, ?, ?)')
    .run(phone, hash, name.trim(), role, fmtDateTime())
  writeAudit(req, 'user.create', `${name.trim()}（${phone}）`, `角色：${roleName(role)}`)
  ok(res, { id: info.lastInsertRowid, phone, name: name.trim(), role })
})

// 调整用户角色
router.patch('/users/:id/role', requirePerm('admin.users.manage'), wrap(async (req, res) => {
  const { role } = req.body || {}
  if (!db.prepare('SELECT 1 FROM roles WHERE code = ?').get(role || '')) throw new BizError('角色不存在')
  const user = db.prepare('SELECT id, name, role FROM users WHERE id = ?').get(req.params.id)
  if (!user) throw new BizError('用户不存在', 404)

  // 防呆：不能把最后一个管理员改成非管理员
  if (
    req.user.id === user.id && req.user.role === 'admin' && role !== 'admin' &&
    db.prepare("SELECT COUNT(*) AS n FROM users WHERE role = 'admin'").get().n <= 1
  ) {
    throw new BizError('至少保留一个管理员账号')
  }
  // 角色变更即时生效：token_version +1 让该用户旧 token 立即失效，需重新登录
  db.prepare('UPDATE users SET role = ?, token_version = token_version + 1 WHERE id = ?').run(role, req.params.id)
  writeAudit(req, 'user.role_change', `${user.name}（ID ${user.id}）`, `角色 ${user.role} → ${role}`)
  ok(res, { id: Number(req.params.id), role })
}))

router.patch('/users/:id/password', requirePerm('admin.users.manage'), (req, res) => {
  const { password } = req.body || {}
  if (!password || password.length < 6) throw new BizError('密码至少 6 位')
  const user = db.prepare('SELECT id, name FROM users WHERE id = ?').get(req.params.id)
  if (!user) throw new BizError('用户不存在', 404)
  db.prepare('UPDATE users SET password_hash = ?, token_version = token_version + 1 WHERE id = ?').run(bcrypt.hashSync(password, 10), req.params.id)
  writeAudit(req, 'user.password_reset', `${user.name}（ID ${user.id}）`)
  ok(res, { id: Number(req.params.id) })
})

router.delete('/users/:id', requirePerm('admin.users.manage'), (req, res) => {
  const id = Number(req.params.id)
  if (id === req.user.id) throw new BizError('不能删除当前登录账号')
  const user = db.prepare('SELECT id, name, phone, role FROM users WHERE id = ?').get(id)
  if (!user) throw new BizError('用户不存在', 404)
  if (db.prepare('SELECT COUNT(*) AS n FROM users').get().n <= 1) throw new BizError('至少保留一个账号')
  if (user.role === 'admin' && db.prepare("SELECT COUNT(*) AS n FROM users WHERE role = 'admin'").get().n <= 1) {
    throw new BizError('至少保留一个管理员账号')
  }
  db.prepare('DELETE FROM users WHERE id = ?').run(id)
  writeAudit(req, 'user.delete', `${user.name}（${user.phone}）`)
  ok(res, { id })
})

// ---------- RBAC：角色与权限矩阵 ----------

// 权限目录
router.get('/permissions', requirePerm('admin.roles.manage'), (req, res) => {
  ok(res, PERMISSION_CATALOG)
})

// 角色简表（code/name/description，不含权限矩阵）
// 供用户管理页的角色下拉使用，只需 admin.users.manage 即可
router.get('/role-options', requirePerm('admin.users.manage'), (req, res) => {
  ok(res, db.prepare('SELECT code, name, description, sort FROM roles ORDER BY sort ASC').all())
})

// ---------- 角色列表 ----------
// 完整角色-权限矩阵：仅授予 admin.roles.manage 的角色可读（与 PUT /roles/:code/permissions 对称）
// 否则任何登录用户都能拿到全量权限矩阵，为提权尝试提供地图
router.get('/roles', requirePerm('admin.roles.manage'), (req, res) => {
  const roles = db.prepare('SELECT code, name, description, sort FROM roles ORDER BY sort ASC').all()
  ok(res, roles.map((r) => ({ ...r, permissions: getRolePermissions(r.code), userLabel: r.name })))
})

// 更新某角色的权限集合
router.put('/roles/:code/permissions', requirePerm('admin.roles.manage'), wrap(async (req, res) => {
  const { permissionCodes } = req.body || {}
  if (!Array.isArray(permissionCodes)) throw new BizError('permissionCodes 必须为数组')

  const validCodes = new Set(PERMISSION_CATALOG.map((p) => p.code))
  for (const c of permissionCodes) {
    if (!validCodes.has(c)) throw new BizError(`未知权限码：${c}`)
  }

  // 防呆：不允许把 admin 的全部权限清空（避免自锁在门外）
  if (req.params.code === 'admin' && permissionCodes.length === 0) {
    throw new BizError('不能移除管理员的全部权限')
  }

  const tx = db.transaction(() => {
    db.prepare('DELETE FROM role_permissions WHERE role_code = ?').run(req.params.code)
    const ins = db.prepare('INSERT INTO role_permissions (role_code, permission_code) VALUES (?, ?)')
    for (const c of permissionCodes) ins.run(req.params.code, c)
  })
  tx()
  writeAudit(req, 'role.perms_update', `角色 ${req.params.code}`, `授权 ${permissionCodes.length} 项：${permissionCodes.join('、')}`)
  ok(res, { roleCode: req.params.code, permissionCodes })
}))

// ---------- 系统设置（脱敏开关等） ----------

router.get('/settings', requirePerm('admin.settings.manage'), (req, res) => {
  ok(res, {
    maskSensitive: getSetting('mask_sensitive', 'on') === 'on',
    maskedPhoneVisibleChars: Number(getSetting('masked_phone_visible_chars', '3')),
  })
})

router.put('/settings', requirePerm('admin.settings.manage'), wrap(async (req, res) => {
  const { maskSensitive, maskedPhoneVisibleChars } = req.body || {}
  const changes = []
  if (typeof maskSensitive === 'boolean') {
    setSetting('mask_sensitive', maskSensitive ? 'on' : 'off')
    changes.push(`脱敏开关 → ${maskSensitive ? '开' : '关'}`)
  }
  if (Number.isInteger(maskedPhoneVisibleChars) && maskedPhoneVisibleChars >= 0 && maskedPhoneVisibleChars <= 7) {
    setSetting('masked_phone_visible_chars', String(maskedPhoneVisibleChars))
    changes.push(`明文保留位数 → ${maskedPhoneVisibleChars}`)
  }
  if (changes.length) writeAudit(req, 'settings.update', '系统设置', changes.join('；'))
  ok(res, {
    maskSensitive: getSetting('mask_sensitive', 'on') === 'on',
    maskedPhoneVisibleChars: Number(getSetting('masked_phone_visible_chars', '3')),
  })
}))

// 当前脱敏状态（任何登录者可查，用于前端展示徽标）
router.get('/mask-status', (req, res) => {
  ok(res, {
    maskOn: getSetting('mask_sensitive', 'on') === 'on',
    canSeeRaw: hasPerm(req.user.role, 'customers.unmasked'),
  })
})

// ---------- 操作审计日志 ----------
// 仅授予 admin.audit.view 的角色可看；支持按动作码过滤 + 条数限制
router.get('/audit-logs', requirePerm('admin.audit.view'), (req, res) => {
  const limit = Math.min(Number(req.query.limit) || 100, 500)
  const action = (req.query.action || '').trim()

  let rows
  if (action) {
    rows = db.prepare('SELECT * FROM audit_logs WHERE action = ? ORDER BY id DESC LIMIT ?').all(action, limit)
  } else {
    rows = db.prepare('SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?').all(limit)
  }
  ok(res, rows.map((r) => ({
    id: r.id,
    userId: r.user_id,
    userName: r.user_name,
    action: r.action,
    target: r.target,
    detail: r.detail,
    ip: r.ip,
    createdAt: r.created_at,
  })))
})

export default router
