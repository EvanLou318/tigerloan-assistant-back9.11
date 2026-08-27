<template>
  <MainLayout>
    <div class="home-page">
      <!-- 顶部问候 + 右上角个人中心入口 -->
      <div class="top-header">
        <div class="user-text">
          <div class="user-name">{{ greeting }}，{{ userInfo?.name || '李经理' }}</div>
          <div class="user-role">
            <span class="online-dot"></span>贷款经理 · 在线
          </div>
        </div>
        <div class="avatar-entry" @click="$router.push('/profile')">
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="8" r="4" fill="#3B82F6" opacity="0.85"/>
            <path d="M4 20C4 16.7 7.6 14 12 14C16.4 14 20 16.7 20 20" stroke="#3B82F6" stroke-width="2" opacity="0.85" fill="none"/>
          </svg>
        </div>
      </div>

      <!-- 今日日程 -->
      <div class="section">
        <div class="section-header">
          <span class="section-title">今日日程</span>
          <span class="section-extra" @click="$router.push('/schedules')">查看全部 ›</span>
        </div>
        <div v-if="todayPreview.length > 0" class="schedule-list">
          <div
            v-for="item in todayPreview"
            :key="item.id"
            class="schedule-row"
            @click="$router.push('/schedules')"
          >
            <div class="time-col" :class="`prio-${item.priority}`">
              <div class="t-time">{{ formatTime(item.startTime) }}</div>
              <div class="t-prio">{{ item.priority }}</div>
            </div>
            <div class="info-col">
              <div class="i-title">{{ item.title }}</div>
              <div class="i-meta">
                <span v-if="item.location">
                  <van-icon name="location-o" size="10" /> {{ item.location }}
                </span>
                <span v-if="item.customerName">
                  <van-icon name="contact" size="10" /> {{ item.customerName }}
                </span>
              </div>
            </div>
            <div class="arrow-col">
              <van-icon name="arrow" color="#94A3B8" size="14" />
            </div>
          </div>
        </div>
        <div v-else class="empty-today">
          <svg width="60" height="60" viewBox="0 0 60 60" fill="none">
            <circle cx="30" cy="30" r="26" fill="rgba(59,130,246,0.06)" />
            <rect x="16" y="20" width="28" height="26" rx="4" fill="rgba(59,130,246,0.1)" />
            <path d="M22 14V20M38 14V20" stroke="#3B82F6" stroke-width="2" stroke-linecap="round" />
            <rect x="22" y="28" width="16" height="2.5" rx="1" fill="rgba(59,130,246,0.4)" />
            <rect x="22" y="34" width="12" height="2.5" rx="1" fill="rgba(59,130,246,0.4)" />
          </svg>
          <p>今日暂无日程</p>
          <van-button size="small" round type="primary" @click="$router.push('/schedules/create')">+ 新建</van-button>
        </div>
      </div>

      <!-- 快捷入口 -->
      <div class="section">
        <div class="section-header">
          <span class="section-title">快捷入口</span>
        </div>
        <div class="quick-grid">
          <div class="quick-item" v-for="item in quickActions" :key="item.label" @click="item.action">
            <div class="quick-icon" :style="{ background: item.bg }">
              <span v-html="item.icon"></span>
            </div>
            <div class="quick-label">{{ item.label }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 录入产品方式选择弹框 -->
    <ProductMethodSheet v-model:show="showMethodSheet" />
  </MainLayout>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { useScheduleStore } from '../../stores/schedule'
import MainLayout from '../../layouts/MainLayout.vue'
import ProductMethodSheet from '../../components/ProductMethodSheet.vue'

const router = useRouter()
const authStore = useAuthStore()
const scheduleStore = useScheduleStore()
const showMethodSheet = ref(false)

// 从后端拉取最新日程（首页展示今日预览）
onMounted(() => {
  scheduleStore.loadSchedules(true)
})

const userInfo = authStore.userInfo

const hour = new Date().getHours()
const greeting = computed(() => {
  if (hour < 6) return '夜深了'
  if (hour < 12) return '早上好'
  if (hour < 14) return '中午好'
  if (hour < 18) return '下午好'
  return '晚上好'
})

const todayPreview = computed(() => scheduleStore.todaySchedules.slice(0, 3))

const quickActions = [
  {
    label: 'AI 助理',
    icon: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="9" stroke="#8B5CF6" stroke-width="1.8"/><circle cx="9" cy="10" r="1.3" fill="#8B5CF6"/><circle cx="15" cy="10" r="1.3" fill="#8B5CF6"/><path d="M9 14.5C9.8 15.3 10.8 15.7 12 15.7C13.2 15.7 14.2 15.3 15 14.5" stroke="#8B5CF6" stroke-width="1.6" stroke-linecap="round"/></svg>',
    bg: 'linear-gradient(135deg, rgba(139,92,246,0.15), rgba(6,182,212,0.05))',
    action: () => router.push('/assistant'),
  },
  {
    label: '新建日程',
    icon: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none"><path d="M19 3H18V1H16V3H8V1H6V3H5C3.9 3 3 3.9 3 5V21C3 22.1 3.9 23 5 23H19C20.1 23 21 22.1 21 21V5C21 3.9 20.1 3 19 3ZM17 14H13V18H11V14H7V12H11V8H13V12H17V14Z" fill="#3B82F6"/></svg>',
    bg: 'linear-gradient(135deg, rgba(59,130,246,0.15), rgba(6,182,212,0.05))',
    action: () => router.push('/schedules/create'),
  },
  {
    label: '录入产品',
    icon: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none"><path d="M19 13H13V19H11V13H5V11H11V5H13V11H19V13Z" fill="#06B6D4"/></svg>',
    bg: 'linear-gradient(135deg, rgba(6,182,212,0.15), rgba(59,130,246,0.05))',
    action: () => { showMethodSheet.value = true },
  },
  {
    label: '新建客户',
    icon: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none"><path d="M15 12C17.2 12 19 10.2 19 8C19 5.8 17.2 4 15 4C12.8 4 11 5.8 11 8C11 10.2 12.8 12 15 12ZM6 10V7H4V10H1V12H4V15H6V12H9V10H6ZM15 14C12.3 14 7 15.3 7 18V20H23V18C23 15.3 17.7 14 15 14Z" fill="#10B981"/></svg>',
    bg: 'linear-gradient(135deg, rgba(16,185,129,0.15), rgba(59,130,246,0.05))',
    action: () => router.push('/customers/create'),
  },
]

function formatTime(iso) {
  const d = new Date(iso)
  return d.toTimeString().slice(0, 5)
}
</script>

<style scoped>
.home-page {
  min-height: 100vh;
  background: var(--bg-base);
  padding-bottom: 20px;
}

/* 顶部 */
.top-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-page);
  padding-top: calc(16px + env(safe-area-inset-top));
  background: transparent;
}
.avatar-entry {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--primary-container);
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: transform 0.15s;
}
.avatar-entry:active { transform: scale(0.92); opacity: 0.85; }
.user-name { font-size: 16px; font-weight: 600; color: var(--text-primary); }
.user-role { font-size: 12px; color: var(--text-secondary); display: flex; align-items: center; gap: 4px; margin-top: 2px; }
.online-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--color-success); }

