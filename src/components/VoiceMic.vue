<template>
  <span
    class="voice-mic-btn"
    :title="`语音输入${label ? '：' + label : ''}`"
    @click.stop.prevent="open"
    @mousedown.stop.prevent
  >
    <van-icon name="mic" :size="size" color="#2E6BFF" />
    <span class="vm-ring"></span>
  </span>
</template>

<script setup>
import { openVoiceInput } from '../stores/voiceInput'

const props = defineProps({
  label: { type: String, default: '' },   // 字段名，显示在面板标题，如「客户姓名」
  sample: { type: String, default: '' },  // 演示/期望转写文本（mock 环境原样返回）
})
const emit = defineEmits(['confirm'])

function open() {
  openVoiceInput({
    label: props.label,
    sample: props.sample,
    onConfirm: (text) => emit('confirm', text),
  })
}
</script>

<style scoped>
.voice-mic-btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #EBF1FF;
  cursor: pointer;
  transition: background 0.15s ease, transform 0.12s ease;
  flex: none;
}
.voice-mic-btn:active {
  background: #D8E4FF;
  transform: scale(0.9);
}
.vm-ring {
  position: absolute;
  inset: -3px;
  border-radius: 50%;
  border: 1px solid rgba(46, 107, 255, 0.25);
  opacity: 0;
}
.voice-mic-btn:active .vm-ring {
  animation: vmPulse 0.4s ease-out forwards;
}
@keyframes vmPulse {
  0% { transform: scale(0.8); opacity: 1; }
  100% { transform: scale(1.4); opacity: 0; }
}
</style>
