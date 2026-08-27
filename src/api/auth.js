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
