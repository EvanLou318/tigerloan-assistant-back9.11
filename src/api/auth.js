// ==================== 认证 API ====================

import request from './index'

export function loginApi(data) {
  return request.post('/auth/login', data)
}

export function changePasswordApi(data) {
  return request.post('/auth/change-password', data)
}

export function getMe() {
  return request.get('/auth/me')
}

// 上传自定义头像（FormData，后端字段名为 file）
export function uploadAvatar(file) {
  const fd = new FormData()
  fd.append('file', file)
  return request.post('/auth/avatar', fd)
}

// 恢复默认头像
export function removeAvatar() {
  return request.delete('/auth/avatar')
}
