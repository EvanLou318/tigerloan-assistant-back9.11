// ==================== 客户360 API ====================

import request from './index'

export function fetchCustomers() {
  return request.get('/customers')
}

export function fetchCustomer(id) {
  return request.get(`/customers/${id}`)
}

export function createCustomer(data) {
  return request.post('/customers', data)
}

export function updateCustomer(id, data) {
  return request.put(`/customers/${id}`, data)
}

export function deleteCustomer(id) {
  return request.delete(`/customers/${id}`)
}

// ---------- 材料 ----------

export function addMaterial(customerId, data) {
  return request.post(`/customers/${customerId}/materials`, data)
}

export function updateMaterial(customerId, materialId, data) {
  return request.put(`/customers/${customerId}/materials/${materialId}`, data)
}

export function removeMaterial(customerId, materialId) {
  return request.delete(`/customers/${customerId}/materials/${materialId}`)
}

// ---------- 推演记录 ----------

export function fetchSimulations(customerId) {
  return request.get(`/customers/${customerId}/simulations`)
}

export function createSimulation(customerId, data) {
  return request.post(`/customers/${customerId}/simulations`, data)
}

export function deleteSimulation(customerId, simulationId) {
  return request.delete(`/customers/${customerId}/simulations/${simulationId}`)
}
