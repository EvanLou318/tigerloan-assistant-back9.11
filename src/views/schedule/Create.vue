<template>
  <div class="page-container create-page">
    <van-nav-bar :title="pageTitle" left-arrow @click-left="onBack" />

    <!-- 1. 选择录入方式 -->
    <div v-if="step === 'select'" class="select-step">
      <div class="hero">
        <svg width="56" height="56" viewBox="0 0 64 64" fill="none">
          <circle cx="32" cy="32" r="28" fill="rgba(59,130,246,0.1)" />
          <rect x="20" y="20" width="24" height="26" rx="3" fill="rgba(59,130,246,0.2)" />
          <rect x="20" y="20" width="24" height="6" rx="3" fill="#3B82F6" />
          <circle cx="26" cy="23" r="1.5" fill="#FFFFFF" />
          <circle cx="30" cy="23" r="1.5" fill="#FFFFFF" />
          <rect x="24" y="32" width="16" height="2.5" rx="1" fill="rgba(59,130,246,0.5)" />
          <rect x="24" y="37" width="12" height="2.5" rx="1" fill="rgba(59,130,246,0.5)" />
          <circle cx="44" cy="42" r="6" fill="#06B6D4" />
          <path d="M41 42 L43 44 L47 40" stroke="#FFFFFF" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" fill="none" />
        </svg>
        <h3>新建日程</h3>
        <p>选择录入方式，AI 自动识别内容</p>
      </div>

      <div class="methods">
        <div class="method" @click="selectMode('text')">
          <div class="m-icon" style="background: rgba(59, 130, 246, 0.12);">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
              <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04a1 1 0 0 0 0-1.41l-2.34-2.34a1 1 0 0 0-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z" fill="#3B82F6" />
            </svg>
          </div>
          <div class="m-text">
            <div class="m-title">文本录入</div>
            <div class="m-desc">手动填写标题、时间、备注等</div>
          </div>
          <van-icon name="arrow" color="#94A3B8" />
        </div>

        <div class="method" @click="selectMode('voice')">
          <div class="m-icon" style="background: rgba(6, 182, 212, 0.12);">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
              <path d="M12 14C13.1 14 14 13.1 14 12V6C14 4.9 13.1 4 12 4C10.9 4 10 4.9 10 6V12C10 13.1 10.9 14 12 14ZM17 12C17 14.8 14.8 17 12 17C9.2 17 7 14.8 7 12H5C5 15.3 7.4 18.1 10.5 18.8V22H13.5V18.8C16.6 18.1 19 15.3 19 12H17Z" fill="#06B6D4" />
            </svg>
          </div>
          <div class="m-text">
            <div class="m-title">语音录入</div>
            <div class="m-desc">口述日程，AI 自动识别标题/时间/优先级</div>
          </div>
          <van-icon name="arrow" color="#94A3B8" />
        </div>
      </div>
    </div>

    <!-- 2. 语音录入 -->
    <div v-else-if="step === 'voice'" class="voice-step">
      <div class="voice-hero">
        <div class="voice-visualizer" :class="{ recording: isRecording }">
          <div class="wave-bar" v-for="i in 18" :key="i" :style="{ animationDelay: i * 0.06 + 's' }"></div>
        </div>
        <div class="voice-status">
          {{ isRecording ? '正在录音...' : (asrResult ? '识别完成' : '点击下方开始录音') }}
        </div>
        <div class="voice-tip" v-if="isRecording">建议 5 秒以上（{{ recordTime }}s / 60s）</div>
        <div class="voice-tip" v-else-if="!asrResult">例如：明天下午 3 点与张总面谈讨论贷款方案</div>
      </div>

      <div v-if="asrResult" class="asr-card">
        <div class="asr-label">
          <span>语音识别结果</span>
          <span class="conf">置信度 {{ asrConfidence }}%</span>
        </div>
        <div class="asr-text">{{ asrResult }}</div>
      </div>

      <div class="bottom-actions">
        <van-button v-if="!isRecording && !asrResult" round block type="primary" @click="startRecording">
          <van-icon name="play" /> 开始录音
        </van-button>
        <van-button v-if="isRecording" round block type="danger" @click="stopRecording">
          <van-icon name="stop" /> 停止录音
        </van-button>
        <van-button v-if="asrResult" round block type="primary" :loading="aiProcessing" loading-text="AI 提取中..." @click="processVoice">
          AI 提取日程
        </van-button>
        <van-button plain round block @click="resetToSelect" style="margin-top: 8px;">重新选择方式</van-button>
      </div>
    </div>

    <!-- 3. 表单确认（文本录入 / AI 提取后共用） -->
    <div v-else-if="step === 'form'" class="form-step">
      <div class="form-header">
        <div class="badge" :class="`badge-${sourceBadgeColor}`">{{ sourceBadgeText }}</div>
        <p class="form-tip">请确认信息，可手动修正</p>
      </div>

      <van-cell-group inset>
        <van-field v-model="form.title" label="标题" placeholder="如：与张总确认额度" :rules="[{ required: true, message: '请输入标题' }]">
          <template #right-icon>
            <VoiceMic label="日程标题" sample="下午3点与张总确认贷款方案" @confirm="form.title = $event" />
          </template>
        </van-field>
        <van-cell title="开始时间" :value="formatDT(form.startTime)">
          <template #value>
            <input
              type="datetime-local"
              :value="toLocal(form.startTime)"
              @input="onStartTimeInput($event.target.value)"
              class="dt-input"
            />
          </template>
        </van-cell>
        <van-cell title="结束时间" :value="formatDT(form.endTime)">
          <template #value>
            <input
              type="datetime-local"
              :value="toLocal(form.endTime)"
              @input="onEndTimeInput($event.target.value)"
              class="dt-input"
            />
          </template>
        </van-cell>
        <van-cell title="优先级" :value="priorityLabel[form.priority]" is-link @click="openPriorityPicker" />
        <van-cell title="类型" :value="typeLabel[form.type]" is-link @click="openTypePicker" />
        <van-field v-model="form.location" label="地点" placeholder="如：客户公司 / 咖啡厅">
          <template #right-icon>
            <VoiceMic label="地点" sample="陆家嘴金融中心咖啡厅" @confirm="form.location = $event" />
          </template>
        </van-field>
        <van-field
          :model-value="form.customerName"
          label="关联客户"
          placeholder="点击选择已有客户"
          readonly
          is-link
          @click="openCustomerPicker"
        />
        <van-cell title="提醒" :value="form.reminderOffset" is-link @click="openReminderPicker" />
      </van-cell-group>

      <!-- 客户选择弹层 -->
      <van-popup v-model:show="showCustomerPicker" position="bottom" round style="height: 60%;">
        <div class="cp-header">选择关联客户</div>
        <div class="cp-search">
          <van-search v-model="customerKeyword" placeholder="搜索姓名或手机号" shape="round">
            <template #right-icon>
              <VoiceMic label="搜索关联客户" sample="13800138000" @confirm="customerKeyword = $event" />
            </template>
          </van-search>
        </div>
        <div class="cp-list">
          <div
            v-for="c in filteredCustomers"
            :key="c.id"
            class="cp-item"
            :class="{ active: c.id === form.customerId }"
            @click="onSelectCustomer(c)"
          >
            <div class="cp-avatar">{{ (c.name || '?').slice(0, 1) }}</div>
            <div class="cp-info">
              <div class="cp-name">{{ c.name }}</div>
              <div class="cp-phone">{{ c.phone }}</div>
            </div>
            <van-icon v-if="c.id === form.customerId" name="success" color="#3B82F6" size="18" />
          </div>
          <div v-if="filteredCustomers.length === 0" class="cp-empty">未找到匹配的客户</div>
        </div>
        <div class="cp-footer">
          <van-button plain round block size="small" @click="clearCustomer">清除关联</van-button>
        </div>
      </van-popup>

      <div style="margin: 16px;">
        <div class="field-label">备注</div>
        <van-field
          v-model="form.remark"
          type="textarea"
          placeholder="可补充议程、需准备的材料等"
          rows="3"
          autosize
        >
          <template #right-icon>
            <VoiceMic label="日程备注" sample="带上身份证和近半年银行流水，确认利率与放款时效" @confirm="form.remark = $event" />
          </template>
        </van-field>
      </div>

      <div style="margin: 24px 16px;">
        <van-button round block type="primary" native-type="submit" :loading="saving" loading-text="保存中..." @click="onSave">
          保存日程
        </van-button>
      </div>

      <!-- 选项弹窗 -->
      <van-action-sheet
        v-model:show="showPriorityPicker"
        :actions="priorityActions"
        cancel-text="取消"
        close-on-click-action
        @select="onPrioritySelect"
      />
      <van-action-sheet
        v-model:show="showTypePicker"
        :actions="typeActions"
        cancel-text="取消"
        close-on-click-action
        @select="onTypeSelect"
      />
      <van-action-sheet
        v-model:show="showReminderPicker"
        :actions="reminderActions"
        cancel-text="不提醒"
        close-on-click-action
        @select="onReminderSelect"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useRoute } from 'vue-router'
