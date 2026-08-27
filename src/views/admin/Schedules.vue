<template>
  <div class="page">
    <div class="toolbar">
      <div class="filter-tabs">
        <button
          v-for="t in ['all', 'todo', 'done']"
          :key="t"
          class="filter-tab"
          :class="{ active: filter === t }"
          @click="filter = t"
        >
          {{ { all: '全部', todo: '待办', done: '已完成' }[t] }}
        </button>
      </div>
      <span class="count-badge">共 {{ filtered.length }} 条日程</span>
    </div>

    <div class="panel">
      <table class="data-table">
        <thead>
          <tr>
            <th>标题</th>
            <th>类型</th>
            <th>优先级</th>
            <th>开始时间</th>
            <th>关联客户</th>
            <th>地点</th>
            <th>创建方式</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in filtered" :key="s.id" :class="{ dim: s.done }">
            <td class="name-cell">{{ s.title }}</td>
            <td><span class="type-tag" :class="s.type">{{ typeLabel[s.type] || '待办' }}</span></td>
            <td><span class="prio" :class="s.priority?.toLowerCase()">{{ s.priority }}</span></td>
            <td class="time-cell">{{ fmtDT(s.startTime) }}</td>
            <td>{{ s.customerName || '--' }}</td>
            <td>{{ s.location || '--' }}</td>
            <td><span class="tag">{{ sourceLabel[s.source] || '手动' }}</span></td>
            <td>
              <span class="status" :class="s.done ? 'off' : 'on'">{{ s.done ? '已完成' : '待办' }}</span>
            </td>
            <td class="op-cell">
              <button class="link-btn" @click="toggleDone(s)">{{ s.done ? '标为待办' : '标为完成' }}</button>
              <button class="link-btn danger" @click="remove(s)">删除</button>
            </td>
          </tr>
          <tr v-if="!filtered.length">
            <td colspan="9" class="empty-cell">暂无日程</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { showConfirmDialog, showSuccessToast, showToast } from 'vant'
import { fetchSchedules, updateSchedule, deleteSchedule } from '../../api/schedules'

const schedules = ref([])
const filter = ref('all')

const filtered = computed(() => {
  return schedules.value.filter((s) => {
    if (filter.value === 'todo') return !s.done
    if (filter.value === 'done') return s.done
    return true
  })
})

const typeLabel = { task: '待办', call: '通话', meeting: '面谈' }
const sourceLabel = { text: '手动', voice: '语音', handwriting: '手写' }

function fmtDT(iso) {
  if (!iso) return '--'
  const d = new Date(iso)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getMonth() + 1}/${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

async function toggleDone(s) {
  try {
    await updateSchedule(s.id, { done: !s.done })
    s.done = !s.done
    showSuccessToast(s.done ? '已标为完成' : '已标为待办')
  } catch (e) {
    showToast(e.message || '操作失败')
  }
}

async function remove(s) {
  try {
    await showConfirmDialog({
      title: '删除日程',
      message: `确定删除日程「${s.title}」吗？`,
    })
  } catch {
    return
  }
  try {
    await deleteSchedule(s.id)
    schedules.value = schedules.value.filter((x) => x.id !== s.id)
    showSuccessToast('已删除')
  } catch (e) {
    showToast(e.message || '删除失败')
  }
}

onMounted(async () => {
  try {
    schedules.value = await fetchSchedules()
    // 按开始时间倒序，最近的在前
    schedules.value.sort((a, b) => new Date(b.startTime) - new Date(a.startTime))
  } catch (e) { /* 拦截器已提示 */ }
})
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 14px;
}

.filter-tabs {
  display: flex;
  background: #EBEEF6;
  border-radius: 10px;
  padding: 3px;
}

.filter-tab {
  border: none;
  background: transparent;
  padding: 7px 16px;
  font-size: 13px;
  color: #5A6A8F;
  border-radius: 8px;
  cursor: pointer;
}

.filter-tab.active {
  background: #fff;
  color: #17233D;
  font-weight: 600;
  box-shadow: 0 1px 4px rgba(23, 35, 61, 0.12);
}

.count-badge {
  font-size: 12px;
  color: #7C8DB5;
  margin-left: auto;
}

.panel {
  background: #fff;
  border-radius: 14px;
  padding: 8px 16px 16px;
  box-shadow: 0 2px 10px rgba(23, 35, 61, 0.05);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.data-table th {
  text-align: left;
  padding: 12px;
  color: #7C8DB5;
  font-weight: 500;
  border-bottom: 1px solid #EDF0F7;
  white-space: nowrap;
}

.data-table td {
  padding: 12px;
  border-bottom: 1px solid #F4F6FB;
  color: #3D4A6B;
}

.data-table tr.dim td {
  color: #B3BdD4;
}

.name-cell {
  font-weight: 600;
  color: #17233D;
  white-space: nowrap;
}

.type-tag {
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 999px;
  white-space: nowrap;
}

.type-tag.call {
  background: #E6F7FD;
  color: #0AA5C9;
}

.type-tag.meeting {
  background: #F0EDFF;
  color: #7C5CFC;
}

.type-tag.task {
  background: #EBF1FF;
  color: #2E6BFF;
}

.prio {
  font-size: 12px;
  font-weight: 700;
}

.prio.p0 {
  color: #EF5350;
}

.prio.p1 {
  color: #F59E0B;
}

.prio.p2 {
  color: #98A5C3;
}

.time-cell {
  color: #5A6A8F;
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
}

.tag {
  background: #F0F3FA;
  color: #5A6A8F;
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 999px;
  white-space: nowrap;
}

.status {
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 999px;
  white-space: nowrap;
}

.status.on {
  background: #EBF1FF;
  color: #2E6BFF;
}

.status.off {
  background: #E6F7F1;
  color: #00A884;
}

.op-cell {
  white-space: nowrap;
}

.link-btn {
  border: none;
  background: none;
  color: #2E6BFF;
  font-size: 13px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
}

.link-btn:hover {
  background: #EBF1FF;
}

.link-btn.danger {
  color: #EF5350;
}

.link-btn.danger:hover {
  background: #FDEBEE;
}

.empty-cell {
  text-align: center;
  color: #98A5C3;
  padding: 30px !important;
}
</style>
