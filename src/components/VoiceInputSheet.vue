<template>
  <van-popup
    :show="voiceState.visible"
    position="bottom"
    round
    :style="{ background: 'transparent' }"
    @update:show="onShowChange"
    @closed="onClosed"
  >
    <div class="voice-sheet">
      <!-- 头部：标题一行 + 提示单独一行，避免互相挤压换行 -->
      <div class="vs-header">
        <div class="vs-title">
          <span class="vs-title-dot"></span>
          <span class="vs-title-text">语音输入</span>
          <span class="vs-field-tag" v-if="voiceState.label">{{ voiceState.label }}</span>
        </div>
        <div class="vs-sub" v-if="step === 'idle'">点击麦克风，说出{{ voiceState.label || '内容' }}，自动转成文字</div>
      </div>

      <!-- 状态主体 -->
      <div class="vs-stage">
        <!-- idle：待录音 -->
        <div v-if="step === 'idle'" class="vs-idle">
          <div class="mic-circle idle" @click="start">
            <AppIcon name="mic" :size="30" color="#FFFFFF" />
          </div>
          <div class="vs-hint">点击开始说话</div>
        </div>

        <!-- recording：录音中 -->
        <div v-else-if="step === 'recording'" class="vs-recording">
          <div class="mic-circle recording" @click="stop">
            <span class="mic-wave" v-for="i in 5" :key="i"></span>
            <AppIcon name="mic" :size="30" color="#FFFFFF" style="position: relative;" />
          </div>
          <div class="vs-hint red">正在聆听… 点击结束</div>
          <div class="vs-timer">{{ recTime }}s<span v-if="recTime >= 18"> 即将自动结束</span></div>
        </div>

        <!-- transcribing：转写中 -->
        <div v-else-if="step === 'transcribing'" class="vs-transcribing">
          <van-loading color="#2563EB" size="34" />
          <div class="vs-hint">语音转写中…</div>
        </div>

        <!-- done：结果确认 -->
        <div v-else class="vs-result">
          <div class="vs-result-head">
            <span class="vs-ok"><AppIcon name="check-circle" :size="14" color="#16A34A" /> 识别完成</span>
            <span class="vs-conf">置信度 {{ confidence }}%</span>
          </div>
          <textarea
            v-model="transcript"
            class="vs-textarea"
            rows="3"
            placeholder="识别文字，可手动修正"
          ></textarea>
          <div class="vs-result-actions">
            <button class="vs-btn ghost" @click="reset">重新录制</button>
            <button class="vs-btn primary" @click="fill">填入</button>
          </div>
        </div>
      </div>
    </div>
  </van-popup>
</template>

<script setup>
import { ref, onBeforeUnmount } from 'vue'
import { showToast, showSuccessToast } from 'vant'
import { voiceState, closeVoiceInput } from '../stores/voiceInput'
import { asr as asrApi, asrAudio } from '../api/ai'
import { startRecording } from '../utils/recorder'

const step = ref('idle') // idle | recording | transcribing | done
const recTime = ref(0)
const transcript = ref('')
const confidence = ref(0)
let recordTimer = null
let recorder = null // 真实录音句柄，null 表示当前无有效录音

const MAX_SEC = 20

function clearTimer() {
  if (recordTimer) {
    clearInterval(recordTimer)
    recordTimer = null
  }
}

async function start() {
  try {
    recorder = await startRecording()
  } catch (e) {
    // 麦克风不可用时不阻断业务：降级为「无录音演示模式」，仍走后端（mock 或已配真实供应商）
    showToast(`${e.message}，已切换为演示模式`)
    recorder = null
  }
  step.value = 'recording'
  recTime.value = 0
  recordTimer = setInterval(() => {
    recTime.value += 1
    if (recTime.value >= MAX_SEC) stop()
  }, 1000)
}

async function stop() {
  if (step.value !== 'recording') return
  clearTimer()
  if (recTime.value < 1) {
    recorder?.cancel()
    recorder = null
    step.value = 'idle'
    showToast('说话时间太短，请重试')
    return
  }
  step.value = 'transcribing'
  try {
    let res
    if (recorder) {
      // 真实录音 → 上传音频，由后端调阿里云智能语音交互转写
      const audio = await recorder.stop()
      recorder = null
      if (audio) {
        res = await asrAudio({
          blob: audio.blob,
          sampleRate: audio.sampleRate,
          text: voiceState.sample || undefined,
        })
      }
    }
    if (!res) {
      // 降级链路：后端 ASR 未配真实供应商时走 mock，返回该字段的示例口述文本
      res = await asrApi(voiceState.sample || undefined)
    }
    const text = (res.text || '').trim()
    if (!text) {
      // 阿里云对静音/非语音信号会返回空串，直接进结果页会让用户对着空白框发懵
      step.value = 'idle'
      showToast('没有听清，请靠近麦克风再说一遍')
      return
    }
    transcript.value = text
    confidence.value = Math.round((res.confidence || 0.9) * 100)
    step.value = 'done'
  } catch (e) {
    showToast(e.message || '语音识别失败')
    step.value = 'idle'
  }
}

