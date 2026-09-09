<template>
  <van-action-sheet
    v-model:show="visible"
    title="选择录入方式"
    description="AI 将自动提取产品信息，减少手动录入"
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
  { name: '文本录入', desc: '手动填写表单', method: 'text', icon: 'edit' },
  { name: '语音录入', desc: '口述产品信息，AI 自动识别', method: 'voice', icon: 'mic' },
  { name: '图片录入', desc: '上传产品海报/宣传单照片', method: 'image', icon: 'image' },
  { name: 'PDF录入', desc: '上传产品说明文档', method: 'pdf', icon: 'file-text' },
]

function onSelect(action) {
  visible.value = false
  router.push(`/products/create?method=${action.method}`)
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
  background: var(--primary-container);
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
