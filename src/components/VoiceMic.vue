<template>
  <span
    class="voice-mic-btn"
    :title="`语音输入${label ? '：' + label : ''}`"
    @click.stop.prevent="open"
    @mousedown.stop.prevent
  >
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
      <path d="M12 14C13.1 14 14 13.1 14 12V6C14 4.9 13.1 4 12 4C10.9 4 10 4.9 10 6V12C10 13.1 10.9 14 12 14Z" fill="#2E6BFF" />
      <path d="M17 12C17 14.8 14.8 17 12 17C9.2 17 7 14.8 7 12H5C5 15.3 7.4 18.1 10.5 18.8V22H13.5V18.8C16.6 18.1 19 15.3 19 12H17Z" fill="#2E6BFF" />
    </svg>
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
