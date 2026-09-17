// ==================== JWT 鉴权中间件 ====================

import jwt from 'jsonwebtoken'
import { config } from '../config.js'
import { db } from '../db.js'
import { fail } from '../utils.js'
import { hasPerm } from '../rbac.js'

/**
 * 从请求中提取并校验 token：
 *   1) 自定义头 X-Auth-Token（部署平台网关会覆盖标准 Authorization 头，
 *      直接读它会导致「登录成功即掉线」）
 *   2) Authorization 头（正则精确提取 JWT，忽略网关追加的内容）
 *   3) ?token= 查询参数（仅用于 <img> 等无法携带请求头的资源直链，如 /uploads）
 * 校验通过后再查库确认用户仍存在且 token_version 未被吊销
 * （改密/改角色会 +1，删用户记录消失——旧 token 一律失效）。
 *
 * @returns {object|null} payload 或 null
 */
export function resolveUser(req) {
  const custom = String(req.headers['x-auth-token'] || '').trim()
  const header = String(req.headers.authorization || '')
  const m = header.match(/Bearer\s+([A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]*)/)
  const queryToken = String(req.query?.token || '').trim()
  const token = custom || (m ? m[1] : null) || queryToken
  if (!token) return null
  try {
    const payload = jwt.verify(token, config.jwtSecret)
    const row = db.prepare('SELECT id, token_version FROM users WHERE id = ?').get(payload.id)
    if (!row) return null
    if ((row.token_version || 0) !== (payload.tv || 0)) return null
    return payload
  } catch {
    return null
  }
}

export function authRequired(req, res, next) {
  const payload = resolveUser(req)
  if (!payload) {
    // 区分「没带凭证」与「凭证失效」，提示更明确
    const hasCred = req.headers['x-auth-token'] || req.headers.authorization || req.query?.token
    return fail(res, 401, hasCred ? '登录状态已失效，请重新登录' : '未登录，请先登录')
  }
  req.user = payload
  next()
}

// RBAC 权限校验：挂在 authRequired 之后使用
export function requirePerm(permCode) {
  return (req, res, next) => {
    if (hasPerm(req.user.role, permCode)) return next()
    return fail(res, 403, `无权限：缺少「${permCode}」授权`)
  }
}
