// ==================== 管理后台 API ====================

import request from './index'

// 全局统计看板
export function fetchAdminStats() {
  return request.get('/admin/stats')
}

// ---------- RBAC 角色权限 ----------
export function fetchPermissions() {
  return request.get('/admin/permissions')
}

export function fetchRoles() {
  return request.get('/admin/roles')
}

export function updateRolePermissions(roleCode, permissionCodes) {
  return request.put(`/admin/roles/${roleCode}/permissions`, { permissionCodes })
}

// 调整用户角色
export function updateUserRole(id, role) {
  return request.patch(`/admin/users/${id}/role`, { role })
}

// ---------- 系统设置（脱敏开关） ----------
export function fetchSettings() {
  return request.get('/admin/settings')
}

export function updateSettings(data) {
  return request.put('/admin/settings', data)
}

// 当前脱敏状态（任何登录者可查）
export function fetchMaskStatus() {
  return request.get('/admin/mask-status')
}

// ---------- 用户管理 ----------
export function fetchAdminUsers() {
  return request.get('/admin/users')
}

export function createAdminUser(data) {
  return request.post('/admin/users', data)
}

export function resetUserPassword(id, password) {
  return request.patch(`/admin/users/${id}/password`, { password })
}

export function deleteAdminUser(id) {
  return request.delete(`/admin/users/${id}`)
}

// ---------- 操作审计日志 ----------
export function fetchAuditLogs(limit = 100, action = '') {
  return request.get('/admin/audit-logs', { params: { limit, action: action || undefined } })
}

// ---------- 三方服务供应商管理 ----------
export function fetchServiceGroups() {
  return request.get('/services')
}

export function createServiceProvider(data) {
  return request.post('/services', data)
}

export function updateServiceProvider(id, data) {
  return request.put(`/services/${id}`, data)
}

export function setServiceDefault(id) {
  return request.post(`/services/${id}/default`)
}

export function deleteServiceProvider(id) {
  return request.delete(`/services/${id}`)
}

export function testServiceProvider(id) {
  return request.post(`/services/${id}/test`)
}