function reset() {
  clearTimer()
  if (recorder) {
    recorder.cancel()
    recorder = null
  }
  step.value = 'idle'
  recTime.value = 0
  transcript.value = ''
  confidence.value = 0
}

function fill() {
  const text = (transcript.value || '').trim()
  if (!text) {
    showToast('识别内容为空')
    return
  }
  voiceState.onConfirm && voiceState.onConfirm(text)
  closeVoiceInput()
  showSuccessToast('已填入')
}

function onShowChange(v) {
  if (!v) closeVoiceInput()
}

function onClosed() {
  reset()
}

onBeforeUnmount(clearTimer)
</script>

<style scoped>
.voice-sheet {
  background: #ffffff;
  border-radius: 22px 22px 0 0;
  padding: 18px 20px calc(20px + env(safe-area-inset-bottom));
}

.vs-header {
  padding-bottom: 4px;
}
.vs-title {
  display: flex;
  align-items: center;
  font-size: 17px;
  font-weight: 600;
  color: var(--text-primary, #1F2937);
  gap: 6px;
  white-space: nowrap;
}
.vs-title-text {
  flex: none;
}
.vs-title-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-primary);
  flex: none;
}
.vs-field-tag {
  flex: none;
  font-size: 12px;
  font-weight: 500;
  color: #2E6BFF;
  background: #EBF1FF;
  border-radius: 999px;
  padding: 2px 10px;
  margin-left: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 60%;
}
.vs-sub {
  font-size: 12px;
  color: var(--text-tertiary, #94A3B8);
  margin-top: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.vs-stage {
  min-height: 226px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 18px 0 6px;
}

/* 圆形麦克风 */
.mic-circle {
  width: 84px;
  height: 84px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 10px 24px rgba(37, 99, 235, 0.28);
  transition: transform 0.15s ease;
  cursor: pointer;
}
.mic-circle:active { transform: scale(0.94); }
.mic-circle.idle {
  background: var(--color-primary);
}
.mic-circle.recording {
  background: #F04438;
  box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.35);
  animation: micPulse 1.4s infinite;
}
@keyframes micPulse {
  0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.35); }
  70% { box-shadow: 0 0 0 22px rgba(239, 68, 68, 0); }
  100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
}

.vs-hint {
  margin-top: 18px;
  font-size: 14px;
  color: var(--text-secondary, #475569);
}
.vs-hint.red { color: #F04438; }
.vs-timer {
  margin-top: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #F04438;
  font-variant-numeric: tabular-nums;
}

/* 录音波形 */
.mic-wave {
  position: absolute;
  width: 4px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.75);
  animation: waveBounce 0.9s ease-in-out infinite;
}
.mic-wave:nth-child(1) { height: 10px; margin-right: 20px; animation-delay: 0s; }
.mic-wave:nth-child(2) { height: 18px; margin-right: 10px; animation-delay: 0.15s; }
.mic-wave:nth-child(3) { height: 24px; animation-delay: 0.3s; }
.mic-wave:nth-child(4) { height: 18px; margin-left: 10px; animation-delay: 0.15s; }
.mic-wave:nth-child(5) { height: 10px; margin-left: 20px; animation-delay: 0s; }
@keyframes waveBounce {
  0%, 100% { transform: scaleY(0.6); opacity: 0.6; }
  50% { transform: scaleY(1); opacity: 1; }
}
.mic-circle.recording { position: relative; }

/* 结果 */
.vs-result { width: 100%; }
.vs-result-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}
.vs-ok {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  font-weight: 600;
  color: #16A34A;
}
.vs-conf {
  font-size: 12px;
  font-weight: 600;
  color: #2E6BFF;
  background: #EBF1FF;
  padding: 3px 10px;
  border-radius: 999px;
}
.vs-textarea {
  width: 100%;
  border: none;
  outline: none;
  resize: none;
  background: #F3F6FC;
  border-radius: 14px;
  padding: 12px 14px;
  font-size: 15px;
  line-height: 1.6;
  color: var(--text-primary, #1F2937);
  box-sizing: border-box;
}
.vs-result-actions {
  display: flex;
  gap: 12px;
  margin-top: 14px;
}
.vs-btn {
  flex: 1;
  height: 42px;
  border-radius: 999px;
  font-size: 15px;
  font-weight: 600;
  border: none;
  cursor: pointer;
  transition: opacity 0.15s ease;
}
.vs-btn:active { opacity: 0.85; }
.vs-btn.ghost {
  background: #F1F4F9;
  color: var(--text-secondary, #475569);
}
.vs-btn.primary {
  background: var(--color-primary);
  color: #FFFFFF;
  box-shadow: 0 6px 16px rgba(37, 99, 235, 0.25);
}

.vs-transcribing { flex-direction: column; gap: 14px; display: flex; align-items: center; }
.vs-idle, .vs-recording { display: flex; flex-direction: column; align-items: center; }
</style>
