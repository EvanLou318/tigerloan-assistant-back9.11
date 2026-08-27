// ==================== 管理后台 API ====================

import request from './index'

// 全局统计看板
export function fetchAdminStats() {
  return request.get('/admin/stats')
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
