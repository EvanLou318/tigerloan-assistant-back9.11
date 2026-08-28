// ==================== RBAC 角色权限模型 ====================
// user --(users.role)--> roles.code --> role_permissions --> permissions
// 另含系统设置（settings）与敏感字段脱敏工具

import { db } from './db.js'

// ---------- 权限目录（按模块分组） ----------
export const PERMISSION_CATALOG = [
  { code: 'admin.dashboard.view', name: '查看数据看板', module: '数据看板' },
  { code: 'admin.customers.view', name: '查看客户列表', module: '客户管理' },
  { code: 'admin.customers.delete', name: '删除客户档案', module: '客户管理' },
  { code: 'customers.unmasked', name: '查看敏感字段明文', module: '客户管理' },
  { code: 'admin.products.view', name: '查看产品列表', module: '产品管理' },
  { code: 'admin.products.manage', name: '启停/删除产品', module: '产品管理' },
  { code: 'admin.schedules.view', name: '查看日程列表', module: '日程管理' },
  { code: 'admin.schedules.manage', name: '管理日程（完成/删除）', module: '日程管理' },
  { code: 'admin.users.view', name: '查看用户列表', module: '用户与安全' },
  { code: 'admin.users.manage', name: '用户管理（创建/改角色/重置密码/删除）', module: '用户与安全' },
  { code: 'admin.roles.manage', name: '配置角色权限', module: '用户与安全' },
  { code: 'admin.settings.manage', name: '修改系统设置（脱敏开关）', module: '用户与安全' },
  { code: 'admin.services.view', name: '查看三方服务配置', module: '三方服务' },
  { code: 'admin.services.manage', name: '管理三方服务（增删改/启停/设默认/连通测试）', module: '三方服务' },
]

// ---------- 角色定义与默认授权 ----------
const ROLE_DEFS = [
  {
    code: 'admin',
    name: '管理员',
    description: '拥有全部权限，包括角色配置与系统设置',
    sort: 1,
    perms: PERMISSION_CATALOG.map((p) => p.code),
  },
  {
    code: 'supervisor',
    name: '团队主管',
    description: '查看全局数据与客户，可管理日程，不可配置系统',
    sort: 2,
    perms: [
      'admin.dashboard.view',
      'admin.customers.view',
      'customers.unmasked',
      'admin.products.view',
      'admin.schedules.view',
      'admin.schedules.manage',
      'admin.users.view',
    ],
  },
  {
    code: 'loan_manager',
    name: '贷款经理',
    description: '移动端展业为主，后台仅可查看基础业务数据，敏感字段脱敏',
    sort: 3,
    perms: [
      'admin.dashboard.view',
      'admin.customers.view',
      'admin.products.view',
      'admin.schedules.view',
    ],
  },
]

// ---------- 种子：增量写入（旧库升级安全） ----------
export function ensureRBACSeed() {
  const insRole = db.prepare('INSERT OR IGNORE INTO roles (code, name, description, sort) VALUES (?, ?, ?, ?)')
  const insPerm = db.prepare('INSERT OR IGNORE INTO permissions (code, name, module) VALUES (?, ?, ?)')
  const insRP = db.prepare('INSERT OR IGNORE INTO role_permissions (role_code, permission_code) VALUES (?, ?)')
  const insSetting = db.prepare('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)')

  for (const r of ROLE_DEFS) {
    insRole.run(r.code, r.name, r.description, r.sort)
  }
  for (const p of PERMISSION_CATALOG) {
    insPerm.run(p.code, p.name, p.module)
  }
  for (const r of ROLE_DEFS) {
    for (const c of r.perms) insRP.run(r.code, c)
  }

  // 系统设置默认值：敏感字段脱敏开启
  insSetting.run('mask_sensitive', 'on')
  insSetting.run('masked_phone_visible_chars', '3') // 明文保留前3位

  // 历史库迁移：保证至少有一个管理员（否则没人能进权限矩阵，自锁）
  // 1) 没有任何 admin 时，将第一个用户升为管理员
  // 2) 库里只有一个用户且角色不在角色目录中（旧版自由文本角色）时，同样升为管理员
  const adminCount = db.prepare("SELECT COUNT(*) AS n FROM users WHERE role = 'admin'").get().n
  if (adminCount === 0) {
    db.prepare("UPDATE users SET role = 'admin' WHERE id = (SELECT MIN(id) FROM users)")
  }
  const userCount = db.prepare('SELECT COUNT(*) AS n FROM users').get().n
  if (userCount === 1) {
    const only = db.prepare('SELECT role FROM users LIMIT 1').get()
    if (!only || !ROLE_DEFS.some((r) => r.code === only.role)) {
      db.prepare("UPDATE users SET role = 'admin'")
    }
  }
}

// ---------- 权限查询 ----------
export function getRolePermissions(roleCode) {
  return db
    .prepare('SELECT permission_code FROM role_permissions WHERE role_code = ?')
    .all(roleCode)
    .map((r) => r.permission_code)
}

export function hasPerm(roleCode, permCode) {
  return !!db
    .prepare('SELECT 1 FROM role_permissions WHERE role_code = ? AND permission_code = ?')
    .get(roleCode, permCode)
}

export function roleName(roleCode) {
  const r = db.prepare('SELECT name FROM roles WHERE code = ?').get(roleCode)
  return r?.name || roleCode
}

// ---------- 设置读写 ----------
export function getSetting(key, fallback = null) {
  const row = db.prepare('SELECT value FROM settings WHERE key = ?').get(key)
  return row?.value ?? fallback
}

export function setSetting(key, value) {
  db.prepare(
    'INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value'
  ).run(key, String(value))
}

// ---------- 敏感字段脱敏 ----------
// 脱敏开关 ON 且用户无 customers.unmasked 权限时生效；返回新对象不改动原数据
export function applyMasking(customerObj, roleCode) {
  if (getSetting('mask_sensitive', 'on') !== 'on') return customerObj
  if (hasPerm(roleCode, 'customers.unmasked')) return customerObj

  const keep = Number(getSetting('masked_phone_visible_chars', '3')) || 3
  const out = { ...customerObj }
  if (out.phone && !out.phone.includes('*')) {
    out.phone = out.phone.slice(0, keep).padEnd(Math.min(out.phone.length, keep + 4), '*')
  }
  if (out.idCard && out.idCard.length >= 10) {
    out.idCard = out.idCard.slice(0, 4) + '**********' + out.idCard.slice(-4)
  }
  return out
}