import { showToast, showSuccessToast } from 'vant'
import { useScheduleStore } from '../../stores/schedule'
import { useCustomerStore } from '../../stores/customer'
import { asr as asrApi, extractSchedule as extractScheduleApi } from '../../api/ai'
import VoiceMic from '../../components/VoiceMic.vue'

const router = useRouter()
const route = useRoute()
const scheduleStore = useScheduleStore()
const customerStore = useCustomerStore()

const step = ref('select') // select | voice | handwriting | form
const source = ref('text') // text | voice | handwriting

// 语音
const isRecording = ref(false)
const recordTime = ref(0)
const asrResult = ref('')
const asrConfidence = ref(0)
const aiProcessing = ref(false)
let recordTimer = null

// 手写
const canvasRef = ref(null)
const hasInk = ref(false)
const ctx = ref(null)
const isPenDown = ref(false)
const lastPoint = ref(null)
const inkLines = ref([])

// 表单
const form = reactive({
  title: '',
  startTime: '',
  endTime: '',
  priority: 'P1',
  type: 'task',
  location: '',
  customerName: '',
  customerId: null,
  remark: '',
  reminderOffset: '不提醒',
  reminderTime: null,
})
const saving = ref(false)
const showPriorityPicker = ref(false)
const showTypePicker = ref(false)
const showReminderPicker = ref(false)