/* Section */
.section { padding: 16px 16px 0; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.section-title { font-size: 16px; font-weight: 600; color: var(--text-primary); position: relative; padding-left: 10px; }
.section-title::before {
  content: '';
  position: absolute;
  left: 0; top: 50%;
  transform: translateY(-50%);
  width: 3px; height: 14px;
  border-radius: 2px;
  background: var(--gradient-primary);
}
.section-extra { font-size: 12px; color: var(--color-primary); cursor: pointer; }

/* 今日日程列表 */
.schedule-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.schedule-row {
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--bg-card);
  border: none;
  border-radius: var(--radius-md);
  padding: 12px var(--space-card-pad);
  box-shadow: var(--shadow-card);
}
.time-col {
  width: 56px;
  flex-shrink: 0;
  text-align: center;
  border-radius: 8px;
  padding: 6px 4px;
  background: var(--primary-container);
}
.time-col.prio-P0 { background: var(--danger-container); }
.time-col.prio-P1 { background: var(--warning-container); }
.time-col.prio-P2 { background: var(--surface-container-high); }
.t-time { font-size: 14px; font-weight: 700; color: var(--text-primary); }
.t-prio { font-size: 11px; color: var(--text-tertiary); margin-top: 1px; }
.info-col { flex: 1; min-width: 0; }
.i-title { font-size: 14px; font-weight: 600; color: var(--text-primary); margin-bottom: 4px; }
.i-meta { font-size: 11px; color: var(--text-tertiary); display: flex; flex-wrap: wrap; gap: 8px; }
.i-meta span { display: inline-flex; align-items: center; gap: 2px; }
.arrow-col { flex-shrink: 0; }

/* 空状态 */
.empty-today {
  text-align: center;
  padding: 24px;
  background: var(--bg-card);
  border: none;
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}
.empty-today p { font-size: 14px; color: var(--text-secondary); }

/* 快捷入口 */
.quick-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}
.quick-item { display: flex; flex-direction: column; align-items: center; gap: 8px; cursor: pointer; }
.quick-icon {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  box-shadow: none;
}
.quick-label { font-size: 12px; color: var(--text-secondary); }
</style>
