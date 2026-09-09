<template>
  <MainLayout>
    <div class="schedule-page">
      <!-- 顶部渐变头部 -->
      <div class="hero-bar">
        <div class="hero-text">
          <div class="hero-title">{{ greetingText }}，{{ userInfo?.name || '李经理' }}</div>
          <div class="hero-sub">
            <span>今日 {{ scheduleStore.todayCount }} 项日程</span>
            <span class="dot" v-if="scheduleStore.overdueCount > 0">·</span>
            <span class="overdue" v-if="scheduleStore.overdueCount > 0">{{ scheduleStore.overdueCount }} 项已逾期</span>
          </div>
        </div>
        <div class="hero-illu">
        <svg width="80" height="80" viewBox="0 0 80 80" fill="none">
          <circle cx="40" cy="40" r="36" fill="rgba(59,130,246,0.08)" />
          <rect x="20" y="22" width="40" height="38" rx="6" fill="rgba(59,130,246,0.18)" />
          <rect x="24" y="30" width="32" height="4" rx="2" fill="#3B82F6" />
          <rect x="24" y="38" width="22" height="4" rx="2" fill="rgba(59,130,246,0.5)" />
          <rect x="24" y="46" width="28" height="4" rx="2" fill="rgba(59,130,246,0.5)" />
          <circle cx="58" cy="22" r="8" fill="#06B6D4" />
          <path d="M55 22 L57 24 L61 20" stroke="#FFFFFF" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" fill="none" />
        </svg>
      </div>
    </div>

    <!-- Tabs -->
    <div class="tabs-wrap">
      <div class="tab-item" :class="{ active: scheduleStore.activeTab === 'today' }" @click="scheduleStore.activeTab = 'today'">
        今日 <span class="tab-count">{{ scheduleStore.todayCount }}</span>
      </div>
      <div class="tab-item" :class="{ active: scheduleStore.activeTab === 'all' }" @click="scheduleStore.activeTab = 'all'">
        全部 <span class="tab-count">{{ scheduleStore.pendingCount }}</span>
      </div>
      <div class="tab-item" :class="{ active: scheduleStore.activeTab === 'done' }" @click="scheduleStore.activeTab = 'done'">
        已完成
      </div>
    </div>

    <!-- 列表 -->
    <van-pull-refresh v-model="refreshing" @refresh="onRefresh" success-text="已更新">
    <SkeletonList v-if="scheduleStore.loading && !refreshing" :count="3" />
    <div v-else class="schedule-list">
      <div
        v-for="item in displayList"
        :key="item.id"
        class="schedule-card"
        :class="{ done: item.done }"
        @click="onItemClick(item)"
      >
        <div class="time-block" :class="`prio-${item.priority}`">
          <div class="time-range">{{ formatTime(item.startTime) }}-{{ formatTime(item.endTime) }}</div>
          <div class="prio-tag">{{ item.priority }}</div>
        </div>
        <div class="info">
          <div class="title">
            <span class="type-icon" v-html="typeIcon(item.type)"></span>
            {{ item.title }}
          </div>
          <div class="meta">
            <span v-if="item.location" class="meta-item">
              <van-icon name="location-o" size="12" /> {{ item.location }}
            </span>
            <span v-if="item.customerName" class="meta-item">
              <van-icon name="contact" size="12" /> {{ item.customerName }}
            </span>
            <span v-if="item.reminderTime" class="meta-item">
              <van-icon name="bell" size="12" /> 提前 {{ getReminderOffset(item.reminderTime, item.startTime) }}
            </span>
          </div>
        </div>
        <div class="check-box" @click.stop="onToggleDone(item)">
          <van-icon :name="item.done ? 'success' : 'circle'" :color="item.done ? '#10B981' : '#CBD5E1'" size="22" />
        </div>
      </div>

      <!-- 空状态 -->
      <div v-if="displayList.length === 0" class="empty-state">
        <svg width="120" height="120" viewBox="0 0 120 120" fill="none">
          <circle cx="60" cy="60" r="50" fill="rgba(59,130,246,0.06)" />
          <rect x="30" y="36" width="60" height="54" rx="8" fill="rgba(59,130,246,0.1)" />
          <rect x="30" y="36" width="60" height="14" rx="8" fill="rgba(59,130,246,0.2)" />
          <circle cx="42" cy="43" r="3" fill="#3B82F6" />
          <circle cx="50" cy="43" r="3" fill="#06B6D4" />
          <circle cx="58" cy="43" r="3" fill="#8B5CF6" />
          <rect x="38" y="58" width="44" height="3" rx="1.5" fill="rgba(59,130,246,0.3)" />
          <rect x="38" y="66" width="32" height="3" rx="1.5" fill="rgba(59,130,246,0.3)" />
          <rect x="38" y="74" width="36" height="3" rx="1.5" fill="rgba(59,130,246,0.3)" />
        </svg>
        <p class="empty-text">{{ emptyText }}</p>
        <van-button round type="primary" size="small" @click="$router.push('/schedules/create')">+ 新建日程</van-button>
      </div>
    </div>
    </van-pull-refresh>

    <!-- 新建 FAB -->
    <div class="fab" @click="$router.push('/schedules/create')">
      <van-icon name="plus" size="22" color="#FFFFFF" />
    </div>
    </div>
  </MainLayout>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showSuccessToast, showConfirmDialog } from 'vant'