/* 关联客户选择 */
const showCustomerPicker = ref(false)
const customerKeyword = ref('')
const filteredCustomers = computed(() => {
  const kw = customerKeyword.value.trim().toLowerCase()
  if (!kw) return customerStore.customers
  return customerStore.customers.filter(
    (c) => c.name.toLowerCase().includes(kw) || c.phone.includes(kw)
  )
})
function openCustomerPicker() {
  showCustomerPicker.value = true
}
function onSelectCustomer(c) {
  form.customerId = c.id
  form.customerName = c.name
  showCustomerPicker.value = false
}
function clearCustomer() {
  form.customerId = null
  form.customerName = ''
  showCustomerPicker.value = false
}

const pageTitle = computed(() => {
  if (step.value === 'voice') return '语音录入'
  if (step.value === 'handwriting') return '手写录入'
  if (step.value === 'form') return '确认日程'
  return '新建日程'
})

const sourceBadgeText = computed(() => {
  if (source.value === 'voice') return 'AI 语音提取'
  if (source.value === 'handwriting') return 'AI 手写识别'
  return '手动填写'
})
const sourceBadgeColor = computed(() => source.value)

const priorityLabel = { P0: '紧急 P0', P1: '普通 P1', P2: '低优 P2' }
const typeLabel = { task: '待办', call: '通话', meeting: '面谈' }
const priorityActions = [
  { name: '紧急 P0', value: 'P0' },
  { name: '普通 P1', value: 'P1' },
  { name: '低优 P2', value: 'P2' },
]
const typeActions = [
  { name: '待办', value: 'task' },
  { name: '通话', value: 'call' },
  { name: '面谈', value: 'meeting' },
]
const reminderActions = [
  { name: '提前 5 分钟', value: 5 },
  { name: '提前 15 分钟', value: 15 },
  { name: '提前 30 分钟', value: 30 },
  { name: '提前 1 小时', value: 60 },
  { name: '提前 1 天', value: 1440 },
]

