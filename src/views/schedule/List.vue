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
          <AppIcon name="calendar" :size="26" color="var(--color-primary)" />
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

    <!-- 日期范围筛选：快捷区间 + 自定义；生效时在当前 tab 列表上求交集 -->
    <div class="filter-row">
      <button class="filter-chip" :class="{ active: quick === 'week' }" @click="applyQuick('week')">近7天</button>
      <button class="filter-chip" :class="{ active: quick === 'month' }" @click="applyQuick('month')">近30天</button>
      <button class="filter-chip" :class="{ active: quick === 'custom' }" @click="showCalendar = true">自定义</button>
      <div v-if="rangeFilter" class="range-badge" @click="clearFilter">
        {{ rangeLabel }}
        <span class="range-clear">✕</span>
      </div>
    </div>

    <!-- 列表 -->
    <van-pull-refresh v-model="refreshing" @refresh="onRefresh" success-text="已更新">
    <SkeletonList v-if="scheduleStore.loading && !refreshing" :count="3" />
    <div v-else class="schedule-list">
      <ScheduleCard
        v-for="item in displayList"
        :key="item.id"
        :item="item"
        @click="openDetail(item)"
      />

      <!-- 空状态 -->
      <div v-if="displayList.length === 0" class="empty-state">
        <div class="empty-ic-wrap">
          <AppIcon name="calendar" :size="40" color="var(--text-tertiary)" />
        </div>
        <p class="empty-text">{{ emptyText }}</p>
        <van-button round type="primary" size="small" @click="showMethodSheet = true">+ 新建日程</van-button>
      </div>
    </div>
    </van-pull-refresh>

    <!-- 新建日程：直接弹层选择录入方式 -->
    <div class="fab" @click="showMethodSheet = true">
      <AppIcon name="plus" :size="22" color="#FFFFFF" />
    </div>

    <!-- 日程详情底部面板（与首页共用组件） -->
    <ScheduleDetailPopup
      v-model:show="showDetail"
      :item="detailItem"
      :acting="acting"
      @toggle="markDone"
      @delete="confirmDelete"
    />

    <!-- 新建日程方式选择 -->
    <ScheduleMethodSheet v-model:show="showMethodSheet" />

    <!-- 自定义日期范围：保留 Vant 默认预选（今天~明天），保证打开即定位当前月 -->
    <van-calendar
      v-model:show="showCalendar"
      type="range"
      title="选择日期范围"
      :min-date="calendarMin"
      :max-date="calendarMax"
      teleport="body"
      @confirm="onCalendarConfirm"
    />
    </div>
  </MainLayout>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showSuccessToast, showToast, showConfirmDialog } from 'vant'
import { useAuthStore } from '../../stores/auth'
import { useScheduleStore } from '../../stores/schedule'
import MainLayout from '../../layouts/MainLayout.vue'
import SkeletonList from '../../components/SkeletonList.vue'
import ScheduleMethodSheet from '../../components/ScheduleMethodSheet.vue'
import ScheduleDetailPopup from '../../components/ScheduleDetailPopup.vue'
import ScheduleCard from '../../components/ScheduleCard.vue'

const router = useRouter()
const authStore = useAuthStore()
const scheduleStore = useScheduleStore()
const refreshing = ref(false)

// 新建日程方式选择弹层
const showMethodSheet = ref(false)

// 详情底部面板
const showDetail = ref(false)
const acting = ref(false)
const detailId = ref(null)
const detailItem = computed(() => scheduleStore.schedules.find((s) => s.id === detailId.value) || null)

function openDetail(item) {
  detailId.value = item.id
  showDetail.value = true
}

function closeDetail() {
  showDetail.value = false
  detailId.value = null
}

async function markDone(item) {
  if (acting.value) return
  acting.value = true
  try {
    await scheduleStore.toggleDone(item.id)
    showSuccessToast(item.done ? '已恢复为未完成' : '已标记完成')
    closeDetail()
  } catch (e) {
    showToast('操作失败，请重试')
  } finally {
    acting.value = false
  }
}

function confirmDelete(item) {
  showConfirmDialog({
    title: '删除日程',
    message: `确定删除「${item.title}」吗？删除后不可恢复。`,
    confirmButtonText: '删除',
    confirmButtonColor: '#F04438',
  })
    .then(async () => {
      try {
        await scheduleStore.deleteSchedule(item.id)
        showSuccessToast('已删除')
        closeDetail()
      } catch (e) {
        showToast('删除失败，请重试')
      }
    })
    .catch(() => {})
}

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
  // 日期范围筛选：以日程开始时间落在 [start, end] 内为准
  if (!rangeFilter.value) return list
  const { start, end } = rangeFilter.value
  return list.filter((s) => {
    if (!s.startTime) return false
    const t = new Date(s.startTime)
    return t >= start && t <= end
  })
})

