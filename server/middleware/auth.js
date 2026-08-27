// ==================== JWT 鉴权中间件 ====================

import jwt from 'jsonwebtoken'
import { config } from '../config.js'
import { fail } from '../utils.js'

export function authRequired(req, res, next) {
  const header = req.headers.authorization || ''
  const token = header.startsWith('Bearer ') ? header.slice(7) : null
  if (!token) return fail(res, 401, '未登录，请先登录')
  try {
    req.user = jwt.verify(token, config.jwtSecret)
    next()
  } catch {
    return fail(res, 401, '登录已过期，请重新登录')
  }
}
