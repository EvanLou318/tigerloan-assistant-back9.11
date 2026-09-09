// ==================== 操作审计 ====================
// 敏感操作统一留痕：谁、什么时间、对什么对象、做了什么。
// 写入失败不影响主流程（审计是旁路，不应拖垮业务接口）。

import { db } from './db.js'
import { fmtDateTime } from './utils.js'

/**
 * @param {object} req Express 请求（取已登录用户与 IP）
 * @param {string} action 动作码，如 user.create / role.perms_update
 * @param {string} target 操作对象简述
 * @param {string} [detail] 补充说明（不要写入密码/Key 等敏感明文）
 */
export function writeAudit(req, action, target = '', detail = '') {
  try {
    const user = req.user || {}
    const ip =
      req.headers['x-forwarded-for']?.split(',')[0]?.trim() ||
      req.socket?.remoteAddress ||
      ''
    db.prepare(
      `INSERT INTO audit_logs (user_id, user_name, action, target, detail, ip, created_at)
       VALUES (?, ?, ?, ?, ?, ?, ?)`
    ).run(user.id || 0, user.name || '', action, String(target).slice(0, 200), String(detail).slice(0, 500), ip, fmtDateTime())
  } catch (e) {
    console.error('[audit] 写入失败:', e.message)
  }
}

// 动作码 → 展示名（前端下拉/表格共用）
export const AUDIT_ACTION_LABELS = {
  'user.create': '创建用户',
  'user.role_change': '调整用户角色',
  'user.password_reset': '重置用户密码',
  'user.delete': '删除用户',
  'role.perms_update': '更新角色权限',
  'settings.update': '修改系统设置',
  'service.create': '新增三方服务供应商',
  'service.update': '更新三方服务供应商',
  'service.delete': '删除三方服务供应商',
  'service.default': '切换默认供应商',
  'customer.delete': '删除客户档案',
}