// ---------- 日期范围筛选 ----------
const rangeFilter = ref(null) // { start: Date, end: Date } | null
const quick = ref('') // 'week' | 'month' | 'custom' | ''
const showCalendar = ref(false)
const calendarMin = (() => {
  const d = new Date()
  d.setFullYear(d.getFullYear() - 1)
  return d
})()
const calendarMax = (() => {
  const d = new Date()
  d.setFullYear(d.getFullYear() + 1)
  return d
})()

function applyQuick(kind) {
  // 再点一次同一个快捷区间 = 取消筛选
  if (quick.value === kind) {
    clearFilter()
    return
  }
  const start = new Date()
  start.setHours(0, 0, 0, 0)
  const end = new Date(start)
  end.setDate(end.getDate() + (kind === 'week' ? 7 : 30))
  end.setHours(23, 59, 59, 999)
  rangeFilter.value = { start, end }
  quick.value = kind
  // 「今日」tab 语义上已固定为今天，选了范围后切到「全部」才看得全
  if (scheduleStore.activeTab === 'today') scheduleStore.activeTab = 'all'
}

function onCalendarConfirm(range) {
  const [a, b] = range || []
  // 范围不完整（只选了起点就点确认）时直接关闭，不改动现有筛选
  if (!a || !b) {
    showCalendar.value = false
    return
  }
  const start = new Date(a)
  start.setHours(0, 0, 0, 0)
  const end = new Date(b)
  end.setHours(23, 59, 59, 999)
  rangeFilter.value = { start, end }
  quick.value = 'custom'
  showCalendar.value = false
  if (scheduleStore.activeTab === 'today') scheduleStore.activeTab = 'all'
}

function clearFilter() {
  rangeFilter.value = null
  quick.value = ''
}

const rangeLabel = computed(() => {
  if (!rangeFilter.value) return ''
  const fmt = (d) => `${d.getMonth() + 1}/${d.getDate()}`
  return `${fmt(rangeFilter.value.start)} ~ ${fmt(rangeFilter.value.end)}`
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
  if (rangeFilter.value) return '所选日期范围内暂无日程'
  if (scheduleStore.activeTab === 'today') return '今日暂无日程，享受轻松的一天'
  if (scheduleStore.activeTab === 'done') return '还没有完成的日程'
  return '没有待办日程，点击下方按钮新建'
})
</script>

<style scoped>
.schedule-page {
  background: var(--bg-base);
  min-height: 100vh;
  min-height: 100dvh;
  padding-top: env(safe-area-inset-top);
  padding-bottom: 16px;
}

/* 顶部信息卡 */
.hero-bar {
  margin: 16px 16px 12px;
  padding: 14px 16px;
  background: var(--d-schedule-50);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: var(--text-primary);
  box-shadow: none;
}
.hero-text { flex: 1; min-width: 0; }
.hero-title { font-size: 16px; font-weight: 700; margin-bottom: 4px; letter-spacing: -0.2px; color: var(--d-schedule-800); }
.hero-sub { font-size: 12px; color: var(--d-schedule-600); display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.hero-sub .dot { opacity: 0.6; }
.hero-sub .overdue { background: var(--d-alert-500); color: #FFFFFF; padding: 1px 8px; border-radius: 6px; }
.hero-illu {
  flex-shrink: 0;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: var(--d-schedule-100);
  display: flex;
  align-items: center;
  justify-content: center;
}

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
  background: var(--d-schedule-50);
  color: var(--d-schedule-800);
  font-weight: 600;
  box-shadow: none;
}
.tab-count {
  display: inline-block;
  margin-left: 4px;
  font-size: 11px;
  background: var(--d-schedule-100);
  padding: 0 6px;
  border-radius: 8px;
}
.tab-item:not(.active) .tab-count {
  background: var(--bg-input);
  color: var(--text-tertiary);
}

/* 日期范围筛选行 */
.filter-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 16px 12px;
  overflow-x: auto;
  scrollbar-width: none;
}
.filter-row::-webkit-scrollbar { display: none; }
.filter-chip {
  flex-shrink: 0;
  border: none;
  background: var(--bg-card);
  color: var(--text-secondary);
  font-size: 12px;
  padding: 6px 14px;
  border-radius: 20px;
  cursor: pointer;
  box-shadow: var(--shadow-card);
  transition: all 0.2s;
}
.filter-chip.active {
  background: var(--d-schedule-50);
  color: var(--d-schedule-800);
  font-weight: 600;
}
.range-badge {
  flex-shrink: 0;
  margin-left: auto;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: var(--d-schedule-800);
  background: var(--d-schedule-50);
  padding: 6px 12px;
  border-radius: 20px;
  cursor: pointer;
}
.range-clear {
  font-size: 11px;
  color: var(--d-schedule-600);
}

/* 列表 */
.schedule-list {
  padding: 0 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
/* 空状态 */
.empty-ic-wrap {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: var(--surface-container-low);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 4px;
}

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
  background: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 6px 18px rgba(37, 99, 235, 0.35);
  z-index: 10;
}
.fab:active { transform: scale(0.95); }
</style>
