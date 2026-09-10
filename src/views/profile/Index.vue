<template>
  <div class="profile-page">
    <!-- 顶部蓝青渐变大色块 -->
    <div class="hero">
      <div class="hero-nav" @click="router.back()">
        <AppIcon name="chevron-left" :size="18" color="var(--text-primary)" />
        <span class="hero-nav-title">个人中心</span>
      </div>
        <div class="user-row">
          <div class="avatar" @click="pickAvatar">
            <img v-if="avatarUrl" :src="avatarUrl" class="avatar-img" alt="头像" />
            <span v-else>{{ (userInfo?.name || '李').charAt(0) }}</span>
            <div class="avatar-edit"><AppIcon name="camera" :size="12" /></div>
          </div>
          <div class="user-text">
            <div class="user-name">{{ userInfo?.name || '李经理' }} <span class="verified">✓ 已认证</span></div>
            <div class="user-phone">{{ userInfo?.phone || '13800138000' }}</div>
          </div>
          <AppIcon name="chevron-right" :size="18" color="var(--text-tertiary)" />
        </div>
        <input ref="fileInput" type="file" accept="image/*" style="display: none" @change="onAvatarChange" />
        <div class="stats">
          <div class="stat-cell tint-product" @click="$router.push('/products')">
            <div class="stat-num">{{ productStore.products.length }}</div>
            <div class="stat-lbl">产品</div>
          </div>
          <div class="stat-cell tint-customer" @click="$router.push('/customers')">
            <div class="stat-num">{{ customerStore.customers.length }}</div>
            <div class="stat-lbl">客户</div>
          </div>
          <div class="stat-cell tint-todo" @click="$router.push('/schedules')">
            <div class="stat-num">{{ scheduleStore.pendingCount }}</div>
            <div class="stat-lbl">待办日程</div>
          </div>
        </div>
      </div>

      <!-- 账户管理 -->
      <div class="list-section">
        <div class="list-title">账户</div>
        <div class="list-card">
          <div class="list-item" @click="$router.push('/change-password')">
            <div class="li-ic" style="background: var(--d-schedule-50);">
              <AppIcon name="lock" :size="20" color="var(--d-schedule-600)" />
            </div>
            <div class="li-text">修改密码</div>
            <AppIcon name="chevron-right" :size="14" color="#94A3B8" />
          </div>
          <div class="list-item" @click="showHelp = true">
            <div class="li-ic" style="background: var(--d-customer-50);">
              <AppIcon name="help" :size="20" color="var(--d-customer-600)" />
            </div>
            <div class="li-text">使用帮助</div>
            <AppIcon name="chevron-right" :size="14" color="#94A3B8" />
          </div>
        </div>
      </div>

      <!-- 退出登录 -->
      <div class="logout-section">
        <van-button plain round block @click="handleLogout">退出登录</van-button>
      </div>

      <!-- 帮助弹窗 -->
      <van-dialog v-model:show="showHelp" title="使用帮助" confirm-button-text="我知道了" :show-cancel-button="false">
        <div style="padding: 16px; font-size: 14px; color: var(--text-secondary); line-height: 1.8;">
          <p><strong style="color: var(--color-primary);">产品录入</strong>：支持文本、语音、图片、PDF四种方式，AI自动提取产品信息</p>
          <p style="margin-top: 8px;"><strong style="color: var(--color-primary);">客户录入</strong>：支持文件上传、拍照、语音口述，AI自动提取结构化信息</p>
          <p style="margin-top: 8px;"><strong style="color: var(--color-primary);">AI匹配</strong>：基于客户档案智能匹配贷款产品，给出准入/拒贷结果及优化建议</p>
          <p style="margin-top: 8px;"><strong style="color: var(--color-primary);">场景推演</strong>：调整客户指标模拟匹配结果，不影响真实档案</p>
        </div>
      </van-dialog>
    </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { showSuccessToast, showConfirmDialog, showToast } from 'vant'
import { useAuthStore } from '../../stores/auth'
import { useProductStore } from '../../stores/product'
import { useCustomerStore } from '../../stores/customer'
import { useScheduleStore } from '../../stores/schedule'
import { uploadAvatar } from '../../api/auth'

const router = useRouter()
const authStore = useAuthStore()
const productStore = useProductStore()
const customerStore = useCustomerStore()
const scheduleStore = useScheduleStore()

const userInfo = authStore.userInfo
const showHelp = ref(false)
const fileInput = ref(null)