function onBack() {
  if (step.value === 'form' || step.value === 'voice' || step.value === 'handwriting') {
    step.value = 'select'
    resetRecording()
  } else {
    router.back()
  }
}

function resetToSelect() {
  step.value = 'select'
  resetRecording()
  if (ctx.value) {
    ctx.value.clearRect(0, 0, canvasRef.value.width, canvasRef.value.height)
  }
  hasInk.value = false
  inkLines.value = []
}

function selectMode(m) {
  source.value = m
  if (m === 'text') {
    // 默认值
    const now = new Date()
    now.setMinutes(0, 0, 0)
    form.startTime = new Date(now.getTime() + 60 * 60000).toISOString()
    form.endTime = new Date(now.getTime() + 2 * 60 * 60000).toISOString()
    form.reminderOffset = '提前 15 分钟'
    form.reminderTime = new Date(now.getTime() + 45 * 60000).toISOString()
    step.value = 'form'
  } else {
    step.value = m
  }
}

/* ============== 语音 ============== */
function startRecording() {
  isRecording.value = true
  recordTime.value = 0
  recordTimer = setInterval(() => {
    recordTime.value++
    if (recordTime.value >= 60) stopRecording()
  }, 1000)
}

function resetRecording() {
  if (recordTimer) {
    clearInterval(recordTimer)
    recordTimer = null
  }
  isRecording.value = false
  recordTime.value = 0
  asrResult.value = ''
  asrConfidence.value = 0
}

async function stopRecording() {
  if (!isRecording.value) return
  isRecording.value = false
  if (recordTimer) {
    clearInterval(recordTimer)
    recordTimer = null
  }
  if (recordTime.value < 2) {
    showToast('录音时间过短')
    return
  }
  const result = await asrApi()
  asrResult.value = result.text
  asrConfidence.value = Math.round((result.confidence || 0.9) * 100)
}

async function processVoice() {
  if (!asrResult.value) {
    showToast('请先录音')
    return
  }
  aiProcessing.value = true
  const result = await extractScheduleApi(asrResult.value)
  aiProcessing.value = false
  applyAiResult(result.data)
  step.value = 'form'
}

/* ============== 手写 ============== */
function initCanvas() {
  if (!canvasRef.value) return
  const dpr = window.devicePixelRatio || 1
  const rect = canvasRef.value.getBoundingClientRect()
  canvasRef.value.width = rect.width * dpr
  canvasRef.value.height = rect.height * dpr
  ctx.value = canvasRef.value.getContext('2d')
  ctx.value.scale(dpr, dpr)
  ctx.value.lineWidth = 2.5
  ctx.value.lineCap = 'round'
  ctx.value.lineJoin = 'round'
  ctx.value.strokeStyle = '#0F172A'
}

function getCanvasPos(e) {
  const rect = canvasRef.value.getBoundingClientRect()
  return { x: e.clientX - rect.left, y: e.clientY - rect.top }
}

