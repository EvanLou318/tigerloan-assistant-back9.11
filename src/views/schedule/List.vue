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
      <div
        v-for="item in displayList"
        :key="item.id"
        class="schedule-card"
        :class="{ done: item.done }"
        @click="openDetail(item)"
      >
        <div class="prio-bar" :class="`prio-${item.priority}`"></div>
        <div class="time-col">
          <div class="t-start">{{ formatTime(item.startTime) }}</div>
          <div class="t-end">{{ formatTime(item.endTime) }}</div>
          <div class="t-date" :class="{ today: isToday(item) }">{{ formatDay(item.startTime) }}</div>
          <div v-if="isOverdue(item)" class="t-overdue">逾期</div>
        </div>
        <div class="info">
          <div class="title">
            <span class="type-icon" v-html="typeIcon(item.type)"></span>
            <span class="title-text">{{ item.title }}</span>
            <span class="prio-chip" :class="`prio-chip-${item.priority}`">{{ prioText(item.priority) }}</span>
          </div>
          <div class="meta">
            <span class="meta-text">{{ metaText(item) }}</span>
          </div>
        </div>
      </div>

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

function formatTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toTimeString().slice(0, 5)
}

function isToday(item) {
  if (!item.startTime) return true
  const d = new Date(item.startTime)
  const n = new Date()
  return d.getFullYear() === n.getFullYear() && d.getMonth() === n.getMonth() && d.getDate() === n.getDate()
}

function formatDay(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const n = new Date()
  const startOf = (x) => new Date(x.getFullYear(), x.getMonth(), x.getDate()).getTime()
  const diff = Math.round((startOf(d) - startOf(n)) / 86400000)
  if (diff === 0) return '今天'
  if (diff === 1) return '明天'
  if (diff === 2) return '后天'
  if (diff === -1) return '昨天'
  return `${d.getMonth() + 1}/${d.getDate()}`
}

function prioText(p) {
  return p === 'P0' ? '紧急' : p === 'P1' ? '普通' : '低优'
}

// 卡片元信息行：固定单行「客户 · 地点 · 提前提醒」；
// 三个字段都为空时回退展示类型，保证每张卡片都是同样的两行结构、高度一致
function metaText(item) {
  const parts = []
  if (item.customerName) parts.push(item.customerName)
  if (item.location) parts.push(item.location)
  if (item.reminderTime) parts.push(`提前 ${getReminderOffset(item.reminderTime, item.startTime)}`)
  if (parts.length === 0) parts.push(typeLabel[item.type] || '待办')
  return parts.join(' · ')
}

const now = Date.now()
function isOverdue(item) {
  return !item.done && item.endTime && new Date(item.endTime).getTime() < now
}

function getReminderOffset(reminderIso, startIso) {
  const mins = Math.round((new Date(startIso) - new Date(reminderIso)) / 60000)
  if (mins < 60) return `${mins} 分钟`
  if (mins < 1440) return `${Math.round(mins / 60)} 小时`
  return `${Math.round(mins / 1440)} 天`
}

const typeLabel = { task: '待办', call: '通话', meeting: '面谈' }

// 日程类型图标：内联 SVG，颜色与「功能域色板」一致
function typeIcon(type) {
  if (type === 'call') return '<svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M20 15.5C18.8 15.5 17.5 15.3 16.4 14.9C16 14.7 15.5 14.8 15.2 15.1L13.5 16.8C11.3 15.7 9.2 13.6 8.1 11.4L9.8 9.7C10.1 9.4 10.2 8.9 10 8.5C9.6 7.4 9.4 6.1 9.4 4.9C9.4 4.4 8.9 4 4.9 4H4.9C4.4 4 4 4.4 4 4.9C4 13.8 11.1 21 20 21C20.5 21 21 20.6 21 20.1V16.6C21 16.1 20.6 15.5 20 15.5Z" fill="#378ADD"/></svg>'
  if (type === 'meeting') return '<svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M12 12C14.2 12 16 10.2 16 8C16 5.8 14.2 4 12 4C9.8 4 8 5.8 8 8C8 10.2 9.8 12 12 12ZM12 14C8.7 14 2 15.7 2 19V21H22V19C22 15.7 15.3 14 12 14Z" fill="#7F77DD"/></svg>'
  return '<svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M9 16.2L4.8 12L3.4 13.4L9 19L21 7L19.6 5.6L9 16.2Z" fill="#2563EB"/></svg>'
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

.schedule-card {
  display: flex;
  align-items: stretch;
  overflow: hidden;
  background: var(--bg-card);
  border-radius: var(--radius-md);
  padding: 14px 14px 14px 0;
  box-shadow: var(--shadow-card);
  border: none;
  transition: all 0.2s;
}
.schedule-card:active { transform: scale(0.99); }
.schedule-card.done { opacity: 0.55; }
.schedule-card.done .title-text { text-decoration: line-through; }

.prio-bar {
  width: 4px;
  border-radius: 4px 0 0 4px;
  flex-shrink: 0;
  align-self: stretch;
}
.prio-bar.prio-P0 { background: var(--d-alert-500); }
.prio-bar.prio-P1 { background: var(--d-todo-500); }
.prio-bar.prio-P2 { background: var(--d-schedule-600); }

/* 时间列：开始时间突出、结束时间次级，不再用色块挤压 */
.time-col {
  flex-shrink: 0;
  width: 62px;
  padding: 2px 0 2px 10px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: flex-start;
}
.t-start {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.25;
  letter-spacing: -0.2px;
  font-variant-numeric: tabular-nums;
}
.t-end {
  margin-top: 2px;
  font-size: 12px;
  color: var(--text-tertiary);
  line-height: 1.3;
  font-variant-numeric: tabular-nums;
}
.t-date {
  margin-top: 4px;
  font-size: 11px;
  color: var(--d-schedule-600);
  background: var(--d-schedule-50);
  border-radius: 5px;
  padding: 1px 5px;
  white-space: nowrap;
}
/* 今日徽标用中性色，非今日用蓝色调；始终渲染保证时间列结构一致 */
.t-date.today {
  background: var(--surface-container-high);
  color: var(--text-secondary);
}
/* 逾期标记：贴着时间列，红色小字，与日期徽标同格式 */
.t-overdue {
  margin-top: 3px;
  font-size: 11px;
  font-weight: 600;
  color: var(--color-danger);
  background: var(--danger-container);
  border-radius: 5px;
  padding: 1px 5px;
  line-height: 1.45;
  white-space: nowrap;
}

.info {
  flex: 1;
  min-width: 0;
  padding-left: 12px;
  border-left: 1px solid var(--surface-container-high);
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 6px;
}
.title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 5px;
}
.title-text {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.prio-chip {
  flex-shrink: 0;
  font-size: 10px;
  font-weight: 700;
  line-height: 1.6;
  padding: 0 6px;
  border-radius: 5px;
  letter-spacing: 0.2px;
}
.prio-chip-P0 { background: var(--danger-container); color: var(--on-danger-container); }
.prio-chip-P1 { background: var(--d-todo-50); color: var(--d-todo-800); }
.prio-chip-P2 { background: var(--surface-container-high); color: var(--text-secondary); }
.type-icon { display: inline-flex; flex-shrink: 0; }
/* 元信息固定单行：超出省略，避免字段多时换行导致卡片高度参差 */
.meta {
  min-width: 0;
  overflow: hidden;
  font-size: 11px;
  color: var(--text-tertiary);
  line-height: 1.4;
}
.meta-text {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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
