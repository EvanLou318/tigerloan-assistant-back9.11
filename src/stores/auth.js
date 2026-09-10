import { defineStore } from 'pinia'
import { ref } from 'vue'
import { loginApi } from '../api/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(JSON.parse(localStorage.getItem('userInfo') || 'null'))

  async function login(phone, password, remember) {
    // 真实登录：调用后端接口换取 JWT
    const data = await loginApi({ phone, password })
    token.value = data.token
    userInfo.value = data.user
    localStorage.setItem('token', token.value)
    localStorage.setItem('userInfo', JSON.stringify(userInfo.value))
    if (remember) {
      localStorage.setItem('savedPhone', phone)
      localStorage.setItem('savedPassword', password)
    } else {
      localStorage.removeItem('savedPhone')
      localStorage.removeItem('savedPassword')
    }
    return true
  }

  function logout() {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('userInfo')
  }

  function getSavedCredentials() {
    return {
      phone: localStorage.getItem('savedPhone') || '',
      password: localStorage.getItem('savedPassword') || '',
    }
  }

  // 更新头像字段并持久化（不触碰 token）
  function setAvatar(url) {
    if (!userInfo.value) userInfo.value = {}
    userInfo.value.avatar = url
    localStorage.setItem('userInfo', JSON.stringify(userInfo.value))
  }

  return { token, userInfo, login, logout, getSavedCredentials, setAvatar }
})
