// ==================== 仪表盘 API ====================

import request from './index'

export function fetchDashboard() {
  return request.get('/dashboard')
}
