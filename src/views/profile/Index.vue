<template>
  <MainLayout>
    <div class="profile-page">
      <!-- 顶部蓝青渐变大色块 -->
      <div class="hero">
        <div class="hero-nav">
          <span class="hero-nav-title">个人中心</span>
        </div>
        <div class="user-row">
          <div class="avatar">{{ (userInfo?.name || '李').charAt(0) }}</div>
          <div class="user-text">
            <div class="user-name">{{ userInfo?.name || '李经理' }} <span class="verified">✓ 已认证</span></div>
            <div class="user-phone">{{ userInfo?.phone || '13800138000' }}</div>
          </div>
          <van-icon name="arrow" color="rgba(255,255,255,0.85)" size="18" />
        </div>
        <div class="stats">
          <div class="stat-cell" @click="$router.push('/products')">
            <div class="stat-num">{{ productStore.products.length }}</div>
            <div class="stat-lbl">产品</div>
          </div>
          <div class="stat-cell" @click="$router.push('/customers')">
            <div class="stat-num">{{ customerStore.customers.length }}</div>
            <div class="stat-lbl">客户</div>
          </div>
          <div class="stat-cell" @click="$router.push('/schedules')">
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
            <div class="li-ic" style="background: rgba(59,130,246,0.12);">
              <van-icon name="lock" size="20" color="#3B82F6" />
            </div>
            <div class="li-text">修改密码</div>
            <van-icon name="arrow" size="14" color="#94A3B8" />
          </div>
          <div class="list-item" @click="showHelp = true">
            <div class="li-ic" style="background: rgba(245,158,11,0.12);">
              <van-icon name="question-o" size="20" color="#F59E0B" />
            </div>
            <div class="li-text">使用帮助</div>
            <van-icon name="arrow" size="14" color="#94A3B8" />
          </div>
        </div>
      </div>

      <!-- 系统信息 -->
      <div class="list-section">
        <div class="list-title">系统</div>
        <div class="list-card">
          <div class="list-item" @click="showAbout = true">
            <div class="li-ic" style="background: rgba(6,182,212,0.12);">
              <van-icon name="info-o" size="20" color="#06B6D4" />
            </div>
            <div class="li-text">关于智贷助手</div>
            <div class="li-extra">v1.0.0</div>
          </div>
          <div class="list-item" @click="showFeedback = true">
            <div class="li-ic" style="background: rgba(139,92,246,0.12);">
              <van-icon name="comment-o" size="20" color="#8B5CF6" />
            </div>
            <div class="li-text">意见反馈</div>
            <van-icon name="arrow" size="14" color="#94A3B8" />
          </div>
        </div>
      </div>

      <!-- 退出登录 -->
      <div class="logout-section">
        <van-button plain round block @click="handleLogout">退出登录</van-button>
      </div>

      <!-- 关于弹窗 -->
      <van-dialog v-model:show="showAbout" title="关于智贷助手" confirm-button-text="关闭" :show-cancel-button="false">
        <div style="padding: 16px; text-align: center;">
          <div style="font-size: 14px; color: var(--text-secondary); line-height: 1.8;">
            <p style="font-size: 20px; font-weight: 700; color: var(--color-primary); margin-bottom: 12px;">
              智贷助手 v1.0.0
            </p>
            <p>AI 驱动的智能展业平台</p>
            <p style="margin-top: 8px; font-size: 12px; color: var(--text-tertiary);">
              面向贷款经理的智能辅助工具<br />
              通过 AI 能力帮助快速录入资料、智能匹配产品
            </p>
          </div>
        </div>
      </van-dialog>

      <!-- 反馈弹窗 -->
      <van-dialog v-model:show="showFeedback" title="意见反馈" confirm-button-text="提交" @confirm="submitFeedback">
        <div style="padding: 16px;">
          <van-field v-model="feedbackText" type="textarea" placeholder="请输入您的意见或建议" rows="4" autosize>
            <template #right-icon>
              <VoiceMic label="意见反馈" sample="希望增加批量导入客户和导出报表的功能" @confirm="feedbackText = $event" />
            </template>
          </van-field>
        </div>
      </van-dialog>

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
  </MainLayout>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { showSuccessToast, showConfirmDialog } from 'vant'
import { useAuthStore } from '../../stores/auth'
import { useProductStore } from '../../stores/product'
import { useCustomerStore } from '../../stores/customer'
import { useScheduleStore } from '../../stores/schedule'
import MainLayout from '../../layouts/MainLayout.vue'
import VoiceMic from '../../components/VoiceMic.vue'

const router = useRouter()
const authStore = useAuthStore()
const productStore = useProductStore()
const customerStore = useCustomerStore()
const scheduleStore = useScheduleStore()

const userInfo = authStore.userInfo
const showAbout = ref(false)
const showFeedback = ref(false)
const showHelp = ref(false)
const feedbackText = ref('')

function handleLogout() {
  showConfirmDialog({ title: '退出登录', message: '确定要退出登录吗？' })
    .then(() => { authStore.logout(); router.replace('/login') })
    .catch(() => {})
}

function submitFeedback() {
  if (!feedbackText.value) return
  feedbackText.value = ''
  showSuccessToast('感谢您的反馈')
}
</script>

<style scoped>
.profile-page {
  min-height: 100vh;
  background: var(--bg-base);
  padding-bottom: 20px;
}

/* ============ 顶部大色块 ============ */
.hero {
  background: linear-gradient(135deg, #3B82F6 0%, #06B6D4 100%);
  padding: calc(env(safe-area-inset-top) + 12px) 16px 24px;
  color: #fff;
  position: relative;
}

.hero-nav {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 0 14px;
}

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
  background: rgba(255, 255, 255, 0.25);
  border: none;
  font-size: 24px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.user-text { flex: 1; min-width: 0; }
.user-name { font-size: 20px; font-weight: 700; display: flex; align-items: center; gap: 6px; }
.verified {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.25);
  font-weight: 500;
  letter-spacing: 0.5px;
}
.user-phone { font-size: 14px; opacity: 0.85; margin-top: 4px; }

/* 统计行（在色块内） */
.stats {
  display: flex;
  margin: 0 -4px;
}
.stat-cell {
  flex: 1;
  text-align: center;
  cursor: pointer;
  border-radius: var(--radius-sm);
  padding: 4px 0;
  transition: background 0.15s;
}
.stat-cell:active { background: rgba(255, 255, 255, 0.16); }
.stat-num { font-size: 24px; font-weight: 700; font-family: 'DIN', 'Roboto', sans-serif; line-height: 1.2; }
.stat-lbl { font-size: 12px; opacity: 0.85; margin-top: 2px; }

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
