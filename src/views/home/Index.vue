<template>
  <MainLayout>
    <div class="home-page">
      <!-- 渐变头部：问候 + 数据概览 -->
      <header class="hero">
        <div class="hero-top">
          <div class="user-text">
            <div class="user-name">{{ greeting }}，{{ userInfo?.name || '李经理' }}</div>
            <div class="user-role">
              <span class="online-dot"></span>{{ todayText }} · 展业顺利
            </div>
          </div>
          <div class="avatar-entry" @click="$router.push('/profile')">
            {{ (userInfo?.name || '李').charAt(0) }}
          </div>
        </div>

        <!-- 数据概览：半压在渐变上的白卡 -->
        <div class="stats-card animate-float-up">
          <div class="stat-cell" @click="$router.push('/schedules')">
            <div class="stat-num accent">{{ scheduleStore.todayCount }}</div>
            <div class="stat-lbl">今日日程</div>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-cell" @click="$router.push('/customers')">
            <div class="stat-num">{{ customerStore.customers.length }}</div>
            <div class="stat-lbl">客户</div>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-cell" @click="$router.push('/products')">
            <div class="stat-num">{{ productStore.products.length }}</div>
            <div class="stat-lbl">产品</div>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-cell" @click="$router.push('/schedules')">
            <div class="stat-num warn" v-if="scheduleStore.pendingCount > 0">{{ scheduleStore.pendingCount }}</div>
            <div class="stat-num" v-else>0</div>
            <div class="stat-lbl">待办</div>
          </div>
        </div>
      </header>

      <!-- 今日日程 -->
      <div class="section anim-item" style="--d: 0.05s">
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
          <p>今日暂无日程，享受轻松的一天</p>
          <van-button size="small" round type="primary" @click="showScheduleSheet = true">+ 新建</van-button>
        </div>
      </div>

      <!-- 快捷入口 -->
      <div class="section anim-item" style="--d: 0.12s">
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
    <!-- 新建日程方式选择弹框 -->
    <ScheduleMethodSheet v-model:show="showScheduleSheet" />
  </MainLayout>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { useScheduleStore } from '../../stores/schedule'
import { useProductStore } from '../../stores/product'
import { useCustomerStore } from '../../stores/customer'
import MainLayout from '../../layouts/MainLayout.vue'
import ProductMethodSheet from '../../components/ProductMethodSheet.vue'
import ScheduleMethodSheet from '../../components/ScheduleMethodSheet.vue'

const router = useRouter()
const authStore = useAuthStore()
const scheduleStore = useScheduleStore()
const productStore = useProductStore()
const customerStore = useCustomerStore()
const showMethodSheet = ref(false)
const showScheduleSheet = ref(false)

// 首页工作台：日程 / 产品 / 客户 数据同时预热（不强制刷新，靠各页面进入时刷新）
onMounted(() => {
  scheduleStore.loadSchedules()
  productStore.loadProducts()
  customerStore.loadCustomers()
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

const todayText = new Date().toLocaleDateString('zh-CN', { month: 'long', day: 'numeric', weekday: 'short' })

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
    action: () => { showScheduleSheet.value = true },
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
  min-height: 100dvh;
  background: var(--bg-base);
  padding-bottom: 20px;
}

/* ============ 渐变头部 ============ */
.hero {
  background: linear-gradient(135deg, #3B82F6 0%, #06B6D4 100%);
  padding: calc(env(safe-area-inset-top) + 20px) 16px 24px;
  border-radius: 0 0 28px 28px;
}

.hero-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 18px;
}

.user-name {
  font-size: 20px;
  font-weight: 700;
  color: #fff;
}

.user-role {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.85);
  display: flex;
  align-items: center;
  gap: 5px;
  margin-top: 4px;
}

.online-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #4ADE80;
  box-shadow: 0 0 0 3px rgba(74, 222, 128, 0.25);
}

.avatar-entry {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.22);
  color: #fff;
  font-size: 17px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: transform 0.15s;
}
.avatar-entry:active { transform: scale(0.92); }

/* 数据概览：半压渐变的白卡（负 margin 上移，不依赖 transform，避免与后续内容重叠） */
.stats-card {
  display: flex;
  align-items: center;
  background: var(--surface-container-lowest);
  border-radius: var(--radius-md);
  padding: 16px 8px;
  box-shadow: 0 4px 16px rgba(26, 34, 51, 0.1);
  margin-bottom: -48px;
}

.stat-cell {
  flex: 1;
  text-align: center;
  cursor: pointer;
  padding: 2px 0;
  border-radius: var(--radius-sm);
  transition: background 0.15s;
}
.stat-cell:active { background: var(--surface-container-high); }

.stat-num {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  font-family: 'DIN', 'Roboto', sans-serif;
  line-height: 1.25;
}
.stat-num.accent { color: var(--color-primary); }
.stat-num.warn { color: var(--color-warning); }

.stat-lbl {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 2px;
}

.stat-divider {
  width: 1px;
  height: 28px;
  background: var(--surface-container-high);
}

/* ============ Section ============ */
.section { padding: 40px 16px 0; }
.section:last-child { padding-bottom: 8px; }

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
.section-extra { font-size: 12px; color: var(--color-primary); cursor: pointer; padding: 4px 0; }
.section-extra:active { opacity: 0.7; }

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
  cursor: pointer;
  transition: transform 0.15s ease;
}
.schedule-row:active { transform: scale(0.98); background: var(--bg-card-hover); }

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
  box-shadow: var(--shadow-card);
}
.empty-today p { font-size: 14px; color: var(--text-secondary); }

/* 快捷入口 */
.quick-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  background: var(--bg-card);
  border-radius: var(--radius-md);
  padding: 16px 8px;
  box-shadow: var(--shadow-card);
}
.quick-item { display: flex; flex-direction: column; align-items: center; gap: 8px; cursor: pointer; padding: 4px 0; border-radius: var(--radius-sm); }
.quick-item:active { opacity: 0.75; }
.quick-item:active .quick-icon { transform: scale(0.92); }
.quick-icon {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  box-shadow: none;
  transition: transform 0.15s ease;
}
.quick-label { font-size: 12px; color: var(--text-secondary); }

/* 入场动效：依次浮起 */
.anim-item {
  animation: float-up 0.4s cubic-bezier(0.2, 0, 0, 1) both;
  animation-delay: var(--d, 0s);
}
</style>