function onPenDown(e) {
  isPenDown.value = true
  lastPoint.value = getCanvasPos(e)
  // 画一个起点小圆点
  ctx.value.beginPath()
  ctx.value.arc(lastPoint.value.x, lastPoint.value.y, 1.2, 0, Math.PI * 2)
  ctx.value.fillStyle = '#0F172A'
  ctx.value.fill()
  hasInk.value = true
}

function onPenMove(e) {
  if (!isPenDown.value) return
  const p = getCanvasPos(e)
  ctx.value.beginPath()
  ctx.value.moveTo(lastPoint.value.x, lastPoint.value.y)
  ctx.value.lineTo(p.x, p.y)
  ctx.value.stroke()
  lastPoint.value = p
}

function onPenUp() {
  isPenDown.value = false
  lastPoint.value = null
}

function clearCanvas() {
  if (!ctx.value) return
  const c = canvasRef.value
  ctx.value.clearRect(0, 0, c.width, c.height)
  hasInk.value = false
}

async function processHandwriting() {
  if (!hasInk.value) {
    showToast('请先书写')
    return
  }
  aiProcessing.value = true
  // 模拟手写识别：根据笔画数量生成不同长度文本
  const samples = [
    '明天下午 3 点与张总面谈',
    '上午 10 点给王先生回电沟通贷款方案',
    '后天下午 2 点提交陈女士的材料补充',
    '明天上午 9 点整理本周客户匹配报告',
  ]
  const recognized = samples[Math.floor(Math.random() * samples.length)]
  aiProcessing.value = false
  asrResult.value = recognized
  asrConfidence.value = 82
  const ai = await extractScheduleApi(recognized)
  applyAiResult(ai.data)
  step.value = 'form'
}

/* ============== 公共 ============== */
function applyAiResult(data) {
  if (!data) return
  form.title = data.title || form.title
  form.startTime = data.startTime || form.startTime
  form.endTime = data.endTime || form.endTime
  form.priority = data.priority || form.priority
  form.type = data.type || form.type
  form.location = data.location || form.location
  // AI 识别的客户名自动关联已有档案
  if (data.customerName) {
    const matched = customerStore.customers.find(
      (c) => c.name === data.customerName || c.name.includes(data.customerName)
    )
    if (matched) {
      form.customerId = matched.id
      form.customerName = matched.name
    } else {
      form.customerName = data.customerName
    }
  }
  if (data.remark) form.remark = data.remark
  // 默认 15 分钟提醒
  if (form.startTime) {
    form.reminderOffset = '提前 15 分钟'
    form.reminderTime = new Date(new Date(form.startTime).getTime() - 15 * 60000).toISOString()
  }
}

/* ============== 表单 ============== */
function openPriorityPicker() { showPriorityPicker.value = true }
function openTypePicker() { showTypePicker.value = true }
function openReminderPicker() { showReminderPicker.value = true }

// HTML5 datetime-local 与 ISO 互转
function toLocal(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}
function onStartTimeInput(v) {
  if (v) form.startTime = new Date(v).toISOString()
  // 自动同步结束时间
  if (form.endTime && new Date(form.endTime) < new Date(v)) {
    form.endTime = new Date(new Date(v).getTime() + 60 * 60000).toISOString()
  }
  // 同步提醒时间
  if (form.reminderTime) {
    form.reminderTime = new Date(new Date(v).getTime() - 15 * 60000).toISOString()
  }
}
function onEndTimeInput(v) {
  if (v) form.endTime = new Date(v).toISOString()
}
function onPrioritySelect(a) {
  form.priority = a.value
  showPriorityPicker.value = false
}
function onTypeSelect(a) {
  form.type = a.value
  showTypePicker.value = false
}
function onReminderSelect(a) {
  const mins = a.value
  form.reminderOffset = a.name
  if (form.startTime) {
    form.reminderTime = new Date(new Date(form.startTime).getTime() - mins * 60000).toISOString()
  }
  showReminderPicker.value = false
}

