// ==================== 产品库 API ====================

import request from './index'

export function fetchProducts() {
  return request.get('/products')
}

export function fetchProduct(id) {
  return request.get(`/products/${id}`)
}

export function createProduct(data) {
  return request.post('/products', data)
}

export function updateProduct(id, data) {
  return request.put(`/products/${id}`, data)
}

export function toggleProductStatus(id, status) {
  return request.patch(`/products/${id}/status`, { status })
}

export function deleteProduct(id) {
  return request.delete(`/products/${id}`)
}
