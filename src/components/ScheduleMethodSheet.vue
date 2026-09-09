<template>
  <van-action-sheet
    v-model:show="visible"
    title="选择录入方式"
    description="AI 将自动识别日程内容，减少手动输入"
    :actions="methods"
    cancel-text="取消"
    close-on-click-action
    @select="onSelect"
  >
    <template #action="{ action }">
      <div class="method-option">
        <div class="method-icon" :style="{ background: action.bg }">
          <span v-html="action.svg"></span>
        </div>
        <div class="method-info">
          <div class="method-name">{{ action.name }}</div>
          <div class="method-desc">{{ action.desc }}</div>
        </div>
        <van-icon name="arrow" color="#94A3B8" />
      </div>
    </template>
  </van-action-sheet>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  show: { type: Boolean, default: false },
})
const emit = defineEmits(['update:show'])

const router = useRouter()
const visible = ref(false)

watch(
  () => props.show,
  (val) => {
    visible.value = val
  }
)
watch(visible, (val) => emit('update:show', val))

const methods = [
  {
    name: '文本录入',
    desc: '手动填写标题、时间、地点',
    method: 'text',
    bg: 'linear-gradient(135deg, rgba(59,130,246,0.15), rgba(6,182,212,0.05))',
    svg: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none"><path d="M5 4V9H10V20H14V9H19V4H5Z" fill="#3B82F6"/></svg>',
  },
  {
    name: '语音录入',
    desc: '口述日程，AI 自动识别时间与优先级',
    method: 'voice',
    bg: 'linear-gradient(135deg, rgba(6,182,212,0.15), rgba(59,130,246,0.05))',
    svg: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none"><path d="M12 14C13.1 14 14 13.1 14 12V6C14 4.9 13.1 4 12 4C10.9 4 10 4.9 10 6V12C10 13.1 10.9 14 12 14ZM17 12C17 14.8 14.8 17 12 17C9.2 17 7 14.8 7 12H5C5 15.3 7.4 18.1 10.5 18.8V22H13.5V18.8C16.6 18.1 19 15.3 19 12H17Z" fill="#06B6D4"/></svg>',
  },
  {
    name: '手写录入',
    desc: '手写便签，AI 识别后生成日程',
    method: 'handwriting',
    bg: 'linear-gradient(135deg, rgba(139,92,246,0.15), rgba(6,182,212,0.05))',
    svg: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none"><path d="M3 17.25V21H6.75L17.81 9.94L14.06 6.19L3 17.25ZM20.71 7.04C21.1 6.65 21.1 6.02 20.71 5.63L18.37 3.29C17.98 2.9 17.35 2.9 16.96 3.29L15.13 5.12L18.88 8.87L20.71 7.04Z" fill="#8B5CF6"/></svg>',
  },
]

function onSelect(action) {
  visible.value = false
  router.push(`/schedules/create?mode=${action.method}`)
}
</script>

<style scoped>
.method-option {
  display: flex;
  align-items: center;
  gap: 14px;
  text-align: left;
}

.method-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border: none;
}

.method-info {
  flex: 1;
}

.method-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.method-desc {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 2px;
}
</style>