import { useAuthStore } from '../../stores/auth'
import { useScheduleStore } from '../../stores/schedule'
import MainLayout from '../../layouts/MainLayout.vue'
import SkeletonList from '../../components/SkeletonList.vue'

const router = useRouter()
const authStore = useAuthStore()
const scheduleStore = useScheduleStore()
const refreshing = ref(false)

onMounted(() => {
  scheduleStore.loadSchedules(true)
})

async function onRefresh() {
  try {
    await scheduleStore.loadSchedules(true)
  } finally {
    refreshing.value = false
  }
}

const userInfo = authStore.userInfo

const displayList = computed(() => {
  const list = scheduleStore.displaySchedules
  // 按日期分组，这里只展示分组的连续列表
  return list
})

const hour = new Date().getHours()
const greetingText = computed(() => {
  if (hour < 6) return '凌晨好'
  if (hour < 12) return '早上好'
  if (hour < 14) return '中午好'
  if (hour < 18) return '下午好'
  return '晚上好'
})

const emptyText = computed(() => {
  if (scheduleStore.activeTab === 'today') return '今日暂无日程，享受轻松的一天'
  if (scheduleStore.activeTab === 'done') return '还没有完成的日程'
  return '没有待办日程，点击下方按钮新建'
})

function formatTime(iso) {
  const d = new Date(iso)
  return d.toTimeString().slice(0, 5)
}

function getReminderOffset(reminderIso, startIso) {
  const mins = Math.round((new Date(startIso) - new Date(reminderIso)) / 60000)
  if (mins < 60) return `${mins} 分钟`
  if (mins < 1440) return `${Math.round(mins / 60)} 小时`
  return `${Math.round(mins / 1440)} 天`
}

function typeIcon(type) {
  if (type === 'call') return '<svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M20 15.5C18.8 15.5 17.5 15.3 16.4 14.9C16 14.7 15.5 14.8 15.2 15.1L13.5 16.8C11.3 15.7 9.2 13.6 8.1 11.4L9.8 9.7C10.1 9.4 10.2 8.9 10 8.5C9.6 7.4 9.4 6.1 9.4 4.9C9.4 4.4 8.9 4 4.9 4H4.9C4.4 4 4 4.4 4 4.9C4 13.8 11.1 21 20 21C20.5 21 21 20.6 21 20.1V16.6C21 16.1 20.6 15.5 20 15.5Z" fill="#06B6D4"/></svg>'
  if (type === 'meeting') return '<svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M12 12C14.2 12 16 10.2 16 8C16 5.8 14.2 4 12 4C9.8 4 8 5.8 8 8C8 10.2 9.8 12 12 12ZM12 14C8.7 14 2 15.7 2 19V21H22V19C22 15.7 15.3 14 12 14Z" fill="#8B5CF6"/></svg>'
  return '<svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M9 16.2L4.8 12L3.4 13.4L9 19L21 7L19.6 5.6L9 16.2Z" fill="#3B82F6"/></svg>'
}

function onItemClick(item) {
  if (item.done) {
    showConfirmDialog({
      title: '日程详情',
      message: `${item.title}\n时间：${new Date(item.startTime).toLocaleString('zh-CN')}\n${item.location ? '地点：' + item.location + '\n' : ''}${item.remark || ''}`,
      confirmButtonText: '标记未完成',
      cancelButtonText: '关闭',
    })
      .then(() => {
        scheduleStore.toggleDone(item.id)
        showSuccessToast('已重置为未完成')
      })
      .catch(() => {})
    return
  }
  showConfirmDialog({
    title: '日程详情',
    message: `${item.title}\n时间：${new Date(item.startTime).toLocaleString('zh-CN')}\n${item.location ? '地点：' + item.location + '\n' : ''}${item.remark || ''}`,
    confirmButtonText: '标记完成',
    cancelButtonText: '关闭',
  })
    .then(() => {
      scheduleStore.toggleDone(item.id)
      showSuccessToast('已完成')
    })
    .catch(() => {})
}

