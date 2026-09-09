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
        <div class="method-icon">
          <AppIcon :name="action.icon" :size="22" color="var(--color-primary)" />
        </div>
        <div class="method-info">
          <div class="method-name">{{ action.name }}</div>
          <div class="method-desc">{{ action.desc }}</div>
        </div>
        <AppIcon name="chevron-right" color="#94A3B8" />
      </div>
    </template>
  </van-action-sheet>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const props = defineProps({
  show: { type: Boolean, default: false },
  // 父组件可附加跳转参数（如从客户详情进入时携带 customerId/customerName）
  extraQuery: { type: Object, default: null },
})
const emit = defineEmits(['update:show'])

const router = useRouter()
const route = useRoute()
const visible = ref(false)

watch(
  () => props.show,
  (val) => {
    visible.value = val
  }
)
watch(visible, (val) => emit('update:show', val))

const methods = [
  { name: '文本录入', desc: '手动填写标题、时间、地点', method: 'text', icon: 'edit' },
  { name: '语音录入', desc: '口述日程，AI 自动识别时间与优先级', method: 'voice', icon: 'mic' },
  { name: '手写录入', desc: '手写便签，AI 识别后生成日程', method: 'handwriting', icon: 'pen' },
]

function onSelect(action) {
  visible.value = false
  // 透传当前页携带的查询参数（如客户详情页的 customerId/customerName），仅替换 mode
  const { mode: _prevMode, ...rest } = route.query
  const extra = props.extraQuery || {}
  router.push({ path: '/schedules/create', query: { ...rest, ...extra, mode: action.method } })
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
  background: var(--primary-container);
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
