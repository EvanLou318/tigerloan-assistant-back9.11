// ==================== 认证路由 ====================

import { Router } from 'express'
import bcrypt from 'bcryptjs'
import jwt from 'jsonwebtoken'
import { db } from '../db.js'
import { config } from '../config.js'
import { ok, fail } from '../utils.js'
import { authRequired } from '../middleware/auth.js'
import { getRolePermissions, roleName } from '../rbac.js'

const router = Router()

// POST /api/auth/login  登录
router.post('/login', (req, res) => {
  const { phone, password } = req.body || {}
  if (!phone || !password) return fail(res, 400, '请输入手机号和密码')

  const user = db.prepare('SELECT * FROM users WHERE phone = ?').get(phone)
  if (!user) return fail(res, 400, '账号不存在')
  if (!bcrypt.compareSync(password, user.password_hash)) {
    return fail(res, 400, '密码错误，请重试')
  }

  const token = jwt.sign(
    { id: user.id, phone: user.phone, name: user.name, role: user.role },
    config.jwtSecret,
    { expiresIn: config.jwtExpires }
  )

  ok(res, {
    token,
    user: {
      id: user.id,
      phone: user.phone,
      name: user.name,
      role: user.role,
      roleName: roleName(user.role),
      permissions: getRolePermissions(user.role),
      loginTime: new Date().toLocaleString('zh-CN'),
    },
  })
})

// POST /api/auth/change-password  修改密码（需登录）
router.post('/change-password', authRequired, (req, res) => {
  const { oldPassword, newPassword } = req.body || {}
  if (!oldPassword || !newPassword) return fail(res, 400, '请填写原密码和新密码')
  if (newPassword.length < 6 || newPassword.length > 20 ||
      /^\d+$/.test(newPassword) || /^[a-zA-Z]+$/.test(newPassword)) {
    return fail(res, 400, '新密码6-20位，不能为纯数字或纯字母')
  }
  if (oldPassword === newPassword) return fail(res, 400, '新密码不能与当前密码相同')

  const user = db.prepare('SELECT * FROM users WHERE id = ?').get(req.user.id)
  if (!user) return fail(res, 401, '用户不存在')
  if (!bcrypt.compareSync(oldPassword, user.password_hash)) {
    return fail(res, 400, '原密码错误')
  }

  db.prepare('UPDATE users SET password_hash = ? WHERE id = ?')
    .run(bcrypt.hashSync(newPassword, 10), user.id)
  ok(res, { changed: true })
})

// GET /api/auth/me  当前用户信息（需登录）
router.get('/me', authRequired, (req, res) => {
  const user = db.prepare('SELECT id, phone, name, role, created_at FROM users WHERE id = ?').get(req.user.id)
  if (!user) return fail(res, 401, '用户不存在')
  ok(res, {
    id: user.id,
    phone: user.phone,
    name: user.name,
    role: user.role,
    roleName: roleName(user.role),
    permissions: getRolePermissions(user.role),
  })
})

export default router