function formatDT(iso) {
  if (!iso) return '未选择'
  const d = new Date(iso)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getMonth() + 1}/${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

async function onSave() {
  if (!form.title?.trim()) {
    showToast('请输入日程标题')
    return
  }
  if (!form.startTime) {
    showToast('请选择开始时间')
    return
  }
  if (form.endTime && new Date(form.endTime) < new Date(form.startTime)) {
    showToast('结束时间不能早于开始时间')
    return
  }
  saving.value = true
  try {
    await scheduleStore.addSchedule({
      title: form.title.trim(),
      startTime: form.startTime,
      endTime: form.endTime || form.startTime,
      priority: form.priority,
      type: form.type,
      location: form.location,
      remark: form.remark,
      customerName: form.customerName,
      customerId: form.customerId,
      reminderTime: form.reminderTime,
      source: source.value,
    })
    saving.value = false
    showSuccessToast('日程已创建')
    setTimeout(() => router.replace('/schedules'), 500)
  } catch (err) {
    saving.value = false
    showToast(err.message || '保存失败，请重试')
  }
}

onMounted(async () => {
  // 关联客户选择器需要客户数据
  customerStore.loadCustomers().catch(() => {})
  // 支持从客户详情页跳转预填关联客户：/schedules/create?customerId=xxx&customerName=xxx
  const qId = route.query.customerId
  const qName = route.query.customerName
  if (qId) {
    // 客户详情跳转过来：跳过方式选择，直接进表单
    const matched = customerStore.customers.find((c) => c.id === qId)
    if (matched) {
      form.customerId = matched.id
      form.customerName = matched.name
    } else if (qName) {
      form.customerName = decodeURIComponent(qName)
    }
    step.value = 'form'
  }
  if (step.value === 'handwriting') {
    nextTick(() => initCanvas())
  }
})

// 监听 step 变化初始化 canvas
import { watch } from 'vue'
watch(step, (val) => {
  if (val === 'handwriting') {
    nextTick(() => initCanvas())
  }
})

onBeforeUnmount(() => {
  if (recordTimer) clearInterval(recordTimer)
})
</script>

<style scoped>
.create-page {
  background: var(--bg-base);
  min-height: 100vh;
  padding-bottom: 40px;
}

.hero {
  text-align: center;
  padding: 24px 16px 8px;
}
.hero h3 {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 12px 0 6px;
}
.hero p {
  font-size: 14px;
  color: var(--text-tertiary);
}

.methods {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.method {
  display: flex;
  align-items: center;
  gap: 14px;
  background: var(--surface-container);
  border-radius: var(--radius-md);
  padding: 16px;
  box-shadow: var(--shadow-card);
  border: none;
  cursor: pointer;
  transition: all 0.2s;
}
.method:active { transform: scale(0.98); }
.m-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.m-text { flex: 1; }
.m-title { font-size: 16px; font-weight: 600; color: var(--text-primary); }
.m-desc { font-size: 12px; color: var(--text-tertiary); margin-top: 2px; }

/* 语音 */
.voice-step { padding: 24px 16px; }
.voice-hero { text-align: center; margin: 24px 0 32px; }
.voice-visualizer {
  width: 200px;
  height: 80px;
  margin: 0 auto 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}
.wave-bar {
  width: 3px;
  height: 8px;
  background: var(--color-primary);
  border-radius: 2px;
  opacity: 0.4;
  transition: height 0.3s;
}
.voice-visualizer.recording .wave-bar {
  animation: wave 0.7s infinite ease-in-out;
}
@keyframes wave {
  0%, 100% { height: 8px; opacity: 0.5; }
  50% { height: 40px; opacity: 1; }
}
.voice-status { font-size: 16px; font-weight: 600; color: var(--text-primary); }
.voice-tip { font-size: 14px; color: var(--text-tertiary); margin-top: 8px; }

.asr-card {
  background: var(--surface-container);
  border: none;
  border-radius: var(--radius-md);
  padding: 16px;
  margin-bottom: 24px;
  box-shadow: var(--shadow-card);
}
.asr-label {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}
.asr-label .conf {
  font-size: 11px;
  background: rgba(59, 130, 246, 0.12);
  color: var(--color-primary);
  padding: 1px 8px;
  border-radius: 8px;
}
.asr-text { font-size: 14px; color: var(--text-primary); line-height: 1.6; }

.bottom-actions {
  padding: 0 16px;
  margin-top: 16px;
}

/* 手写 */
.handwriting-step { padding: 16px; }
.hw-card {
  background: var(--surface-container);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
  border: none;
  overflow: hidden;
  margin-bottom: 16px;
}
.hw-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: none;
}
.hw-title { font-size: 14px; font-weight: 600; color: var(--text-primary); }
.tool-btn {
  background: var(--surface-container-high);
  border: none;
  border-radius: 8px;
  padding: 4px 12px;
  font-size: 12px;
  color: var(--text-secondary);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.hw-canvas {
  display: block;
  width: 100%;
  height: 280px;
  background: linear-gradient(0deg, rgba(59, 130, 246, 0.02), rgba(6, 182, 212, 0.02));
  background-image:
    linear-gradient(rgba(59, 130, 246, 0.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(59, 130, 246, 0.06) 1px, transparent 1px);
  background-size: 24px 24px;
  touch-action: none;
  cursor: crosshair;
}
.hw-tip {
  text-align: center;
  font-size: 12px;
  color: var(--text-tertiary);
  padding: 10px;
}
.hw-tip.done { color: var(--color-success); }

/* 表单 */
.form-step { padding-top: 12px; }
.form-header { text-align: center; margin-bottom: 12px; }
.badge {
  display: inline-block;
  padding: 4px 12px;
  font-size: 12px;
  border-radius: 12px;
  font-weight: 500;
}
.badge-text { background: rgba(59, 130, 246, 0.12); color: var(--color-primary); }
.badge-voice { background: rgba(6, 182, 212, 0.12); color: #06B6D4; }
.badge-handwriting { background: rgba(139, 92, 246, 0.12); color: #8B5CF6; }
.form-tip { font-size: 12px; color: var(--text-tertiary); margin-top: 6px; }
.field-label {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 6px;
  padding-left: 4px;
}

.dt-input {
  border: 1px solid var(--border-color-soft);
  border-radius: 8px;
  padding: 4px 8px;
  font-size: 14px;
  color: var(--text-primary);
  background: var(--bg-input);
  outline: none;
  font-family: inherit;
  min-width: 160px;
}
.dt-input:focus { border-color: var(--color-primary); }

/* 客户选择弹层 */
.cp-header {
  text-align: center;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  padding: 16px 0 4px;
}
.cp-search { padding: 4px 12px 8px; }
.cp-list {
  height: calc(100% - 160px);
  overflow-y: auto;
  padding: 0 12px;
}
.cp-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 14px;
  margin-bottom: 8px;
  background: var(--surface-container);
  border: none;
  cursor: pointer;
  transition: all 0.15s;
}
.cp-item.active {
  background: var(--primary-container);
}
.cp-avatar {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: linear-gradient(135deg, var(--blue-100, #DBEAFE), var(--cyan-100, #CFFAFE));
  color: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 16px;
  flex-shrink: 0;
}
.cp-info { flex: 1; min-width: 0; }
.cp-name { font-size: 14px; font-weight: 600; color: var(--text-primary); }
.cp-phone { font-size: 12px; color: var(--text-tertiary); margin-top: 1px; }
.cp-empty {
  text-align: center;
  color: var(--text-tertiary);
  font-size: 13px;
  padding: 32px 0;
}
.cp-footer { padding: 8px 16px calc(12px + env(safe-area-inset-bottom)); }
</style>