// 头像地址：优先本地存储，其次走相对路径（同域静态服务 /uploads）
const avatarUrl = computed(() => {
  const a = userInfo?.value?.avatar || ''
  return a || ''
})

const uploading = ref(false)

function pickAvatar() {
  fileInput.value?.click()
}

async function onAvatarChange(e) {
  const file = e.target.files?.[0]
  e.target.value = '' // 允许重复选择同一文件
  if (!file) return
  if (!/^image\//.test(file.type)) {
    showToast('请选择图片文件')
    return
  }
  if (file.size > 5 * 1024 * 1024) {
    showToast('图片不能超过 5MB')
    return
  }
  if (uploading.value) return
  uploading.value = true
  try {
    const { avatar } = await uploadAvatar(file)
    authStore.setAvatar(avatar)
    showSuccessToast('头像已更新')
  } catch (err) {
    showToast(err.message || '上传失败，请重试')
  } finally {
    uploading.value = false
  }
}

function handleLogout() {
  showConfirmDialog({ title: '退出登录', message: '确定要退出登录吗？' })
    .then(() => { authStore.logout(); router.replace('/login') })
    .catch(() => {})
}
</script>

<style scoped>
.profile-page {
  min-height: 100vh;
  background: var(--bg-base);
  padding-bottom: 20px;
}

/* ============ 顶部面板（白色，与首页一致） ============ */
.hero {
  background: var(--surface-container-lowest);
  padding: calc(env(safe-area-inset-top) + 12px) 16px 20px;
  color: var(--text-primary);
  border-radius: 0 0 24px 24px;
  position: relative;
}

.hero-nav {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 0 14px;
  cursor: pointer;
  width: fit-content;
}
.hero-nav:active { opacity: 0.75; }

.hero-nav-title {
  font-size: 16px;
  font-weight: 600;
}

.user-row {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 8px 0 16px;
}

.avatar {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--primary-container);
  color: var(--on-primary-container);
  border: none;
  font-size: 24px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  position: relative;
  cursor: pointer;
  overflow: visible;
}
.avatar:active { opacity: 0.85; }
.avatar-img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
}
.avatar-edit {
  position: absolute;
  right: -2px;
  bottom: -2px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--color-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid var(--surface-container-lowest);
}

.user-text { flex: 1; min-width: 0; }
.user-name { font-size: 20px; font-weight: 700; display: flex; align-items: center; gap: 6px; letter-spacing: -0.2px; }
.verified {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 4px;
  background: var(--success-container);
  color: var(--on-success-container);
  font-weight: 500;
  letter-spacing: 0.5px;
}
.user-phone { font-size: 14px; color: var(--text-secondary); margin-top: 4px; }

/* 统计行（在色块内） */
.stats {
  display: flex;
  margin: 0 -4px;
}
.stat-cell {
  flex: 1;
  text-align: center;
  cursor: pointer;
  border-radius: 12px;
  padding: 10px 4px;
  margin: 0 4px;
  transition: transform 0.15s;
}
.stat-cell:active { transform: scale(0.97); }
.stat-num { font-size: 24px; font-weight: 700; font-family: 'DIN', 'Roboto', sans-serif; line-height: 1.2; }
.stat-lbl { font-size: 12px; margin-top: 2px; }

.stat-cell.tint-product  { background: var(--d-product-50); }
.stat-cell.tint-customer { background: var(--d-customer-50); }
.stat-cell.tint-todo     { background: var(--d-todo-50); }
.tint-product  .stat-num { color: var(--d-product-800); }
.tint-customer .stat-num { color: var(--d-customer-800); }
.tint-todo     .stat-num { color: var(--d-todo-800); }
.tint-product  .stat-lbl { color: var(--d-product-600); }
.tint-customer .stat-lbl { color: var(--d-customer-600); }
.tint-todo     .stat-lbl { color: var(--d-todo-600); }

/* ============ 列表区 ============ */
.list-section { padding: 0 16px 16px; }
.list-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
  padding-left: 4px;
}
.list-card {
  background: var(--bg-card);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
  overflow: hidden;
}
.list-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-bottom: none;
  cursor: pointer;
  transition: background 0.15s;
}
.list-item:last-child { border-bottom: none; }
.list-item:active { background: var(--bg-card-hover); }
.li-ic {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.li-text { flex: 1; font-size: 14px; color: var(--text-primary); }
.li-extra { font-size: 12px; color: var(--text-tertiary); }

/* ============ 退出 ============ */
.logout-section { padding: 16px; }
</style>
