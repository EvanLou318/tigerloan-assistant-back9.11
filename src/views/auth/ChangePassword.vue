<template>
  <div class="page-container">
    <van-nav-bar title="修改密码" left-arrow @click-left="$router.back()" />

    <div class="content">
      <div class="security-tip">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none">
          <path d="M18 8H17V6C17 3.2 14.8 1 12 1C9.2 1 7 3.2 7 6V8H6C4.9 8 4 8.9 4 10V20C4 21.1 4.9 22 6 22H18C19.1 22 20 21.1 20 20V10C20 8.9 19.1 8 18 8ZM12 17C10.9 17 10 16.1 10 15C10 13.9 10.9 13 12 13C13.1 13 14 13.9 14 15C14 16.1 13.1 17 12 17ZM15 8H9V6C9 4.3 10.3 3 12 3C13.7 3 15 4.3 15 6V8Z" fill="#3B82F6" opacity="0.6"/>
        </svg>
        <p>为保障账户安全，请定期修改密码</p>
      </div>

      <div class="form-card">
        <van-form @submit="onSubmit">
          <van-cell-group inset>
            <van-field
              v-model="form.oldPassword"
              label="原密码"
              placeholder="请输入原密码"
              :type="showOld ? 'text' : 'password'"
              :rules="[{ required: true, message: '请输入原密码' }]"
            >
              <template #right-icon>
                <span @click="showOld = !showOld" class="toggle-pwd">{{ showOld ? '隐藏' : '显示' }}</span>
              </template>
            </van-field>

            <van-field
              v-model="form.newPassword"
              label="新密码"
              placeholder="6-20位，不能纯数字或纯字母"
              :type="showNew ? 'text' : 'password'"
              :rules="passwordRules"
            >
              <template #right-icon>
                <span @click="showNew = !showNew" class="toggle-pwd">{{ showNew ? '隐藏' : '显示' }}</span>
              </template>
            </van-field>

            <van-field
              v-model="form.confirmPassword"
              label="确认密码"
              placeholder="请再次输入新密码"
              :type="showConfirm ? 'text' : 'password'"
              :rules="confirmRules"
            >
              <template #right-icon>
                <span @click="showConfirm = !showConfirm" class="toggle-pwd">{{ showConfirm ? '隐藏' : '显示' }}</span>
              </template>
            </van-field>
          </van-cell-group>

          <div class="password-rules">
            <p class="rules-title">密码要求：</p>
            <ul>
              <li>长度6-20位</li>
              <li>不能为纯数字或纯字母</li>
              <li>不能与当前密码相同</li>
            </ul>
          </div>

          <div style="margin: 24px 16px 0;">
            <van-button round block type="primary" native-type="submit" :loading="loading" loading-text="提交中...">
              确认修改
            </van-button>
          </div>
        </van-form>
      </div>

      <div class="tip-card">
        <p>修改成功后需使用新密码重新登录</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showSuccessToast } from 'vant'
import { useAuthStore } from '../../stores/auth'
import { changePasswordApi } from '../../api/auth'

const router = useRouter()
const authStore = useAuthStore()

const showOld = ref(false)
const showNew = ref(false)
const showConfirm = ref(false)
const loading = ref(false)

const form = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: '',
})

const passwordRules = [
  { required: true, message: '请输入新密码' },
  {
    validator: (val) => {
      if (val.length < 6 || val.length > 20) return false
      if (/^\d+$/.test(val) || /^[a-zA-Z]+$/.test(val)) return false
      return true
    },
    message: '6-20位，不能为纯数字或纯字母',
  },
]

const confirmRules = [
  { required: true, message: '请确认密码' },
  {
    validator: (val) => val === form.newPassword,
    message: '两次输入的密码不一致',
  },
]

async function onSubmit() {
  if (form.oldPassword === form.newPassword) {
    showToast('新密码不能与当前密码相同')
    return
  }
  loading.value = true
  try {
    // 真实修改密码：调用后端接口校验原密码并更新
    await changePasswordApi({ oldPassword: form.oldPassword, newPassword: form.newPassword })
    authStore.logout()
    showSuccessToast('密码修改成功，请重新登录')
    setTimeout(() => router.replace('/login'), 1000)
  } catch (e) {
    showToast(e.message || '修改失败，请重试')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.content {
  padding: 16px 0;
}

.security-tip {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 32px 24px 24px;
}

.security-tip p {
  margin-top: 12px;
  font-size: 14px;
  color: var(--text-secondary);
}

.form-card {
  margin: 0 16px;
}

.password-rules {
  margin: 16px 24px 0;
  padding: 12px 14px;
  background: var(--secondary-container);
  border: none;
  border-radius: var(--radius-sm);
}

.rules-title {
  font-size: 12px;
  color: var(--color-secondary);
  margin-bottom: 4px;
  font-weight: 600;
}

.password-rules ul {
  list-style: none;
  padding-left: 0;
}

.password-rules li {
  font-size: 12px;
  color: var(--text-tertiary);
  padding: 2px 0;
  position: relative;
  padding-left: 12px;
}

.password-rules li::before {
  content: '·';
  position: absolute;
  left: 0;
  color: var(--color-secondary);
}

.toggle-pwd {
  font-size: 14px;
  color: var(--text-tertiary);
  cursor: pointer;
}

.tip-card {
  margin: 16px;
  text-align: center;
  font-size: 12px;
  color: var(--text-tertiary);
}
</style>
