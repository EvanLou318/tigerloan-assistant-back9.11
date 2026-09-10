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

    <!-- 日程详情底部面板 -->
    <van-popup v-model:show="showDetail" position="bottom" round class="detail-popup">
      <template v-if="detailItem">
        <div class="dp-handle"></div>
        <div class="dp-head">
          <div class="dp-title">
            <span class="dp-type" v-html="typeIcon(detailItem.type)"></span>
            <span class="dp-title-text">{{ detailItem.title }}</span>
          </div>
          <AppIcon name="close" class="dp-close" @click="showDetail = false" />
        </div>

        <div class="dp-tags">
          <span class="dp-tag" :class="`dp-tag-${detailItem.priority}`">{{ detailItem.priority === 'P0' ? '紧急 P0' : detailItem.priority === 'P1' ? '普通 P1' : '低优 P2' }}</span>
          <span class="dp-tag dp-tag-type">{{ typeLabel[detailItem.type] || '待办' }}</span>
          <span class="dp-tag" :class="detailItem.done ? 'dp-tag-done' : 'dp-tag-open'">
            <AppIcon :name="detailItem.done ? 'check-circle' : 'clock'" :size="12" />
            {{ detailItem.done ? '已完成' : '未完成' }}
          </span>
        </div>

        <div class="dp-info">
          <div class="dp-row">
            <AppIcon name="clock" class="dp-ic" />
            <span class="dp-lbl">时间</span>
            <span class="dp-val">{{ formatFullDate(detailItem.startTime) }} - {{ formatTime(detailItem.endTime) }}</span>
          </div>
          <div class="dp-row" v-if="detailItem.location">
            <AppIcon name="map-pin" class="dp-ic" />
            <span class="dp-lbl">地点</span>
            <span class="dp-val">{{ detailItem.location }}</span>
          </div>
          <div class="dp-row" v-if="detailItem.customerName">
            <AppIcon name="user" class="dp-ic" />
            <span class="dp-lbl">客户</span>
            <span class="dp-val">{{ detailItem.customerName }}</span>
          </div>
          <div class="dp-row" v-if="detailItem.reminderTime">
            <AppIcon name="bell" class="dp-ic" />
            <span class="dp-lbl">提醒</span>
            <span class="dp-val">提前 {{ getReminderOffset(detailItem.reminderTime, detailItem.startTime) }}</span>
          </div>
          <div class="dp-row dp-row-note" v-if="detailItem.remark">
            <AppIcon name="file-text" class="dp-ic" />
            <span class="dp-lbl">备注</span>
            <span class="dp-val">{{ detailItem.remark }}</span>
          </div>
        </div>

        <div class="dp-actions">
          <van-button
            v-if="!detailItem.done"
            round block type="primary"
            :loading="acting"
            loading-text="处理中..."
            @click="markDone(detailItem)"
          >
            <AppIcon name="check-circle" /> 标记完成
          </van-button>
          <van-button
            v-else
            round block
            class="dp-restore"
            :loading="acting"
            loading-text="处理中..."
            @click="markDone(detailItem)"
          >
            <AppIcon name="refresh" /> 恢复未完成
          </van-button>
          <van-button plain round block class="dp-delete" @click="confirmDelete(detailItem)">删除日程</van-button>
        </div>
      </template>
    </van-popup>

    <!-- 新建日程方式选择 -->
    <ScheduleMethodSheet v-model:show="showMethodSheet" />
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

function formatFullDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const week = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][d.getDay()]
  return `${d.getMonth() + 1}月${d.getDate()}日 ${week} ${d.toTimeString().slice(0, 5)}`
}

const typeLabel = { task: '待办', call: '通话', meeting: '面谈' }

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

function typeIcon(type) {
  if (type === 'call') return '<svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M20 15.5C18.8 15.5 17.5 15.3 16.4 14.9C16 14.7 15.5 14.8 15.2 15.1L13.5 16.8C11.3 15.7 9.2 13.6 8.1 11.4L9.8 9.7C10.1 9.4 10.2 8.9 10 8.5C9.6 7.4 9.4 6.1 9.4 4.9C9.4 4.4 8.9 4 4.9 4H4.9C4.4 4 4 4.4 4 4.9C4 13.8 11.1 21 20 21C20.5 21 21 20.6 21 20.1V16.6C21 16.1 20.6 15.5 20 15.5Z" fill="#0EA5A5"/></svg>'
  if (type === 'meeting') return '<svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M12 12C14.2 12 16 10.2 16 8C16 5.8 14.2 4 12 4C9.8 4 8 5.8 8 8C8 10.2 9.8 12 12 12ZM12 14C8.7 14 2 15.7 2 19V21H22V19C22 15.7 15.3 14 12 14Z" fill="#7C6CF0"/></svg>'
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

/* ============ 日程详情底部面板 ============ */
.detail-popup {
  background: var(--surface-container-lowest);
  border-radius: 20px 20px 0 0;
  padding: 10px 20px calc(24px + env(safe-area-inset-bottom));
  max-height: 82vh;
  overflow-y: auto;
}
.dp-handle {
  width: 36px;
  height: 4px;
  border-radius: 2px;
  background: var(--surface-container-high);
  margin: 0 auto 12px;
}
.dp-head {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 10px;
}
.dp-title {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 17px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.4;
}
.dp-title-text { word-break: break-all; }
.dp-type { display: inline-flex; flex-shrink: 0; transform: scale(1.3); transform-origin: center; }
.dp-close {
  flex-shrink: 0;
  color: var(--text-tertiary);
  padding: 4px;
  margin: -4px;
  cursor: pointer;
}
.dp-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 14px; }
.dp-tag {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 999px;
  color: var(--text-secondary);
  background: var(--surface-container-high);
}
.dp-tag-P0 { background: var(--danger-container); color: var(--on-danger-container); }
.dp-tag-P1 { background: var(--primary-container); color: var(--on-primary-container); }
.dp-tag-P2 { background: var(--surface-container-high); color: var(--text-secondary); }
.dp-tag-type { background: var(--surface-container-high); color: var(--text-secondary); }
.dp-tag-done { background: rgba(16, 185, 129, 0.14); color: #059669; }
.dp-tag-open { background: rgba(37, 99, 235, 0.12); color: var(--color-primary); }

.dp-info {
  background: var(--surface-container);
  border-radius: 14px;
  padding: 4px 14px;
  margin-bottom: 16px;
}
.dp-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 11px 0;
  font-size: 13px;
}
.dp-row + .dp-row { border-top: 1px solid var(--surface-container-high); }
.dp-ic { color: var(--color-primary); margin-top: 2px; flex-shrink: 0; }
.dp-lbl {
  width: 32px;
  flex-shrink: 0;
  color: var(--text-tertiary);
  line-height: 1.6;
}
.dp-val {
  flex: 1;
  min-width: 0;
  color: var(--text-primary);
  line-height: 1.6;
  word-break: break-all;
}
.dp-row-note .dp-val { white-space: pre-wrap; }

.dp-actions { display: flex; flex-direction: column; gap: 10px; }
.dp-restore {
  border: 1px solid rgba(16, 185, 129, 0.5);
  color: #059669;
  background: #fff;
}
.dp-delete {
  color: var(--color-danger);
  border-color: rgba(239, 68, 68, 0.35);
}
</style>
