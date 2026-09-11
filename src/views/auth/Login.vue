<template>
  <div class="login-page">
    <!-- 背景装饰 -->
    <div class="bg-decoration">
      <div class="bg-orb bg-orb-1"></div>
      <div class="bg-orb bg-orb-2"></div>
      <div class="bg-grid"></div>
    </div>

    <!-- Logo 区域 -->
    <div class="logo-section anim-item" style="--d: 0s">
      <div class="logo-icon">
        <svg viewBox="0 0 48 48" width="48" height="48">
          <defs>
            <linearGradient id="logoGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stop-color="#2563EB" />
              <stop offset="100%" stop-color="#0EA5A5" />
            </linearGradient>
          </defs>
          <path d="M24 4 L42 14 V30 L24 44 L6 30 V14 Z" fill="none" stroke="url(#logoGrad)" stroke-width="2" />
          <path d="M24 12 L34 18 V28 L24 36 L14 28 V18 Z" fill="url(#logoGrad)" opacity="0.3" />
          <circle cx="24" cy="24" r="4" fill="url(#logoGrad)" />
        </svg>
      </div>
      <h1 class="logo-title">智贷助手</h1>
      <p class="logo-subtitle">AI 驱动的智能展业平台</p>
    </div>

    <!-- 表单区域 -->
    <div class="form-section">
      <div class="form-card anim-item" style="--d: 0.1s">
        <van-form @submit="onSubmit">
          <div class="form-field">
            <van-field
              v-model="form.phone"
              name="phone"
              placeholder="请输入手机号"
              type="tel"
              maxlength="11"
              :rules="phoneRules"
              clearable
            >
              <template #left-icon>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path d="M20 15.5C18.8 15.5 17.5 15.3 16.4 14.9C16 14.7 15.5 14.8 15.2 15.1L13.5 16.8C11.3 15.7 9.2 13.6 8.1 11.4L9.8 9.7C10.1 9.4 10.2 8.9 10 8.5C9.6 7.4 9.4 6.1 9.4 4.9C9.4 4.4 8.9 4 8.4 4H4.9C4.4 4 4 4.4 4 4.9C4 13.8 11.1 21 20 21C20.5 21 21 20.6 21 20.1V16.6C21 16.1 20.6 15.5 20 15.5Z" fill="#475569"/>
                </svg>
              </template>
            </van-field>
          </div>

          <div class="form-field">
            <van-field
              v-model="form.password"
              name="password"
              placeholder="请输入密码"
              :type="showPassword ? 'text' : 'password'"
              :rules="passwordRules"
              clearable
            >
              <template #left-icon>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path d="M18 8H17V6C17 3.2 14.8 1 12 1C9.2 1 7 3.2 7 6V8H6C4.9 8 4 8.9 4 10V20C4 21.1 4.9 22 6 22H18C19.1 22 20 21.1 20 20V10C20 8.9 19.1 8 18 8ZM9 6C9 4.3 10.3 3 12 3C13.7 3 15 4.3 15 6V8H9V6ZM13 17C13 17.6 12.6 18 12 18C11.4 18 11 17.6 11 17V13C11 12.4 11.4 12 12 12C12.6 12 13 12.4 13 13V17Z" fill="#475569"/>
                </svg>
              </template>
              <template #right-icon>
                <span @click="showPassword = !showPassword" style="font-size: 14px; color: var(--text-tertiary);">
                  {{ showPassword ? '隐藏' : '显示' }}
                </span>
              </template>
            </van-field>
          </div>

          <div class="form-options">
            <van-checkbox v-model="form.remember" shape="square" icon-size="16">
              记住密码
            </van-checkbox>
            <span class="forgot-link" @click="showForgotDialog = true">忘记密码</span>
          </div>

          <div style="margin-top: 24px;">
            <van-button round block type="primary" native-type="submit" :loading="loading" loading-text="登录中...">
              登 录
            </van-button>
          </div>
        </van-form>

        <div class="form-footer">
          <span class="footer-text">仅限授权贷款经理使用</span>
          <span class="admin-link" @click="$router.push('/admin')">管理后台入口 →</span>
        </div>
      </div>
    </div>

    <!-- 忘记密码弹窗 -->
    <van-dialog v-model:show="showForgotDialog" title="忘记密码" confirm-button-text="我知道了" :show-cancel-button="false">
      <div style="padding: 16px; text-align: center; color: var(--text-secondary); font-size: 14px; line-height: 1.8;">
        请联系超级管理员进行密码重置<br />
        重置后可使用新密码登录，<br />
        登录后在「个人中心」自行修改密码
      </div>
    </van-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showToast } from 'vant'
