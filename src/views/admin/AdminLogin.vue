<template>
  <div class="admin-login-page">
    <div class="login-card">
      <div class="brand">
        <div class="brand-logo">智</div>
        <div class="brand-text">
          <h1 class="brand-name">智贷助手 · 管理后台</h1>
          <p class="brand-sub">请使用管理员账号登录</p>
        </div>
      </div>

      <van-form @submit="onSubmit">
        <van-cell-group inset>
          <van-field
            v-model="form.phone"
            name="phone"
            type="tel"
            maxlength="11"
            label="手机号"
            placeholder="请输入手机号"
            :rules="phoneRules"
            clearable
          />
          <van-field
            v-model="form.password"
            name="password"
            :type="showPassword ? 'text' : 'password'"
            label="密码"
            placeholder="请输入密码"
            :rules="passwordRules"
          >
            <template #button>
              <span class="toggle-pw" @click="showPassword = !showPassword">{{ showPassword ? '隐藏' : '显示' }}</span>
            </template>
          </van-field>
        </van-cell-group>
        <div class="submit-wrap">
          <van-button round block type="primary" native-type="submit" :loading="loading" loading-text="登录中...">
            登 录
          </van-button>
        </div>
      </van-form>

      <div class="card-footer">
        <span class="hint">仅限拥有后台权限的角色（管理员 / 团队主管）</span>
        <span class="back-link" @click="router.push('/login')">← 返回移动端登录</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showToast } from 'vant'
import { useAuthStore } from '../../stores/auth'
import { isAdminUser } from '../../router'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const showPassword = ref(false)
const loading = ref(false)

const form = reactive({
  phone: '',
  password: '',
})

const phoneRules = [
  { required: true, message: '请输入手机号' },
  { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号' },
]

const passwordRules = [
  { required: true, message: '请输入密码' },
]

async function onSubmit() {
  loading.value = true
  try {
    await authStore.login(form.phone, form.password, false)
    // 无后台权限的账号不允许进入后台：立即登出并提示
    if (!isAdminUser()) {
      authStore.logout()
      showToast('该账号没有管理后台访问权限')
      return
    }
    showToast({ message: '登录成功', type: 'success' })
    const r = route.query.redirect
    const redirect = typeof r === 'string' && r.startsWith('/admin') && !r.startsWith('//') ? r : ''
    router.replace(redirect || '/admin/dashboard')
  } catch (e) {
    showToast(e.message || '登录失败，请重试')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.admin-login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-base, #E8EDF5);
  padding: 40px 24px;
}

.login-card {
  width: 420px;
  max-width: 100%;
  background: var(--surface, #fff);
  border-radius: 24px;
  padding: 40px 36px 28px;
  box-shadow: 0 8px 32px rgba(31, 45, 88, 0.08);
}

.brand {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 28px;
}

.brand-logo {
  width: 52px;
  height: 52px;
  border-radius: 16px;
  background: linear-gradient(135deg, #2E6BFF, #5A8BFF);
  color: #fff;
  font-size: 24px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.brand-name {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary, #1B2440);
}

.brand-sub {
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--text-tertiary, #8A93A8);
}

:deep(.van-cell-group--inset) {
  margin: 0 !important;
  background: transparent;
}

:deep(.van-field) {
  background: var(--bg-base, #EEF2F9);
  border-radius: 12px;
  margin-bottom: 12px;
}

:deep(.van-field__label) {
  width: 58px;
}

.toggle-pw {
  font-size: 13px;
  color: var(--color-primary, #2E6BFF);
  cursor: pointer;
}

.submit-wrap {
  margin-top: 20px;
}

.submit-wrap .van-button {
  height: 46px;
  font-size: 16px;
  font-weight: 600;
}

.card-footer {
  margin-top: 22px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: center;
}

.hint {
  font-size: 12px;
  color: var(--text-tertiary, #8A93A8);
}

.back-link {
  font-size: 13px;
  color: var(--color-primary, #2E6BFF);
  cursor: pointer;
}
</style>
