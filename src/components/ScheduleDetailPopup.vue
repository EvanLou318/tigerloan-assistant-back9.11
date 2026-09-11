<template>
  <van-popup
    :show="show"
    position="bottom"
    round
    teleport="body"
    :z-index="2200"
    class="detail-popup"
    @update:show="(v) => emit('update:show', v)"
  >
    <template v-if="item">
      <div class="dp-handle"></div>
      <div class="dp-head">
        <div class="dp-title">
          <span class="dp-type" v-html="typeIcon(item.type)"></span>
          <span class="dp-title-text">{{ item.title }}</span>
        </div>
        <AppIcon name="close" class="dp-close" @click="close" />
      </div>

      <!-- 标签行 -->
      <div class="dp-tags">
        <span class="dp-tag" :class="`dp-tag-${item.priority}`">{{ prioFullText(item.priority) }}</span>
        <span class="dp-tag dp-tag-type">{{ typeLabel[item.type] || '待办' }}</span>
        <span class="dp-tag" :class="item.done ? 'dp-tag-done' : 'dp-tag-open'">
          <AppIcon :name="item.done ? 'check-circle' : 'clock'" :size="12" />
          {{ item.done ? '已完成' : '未完成' }}
        </span>
      </div>

      <!-- 信息区 -->
      <div class="dp-info">
        <div class="dp-row">
          <AppIcon name="clock" class="dp-ic" />
          <span class="dp-lbl">时间</span>
          <span class="dp-val">{{ formatFullDate(item.startTime) }} - {{ formatTime(item.endTime) }}</span>
        </div>
        <div class="dp-row" v-if="item.location">
          <AppIcon name="map-pin" class="dp-ic" />
          <span class="dp-lbl">地点</span>
          <span class="dp-val">{{ item.location }}</span>
        </div>
        <div class="dp-row" v-if="item.customerName">
          <AppIcon name="user" class="dp-ic" />
          <span class="dp-lbl">客户</span>
          <span class="dp-val">{{ item.customerName }}</span>
        </div>
        <div class="dp-row" v-if="item.reminderTime">
          <AppIcon name="bell" class="dp-ic" />
          <span class="dp-lbl">提醒</span>
          <span class="dp-val">提前 {{ getReminderOffset(item.reminderTime, item.startTime) }}</span>
        </div>
        <div class="dp-row dp-row-note" v-if="item.remark">
          <AppIcon name="file-text" class="dp-ic" />
          <span class="dp-lbl">备注</span>
          <span class="dp-val">{{ item.remark }}</span>
        </div>
      </div>

      <!-- 操作区 -->
      <div class="dp-actions">
        <van-button
          v-if="!item.done"
          round block type="primary"
          :loading="acting"
          loading-text="处理中..."
          @click="$emit('toggle', item)"
        >
          <AppIcon name="check-circle" /> 标记完成
        </van-button>
        <van-button
          v-else
          round block
          class="dp-restore"
          :loading="acting"
          loading-text="处理中..."
          @click="$emit('toggle', item)"
        >
          <AppIcon name="refresh" /> 恢复未完成
        </van-button>
        <van-button plain round block class="dp-delete" @click="$emit('delete', item)">删除日程</van-button>

        <div v-if="showMore" class="dp-more" @click="goList">
          前往日程列表管理全部日程
          <AppIcon name="chevron-right" :size="12" />
        </div>
      </div>
    </template>
  </van-popup>
</template>

<script setup>
import AppIcon from './AppIcon.vue'

defineProps({
  show: { type: Boolean, default: false },
  // 当前展示的日程对象（由父组件从 store 中解析后传入）
  item: { type: Object, default: null },
  // 操作请求进行中（禁用重复点击 + 按钮 loading）
  acting: { type: Boolean, default: false },
  // 是否在底部提供「前往日程列表」入口（首页用；列表页自身不需要）
  showMore: { type: Boolean, default: false },
})

const emit = defineEmits(['update:show', 'toggle', 'delete', 'more'])

function close() {
  emit('update:show', false)
}

function goList() {
  emit('more')
  emit('update:show', false)
}

const typeLabel = { task: '待办', call: '通话', meeting: '面谈' }

function prioFullText(p) {
  if (p === 'P0') return '紧急 P0'
  if (p === 'P2') return '低优 P2'
  return '普通 P1'
}

function formatTime(iso) {
  if (!iso) return ''
  return new Date(iso).toTimeString().slice(0, 5)
}

function formatFullDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const week = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][d.getDay()]
  return `${d.getMonth() + 1}月${d.getDate()}日 ${week} ${d.toTimeString().slice(0, 5)}`
}

function getReminderOffset(reminderIso, startIso) {
  const mins = Math.round((new Date(startIso) - new Date(reminderIso)) / 60000)
  if (mins < 60) return `${mins} 分钟`
  if (mins < 1440) return `${Math.round(mins / 60)} 小时`
  return `${Math.round(mins / 1440)} 天`
}

// 日程类型图标：内联 SVG，颜色与「功能域色板」一致
function typeIcon(type) {
  if (type === 'call') {
    return '<svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M20 15.5C18.8 15.5 17.5 15.3 16.4 14.9C16 14.7 15.5 14.8 15.2 15.1L13.5 16.8C11.3 15.7 9.2 13.6 8.1 11.4L9.8 9.7C10.1 9.4 10.2 8.9 10 8.5C9.6 7.4 9.4 6.1 9.4 4.9C9.4 4.4 8.9 4 4.9 4H4.9C4.4 4 4 4.4 4 4.9C4 13.8 11.1 21 20 21C20.5 21 21 20.6 21 20.1V16.6C21 16.1 20.6 15.5 20 15.5Z" fill="#378ADD"/></svg>'
  }
  if (type === 'meeting') {
    return '<svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M12 12C14.2 12 16 10.2 16 8C16 5.8 14.2 4 12 4C9.8 4 8 5.8 8 8C8 10.2 9.8 12 12 12ZM12 14C8.7 14 2 15.7 2 19V21H22V19C22 15.7 15.3 14 12 14Z" fill="#7F77DD"/></svg>'
  }
  return '<svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M9 16.2L4.8 12L3.4 13.4L9 19L21 7L19.6 5.6L9 16.2Z" fill="#2563EB"/></svg>'
}
</script>

<style scoped>
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
/* 次级入口：轻量文字链，不抢主操作视觉权重 */
.dp-more {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2px;
  margin-top: 2px;
  padding: 8px 0;
  font-size: 12px;
  color: var(--color-primary);
  cursor: pointer;
}
.dp-more:active { opacity: 0.7; }
</style>