function onToggleDone(item) {
  scheduleStore.toggleDone(item.id)
  showSuccessToast(item.done ? '已标记为未完成' : '已完成')
}
</script>

<style scoped>
.schedule-page {
  background: var(--bg-base);
  min-height: 100vh;
  min-height: 100dvh;
  padding-top: env(safe-area-inset-top);
  padding-bottom: 16px;
}

/* 顶部渐变条 */
.hero-bar {
  margin: 16px 16px 16px;
  padding: 16px 20px;
  background: linear-gradient(135deg, #3B82F6 0%, #06B6D4 100%);
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #FFFFFF;
  box-shadow: 0 6px 18px rgba(59, 130, 246, 0.18);
}
.hero-title { font-size: 16px; font-weight: 700; margin-bottom: 4px; }
.hero-sub { font-size: 12px; opacity: 0.9; display: flex; align-items: center; gap: 6px; }
.hero-sub .dot { opacity: 0.6; }
.hero-sub .overdue { background: rgba(255,255,255,0.22); padding: 1px 8px; border-radius: 4px; }
.hero-illu { flex-shrink: 0; }

/* Tabs */
.tabs-wrap {
  display: flex;
  background: var(--bg-card);
  margin: 0 16px 12px;
  padding: 4px;
  border-radius: 12px;
  box-shadow: var(--shadow-card);
}
.tab-item {
  flex: 1;
  text-align: center;
  padding: 8px 0;
  font-size: 14px;
  color: var(--text-secondary);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}
.tab-item.active {
  background: var(--color-primary);
  color: #FFFFFF;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
}
.tab-count {
  display: inline-block;
  margin-left: 4px;
  font-size: 11px;
  background: rgba(255,255,255,0.25);
  padding: 0 6px;
  border-radius: 8px;
}
.tab-item:not(.active) .tab-count {
  background: var(--bg-input);
  color: var(--text-tertiary);
}

/* 列表 */
.schedule-list {
  padding: 0 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.schedule-card {
  display: flex;
  align-items: stretch;
  gap: 12px;
  background: var(--bg-card);
  border-radius: var(--radius-md);
  padding: 14px;
  box-shadow: var(--shadow-card);
  border: none;
  transition: all 0.2s;
}
.schedule-card:active { transform: scale(0.99); }
.schedule-card.done { opacity: 0.55; }
.schedule-card.done .title { text-decoration: line-through; }

.time-block {
  flex-shrink: 0;
  width: 68px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 6px 4px;
  border-radius: 10px;
  background: rgba(59, 130, 246, 0.08);
  position: relative;
}
.time-block.prio-P0 { background: var(--danger-container); }
.time-block.prio-P1 { background: var(--primary-container); }
.time-block.prio-P2 { background: var(--surface-container-high); }
.time-range {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-primary);
  white-space: nowrap;
  letter-spacing: -0.2px;
  line-height: 1.2;
}
.prio-tag {
  font-size: 11px;
  font-weight: 700;
  margin-top: 3px;
  padding: 0 6px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.75);
  color: var(--text-secondary);
  border: none;
  line-height: 1.5;
}
.time-block.prio-P0 .prio-tag { color: var(--on-danger-container); }
.time-block.prio-P1 .prio-tag { color: var(--on-primary-container); }
.time-block.prio-P2 .prio-tag { color: var(--text-secondary); }

.info { flex: 1; min-width: 0; }
.title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 6px;
  display: flex;
  align-items: center;
  gap: 4px;
}
.type-icon { display: inline-flex; }
.meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 11px;
  color: var(--text-tertiary);
}
.meta-item { display: inline-flex; align-items: center; gap: 2px; }

.check-box {
  display: flex;
  align-items: center;
  padding: 0 4px;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 48px 16px;
  color: var(--text-tertiary);
}
.empty-text {
  font-size: 14px;
  margin: 12px 0 20px;
  color: var(--text-secondary);
}

/* FAB */
.fab {
  position: fixed;
  right: 16px;
  bottom: calc(80px + env(safe-area-inset-bottom));
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: linear-gradient(135deg, #3B82F6 0%, #06B6D4 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 6px 18px rgba(59, 130, 246, 0.35);
  z-index: 10;
}
.fab:active { transform: scale(0.95); }
</style>
