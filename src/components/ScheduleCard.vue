<template>
  <div class="schedule-card" :class="{ done: item.done }" @click="$emit('click', item)">
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
</template>

<script setup>
// 日程卡片（首页今日日程 / 日程列表共用，保证两处样式一致）
defineProps({
  item: { type: Object, required: true },
})
defineEmits(['click'])

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

const typeLabel = { task: '待办', call: '通话', meeting: '面谈' }

function isOverdue(item) {
  return !item.done && item.endTime && new Date(item.endTime).getTime() < Date.now()
}

function getReminderOffset(reminderIso, startIso) {
  const mins = Math.round((new Date(startIso) - new Date(reminderIso)) / 60000)
  if (mins < 60) return `${mins} 分钟`
  if (mins < 1440) return `${Math.round(mins / 60)} 小时`
  return `${Math.round(mins / 1440)} 天`
}

// 日程类型图标：内联 SVG，颜色与「功能域色板」一致
function typeIcon(type) {
  if (type === 'call') return '<svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M20 15.5C18.8 15.5 17.5 15.3 16.4 14.9C16 14.7 15.5 14.8 15.2 15.1L13.5 16.8C11.3 15.7 9.2 13.6 8.1 11.4L9.8 9.7C10.1 9.4 10.2 8.9 10 8.5C9.6 7.4 9.4 6.1 9.4 4.9C9.4 4.4 8.9 4 4.9 4H4.9C4.4 4 4 4.4 4 4.9C4 13.8 11.1 21 20 21C20.5 21 21 20.6 21 20.1V16.6C21 16.1 20.6 15.5 20 15.5Z" fill="#378ADD"/></svg>'
  if (type === 'meeting') return '<svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M12 12C14.2 12 16 10.2 16 8C16 5.8 14.2 4 12 4C9.8 4 8 5.8 8 8C8 10.2 9.8 12 12 12ZM12 14C8.7 14 2 15.7 2 19V21H22V19C22 15.7 15.3 14 12 14Z" fill="#7F77DD"/></svg>'
  return '<svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M9 16.2L4.8 12L3.4 13.4L9 19L21 7L19.6 5.6L9 16.2Z" fill="#2563EB"/></svg>'
}
</script>

<style scoped>
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
  cursor: pointer;
}
.schedule-card:active { transform: scale(0.99); background: var(--bg-card-hover); }
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
</style>
