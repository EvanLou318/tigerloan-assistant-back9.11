// ==================== JWT 鉴权中间件 ====================

import jwt from 'jsonwebtoken'
import { config } from '../config.js'
import { fail } from '../utils.js'
import { hasPerm } from '../rbac.js'

export function authRequired(req, res, next) {
  // 优先读自定义头 X-Auth-Token：部署平台的网关会覆盖标准 Authorization 头
  // （替换成平台自己的 JWT），直接读它会导致「登录成功即掉线」。
  // 其次回退到 Authorization，并用正则精确提取 JWT，忽略网关追加的内容。
  const custom = String(req.headers['x-auth-token'] || '').trim()
  const header = String(req.headers.authorization || '')
  const m = header.match(/Bearer\s+([A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]*)/)
  const token = custom || (m ? m[1] : null)
  if (!token) return fail(res, 401, '未登录，请先登录')
  try {
    req.user = jwt.verify(token, config.jwtSecret)
    next()
  } catch (err) {
    console.warn('[auth] token verify failed:', err?.name)
    return fail(res, 401, '登录已过期，请重新登录')
  }
}

// RBAC 权限校验：挂在 authRequired 之后使用
export function requirePerm(permCode) {
  return (req, res, next) => {
    if (hasPerm(req.user.role, permCode)) return next()
    return fail(res, 403, `无权限：缺少「${permCode}」授权`)
  }
}
