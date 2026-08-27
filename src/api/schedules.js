// ==================== 日程 API ====================

import request from './index'

export function fetchSchedules() {
  return request.get('/schedules')
}

export function createSchedule(data) {
  return request.post('/schedules', data)
}

export function updateSchedule(id, data) {
  return request.patch(`/schedules/${id}`, data)
}

export function deleteSchedule(id) {
  return request.delete(`/schedules/${id}`)
}
