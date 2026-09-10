// ==================== Axios 实例与拦截器 ====================
// 统一 baseURL '/api'（开发环境经 vite proxy 转发到 3001，生产同域直连）
// 请求拦截器：注入 JWT token
// 响应拦截器：统一解包 { success, data } → 直接返回 data；401 自动登出

import axios from 'axios'
import { showToast } from 'vant'

const request = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// 请求拦截：注入 token
request.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    // 用自定义头传 token：部分部署平台的网关会覆盖标准 Authorization 头，
    // 导致服务端永远收不到我们的 JWT（表现为登录成功即掉线）。
    // 同时保留 Authorization 以兼容本地开发与其他环境。
    config.headers['X-Auth-Token'] = token
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截：解包 + 错误处理
request.interceptors.response.use(
  (response) => {
    const body = response.data
    // 后端统一响应格式 { success: true, data } / { success: false, message }
    if (body && typeof body === 'object' && 'success' in body) {
      if (!body.success) {
        return Promise.reject(new Error(body.message || '请求失败'))
      }
      return body.data
    }
    return body
  },
  (error) => {
    const status = error.response?.status
    const message = error.response?.data?.message || error.message || '网络异常'

    // 401：登录失效，清理本地状态并跳转登录页
    if (status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('userInfo')
      if (!location.hash.includes('/login')) {
        showToast('登录已过期，请重新登录')
        setTimeout(() => { location.hash = '#/login' }, 600)
      }
    }
    return Promise.reject(new Error(message))
  }
)

export default request
