// 全局语音输入面板状态（非 Pinia，模块单例，供任意输入框唤起）
import { reactive } from 'vue'

export const voiceState = reactive({
  visible: false,
  label: '',      // 当前输入框字段名，如「客户姓名」
  sample: '',     // mock 演示时的期望转写文本（真实 ASR 由后端按录音返回）
  onConfirm: null,
})

export function openVoiceInput(opts = {}) {
  voiceState.label = opts.label || ''
  voiceState.sample = opts.sample || ''
  voiceState.onConfirm = typeof opts.onConfirm === 'function' ? opts.onConfirm : null
  voiceState.visible = true
}

export function closeVoiceInput() {
  voiceState.visible = false
  voiceState.onConfirm = null
}
