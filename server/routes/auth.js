// ==================== 认证路由 ====================

import { Router } from 'express'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import bcrypt from 'bcryptjs'
import jwt from 'jsonwebtoken'
import multer from 'multer'
import { db } from '../db.js'
import { config } from '../config.js'
import { ok, fail, genId } from '../utils.js'
import { authRequired } from '../middleware/auth.js'
import { getRolePermissions, roleName } from '../rbac.js'

const router = Router()

// ---------- 头像上传配置 ----------
const UPLOAD_DIR = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'uploads')
fs.mkdirSync(UPLOAD_DIR, { recursive: true })

// MIME → 规范后缀，只走白名单映射，不回退信任客户端文件名（防止 avatar_x.html 之类落盘后被直链执行）
const AVATAR_EXT = { 'image/jpeg': '.jpg', 'image/png': '.png', 'image/webp': '.webp', 'image/gif': '.gif' }

const avatarUpload = multer({
  storage: multer.diskStorage({
    destination: (req, file, cb) => cb(null, UPLOAD_DIR),
    filename: (req, file, cb) => {
      const ext = AVATAR_EXT[file.mimetype] || '.jpg'
      cb(null, `avatar_${req.user?.id || 'u'}_${genId('')}${ext}`)
    },
  }),
  limits: { fileSize: 5 * 1024 * 1024, files: 1 }, // 5MB
  fileFilter: (req, file, cb) => {
    if (!AVATAR_EXT[file.mimetype]) return cb(new Error('仅支持上传 jpg / png / webp / gif 图片'))
    cb(null, true)
  },
})

// ---------- 登录限流（内存计数：同 手机号+IP 10 分钟内最多 5 次失败） ----------
const LOGIN_WINDOW = 10 * 60 * 1000
const LOGIN_MAX_FAILS = 5
const loginFails = new Map()

function loginBlocked(key) {
  const rec = loginFails.get(key)
  return rec && rec.count >= LOGIN_MAX_FAILS && Date.now() - rec.first < LOGIN_WINDOW
}

function recordLoginFail(key) {
  const now = Date.now()
  const rec = loginFails.get(key)
  if (rec && now - rec.first < LOGIN_WINDOW) {
    rec.count += 1
  } else {
    loginFails.set(key, { first: now, count: 1 })
  }
  // 防止 Map 无限增长：过期记录超阈值时整体清理一次
  if (loginFails.size > 500) {
    for (const [k, v] of loginFails) {
      if (now - v.first >= LOGIN_WINDOW) loginFails.delete(k)
    }
  }
}

// POST /api/auth/login  登录
router.post('/login', (req, res) => {
  const { phone, password } = req.body || {}
  if (!phone || !password) return fail(res, 400, '请输入手机号和密码')

  const failKey = `${phone}|${req.socket?.remoteAddress || ''}`
  if (loginBlocked(failKey)) {
    return fail(res, 429, '尝试次数过多，请 10 分钟后再试')
  }

  // 「账号不存在」与「密码错误」统一文案：避免泄露手机号是否已注册
  const user = db.prepare('SELECT * FROM users WHERE phone = ?').get(phone)
  if (!user || !bcrypt.compareSync(password, user.password_hash)) {
    recordLoginFail(failKey)
    return fail(res, 400, '手机号或密码错误')
  }
  loginFails.delete(failKey)

  const token = jwt.sign(
    { id: user.id, phone: user.phone, name: user.name, role: user.role, tv: user.token_version || 0 },
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
      avatar: user.avatar || '',
      loginTime: new Date().toLocaleString('zh-CN'),
    },
  })
})

// POST /api/auth/avatar  上传自定义头像（需登录）
router.post('/avatar', authRequired, (req, res) => {
  avatarUpload.single('file')(req, res, (err) => {
    if (err) {
      const msg = err instanceof multer.MulterError
        ? (err.code === 'LIMIT_FILE_SIZE' ? '图片不能超过 5MB' : '上传失败，请重试')
        : (err.message || '上传失败，请重试')
      return fail(res, 400, msg)
    }
    if (!req.file) return fail(res, 400, '请选择要上传的图片')

    const url = `/uploads/${req.file.filename}`
    // 清掉上一张旧头像，避免 uploads 目录无限增长
    const old = db.prepare('SELECT avatar FROM users WHERE id = ?').get(req.user.id)
    if (old?.avatar && old.avatar.startsWith('/uploads/avatar_')) {
      const oldPath = path.join(UPLOAD_DIR, path.basename(old.avatar))
      fs.promises.unlink(oldPath).catch(() => {})
    }
    db.prepare('UPDATE users SET avatar = ? WHERE id = ?').run(url, req.user.id)
    ok(res, { avatar: url })
  })
})

// DELETE /api/auth/avatar  恢复默认头像（需登录）
router.delete('/avatar', authRequired, (req, res) => {
  const old = db.prepare('SELECT avatar FROM users WHERE id = ?').get(req.user.id)
  if (old?.avatar && old.avatar.startsWith('/uploads/avatar_')) {
    const oldPath = path.join(UPLOAD_DIR, path.basename(old.avatar))
    fs.promises.unlink(oldPath).catch(() => {})
  }
  db.prepare("UPDATE users SET avatar = '' WHERE id = ?").run(req.user.id)
  ok(res, { avatar: '' })
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

  db.prepare('UPDATE users SET password_hash = ?, token_version = token_version + 1 WHERE id = ?')
    .run(bcrypt.hashSync(newPassword, 10), user.id)
  ok(res, { changed: true, relogin: true })
})

// GET /api/auth/me  当前用户信息（需登录）
router.get('/me', authRequired, (req, res) => {
  const user = db.prepare('SELECT id, phone, name, role, avatar, created_at FROM users WHERE id = ?').get(req.user.id)
  if (!user) return fail(res, 401, '用户不存在')
  ok(res, {
    id: user.id,
    phone: user.phone,
    name: user.name,
    role: user.role,
    roleName: roleName(user.role),
    permissions: getRolePermissions(user.role),
    avatar: user.avatar || '',
  })
})

export default router
