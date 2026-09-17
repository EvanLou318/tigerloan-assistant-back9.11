import { defineStore } from 'pinia'
import { ref } from 'vue'
import { loginApi } from '../api/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(JSON.parse(localStorage.getItem('userInfo') || 'null'))
  // 一次性清理历史版本明文落盘的密码（安全策略升级残留）
  localStorage.removeItem('savedPassword')

  async function login(phone, password, remember) {
    // 真实登录：调用后端接口换取 JWT
    const data = await loginApi({ phone, password })
    token.value = data.token
    userInfo.value = data.user
    localStorage.setItem('token', token.value)
    localStorage.setItem('userInfo', JSON.stringify(userInfo.value))
    // 「记住登录」只记住手机号：密码明文落盘在 XSS/设备借用场景下会直接泄露
    if (remember) {
      localStorage.setItem('savedPhone', phone)
    } else {
      localStorage.removeItem('savedPhone')
    }
    return true
  }

  function logout() {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('userInfo')
  }

  function getSavedPhone() {
    return localStorage.getItem('savedPhone') || ''
  }

  // 更新头像字段并持久化（不触碰 token）
  function setAvatar(url) {
    if (!userInfo.value) userInfo.value = {}
    userInfo.value.avatar = url
    localStorage.setItem('userInfo', JSON.stringify(userInfo.value))
  }

  return { token, userInfo, login, logout, getSavedPhone, setAvatar }
})