import { useAuthStore } from '../../stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const showPassword = ref(false)
const loading = ref(false)
const showForgotDialog = ref(false)

const form = reactive({
  phone: '',
  password: '',
  remember: false,
})

// 自动填充记住的密码
const saved = authStore.getSavedCredentials()
if (saved.phone) {
  form.phone = saved.phone
  form.password = saved.password
  form.remember = true
}

const phoneRules = [
  { required: true, message: '请输入手机号' },
  { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号' },
]

const passwordRules = [
  { required: true, message: '请输入密码' },
  {
    validator: (val) => {
      if (val.length < 6 || val.length > 20) return false
      if (/^\d+$/.test(val) || /^[a-zA-Z]+$/.test(val)) return false
      return true
    },
    message: '密码6-20位，不能为纯数字或纯字母',
  },
]

async function onSubmit() {
  loading.value = true
  try {
    // 真实登录：调用后端接口校验账号密码
    await authStore.login(form.phone, form.password, form.remember)
    showToast({ message: '登录成功', type: 'success' })
    // 回到登录前想去的页面（如直达后台地址 #/admin/...），否则进移动端首页
    const r = route.query.redirect
    const redirect = typeof r === 'string' && r.startsWith('/') && !r.startsWith('//') ? r : ''
    router.replace(redirect || '/home')
  } catch (e) {
    showToast(e.message || '登录失败，请重试')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  position: relative;
  overflow: hidden;
  background: var(--bg-base);
  padding: 40px 24px;
}

/* 背景装饰 */
.bg-decoration {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
  z-index: 0;
}

.bg-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.06;
}

.bg-orb-1 {
  width: 300px;
  height: 300px;
  background: var(--color-primary);
  top: -100px;
  right: -50px;
}

.bg-orb-2 {
  width: 250px;
  height: 250px;
  background: var(--color-secondary);
  bottom: -50px;
  left: -80px;
}

.bg-grid {
  display: none;
}

/* Logo 区域 */
.logo-section {
  text-align: center;
  margin-bottom: 40px;
  position: relative;
  z-index: 1;
}

.logo-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 24px;
  background: var(--primary-container);
  color: var(--on-primary-container);
  border: none;
  box-shadow: none;
}

.logo-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--color-primary);
  letter-spacing: 2px;
  margin-bottom: 8px;
}

.logo-subtitle {
  font-size: 14px;
  color: var(--text-tertiary);
  letter-spacing: 1px;
}

/* 入场动效：依次浮起 */
.anim-item {
  animation: float-up 0.45s cubic-bezier(0.2, 0, 0, 1) both;
  animation-delay: var(--d, 0s);
}

/* 表单区域 */
.form-section {
  position: relative;
  z-index: 1;
}

.form-card {
  background: var(--surface-container);
  border: none;
  border-radius: var(--radius-lg);
  padding: 24px 16px;
  box-shadow: var(--shadow-card);
  position: relative;
}

.form-card::before {
  display: none;
}

.form-field {
  margin-bottom: 16px;
}

.form-field :deep(.van-field) {
  background: var(--bg-input);
  border-radius: var(--radius-sm);
  border: none;
}

.form-field :deep(.van-field__left-icon) {
  margin-right: 10px;
}

.form-field :deep(.van-cell) {
  border-radius: var(--radius-sm);
  padding: 12px 14px;
}

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 4px;
  padding: 0 4px;
}

.forgot-link {
  font-size: 14px;
  color: var(--color-secondary);
  cursor: pointer;
}

.form-options :deep(.van-checkbox__label) {
  color: var(--text-secondary);
  font-size: 14px;
  margin-left: 4px;
}

.form-footer {
  margin-top: 20px;
  text-align: center;
}

.footer-text {
  font-size: 12px;
  color: var(--text-tertiary);
}

.admin-link {
  font-size: 12px;
  color: var(--color-primary, #2E6BFF);
  cursor: pointer;
  margin-left: 12px;
}
</style>
