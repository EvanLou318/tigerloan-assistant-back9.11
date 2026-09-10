<template>
  <div class="page-container create-page">
    <van-nav-bar :title="pageTitle" left-arrow @click-left="onBack" />

    <!-- 语音录入（方式在入口弹层中选择，?mode=voice 直达） -->
    <div v-if="step === 'voice'" class="voice-step">
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
          <AppIcon name="play" /> 开始录音
        </van-button>
        <van-button v-if="isRecording" round block type="danger" @click="stopRecording">
          <AppIcon name="stop" /> 停止录音
        </van-button>
        <van-button v-if="asrResult" round block type="primary" :loading="aiProcessing" loading-text="AI 提取中..." @click="processVoice">
          AI 提取日程
        </van-button>
        <div class="voice-extra" v-if="asrResult">
          <span @click="resetRecording">觉得不对？重新录音</span>
        </div>
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
            <AppIcon name="check-circle" :size="18" color="#2563EB" v-if="c.id === form.customerId" />
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
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
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

// 录入方式已在入口弹层选择：?mode=text|voice，缺省（如客户详情跳转）直达文本表单
const enteredMode = route.query.mode === 'voice' ? 'voice' : 'text'
const step = ref(enteredMode === 'text' ? 'form' : enteredMode) // form | voice
const source = ref(enteredMode) // text | voice

// 语音
const isRecording = ref(false)
const recordTime = ref(0)
const asrResult = ref('')
const asrConfidence = ref(0)
const aiProcessing = ref(false)
let recordTimer = null


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

// 文本表单默认时间（setup 即预填，避免表单短暂空值）
ensureDefaults()

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
  if (step.value === 'voice') return '语音录入日程'
  return '新建日程'
})

const sourceBadgeText = computed(() => {
  if (source.value === 'voice') return 'AI 语音提取'
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
  router.back()
}

// 录入方式已在入口弹层选好；文本录入（或直达）需预填默认时间
function ensureDefaults() {
  if (form.startTime) return
  const now = new Date()
  now.setMinutes(0, 0, 0)
  form.startTime = new Date(now.getTime() + 60 * 60000).toISOString()
  form.endTime = new Date(now.getTime() + 2 * 60 * 60000).toISOString()
  form.reminderOffset = '提前 15 分钟'
  form.reminderTime = new Date(now.getTime() + 45 * 60000).toISOString()
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
  ensureDefaults()
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
  // 关联客户选择器需要客户数据（等待加载完成再匹配预填）
  try {
    await customerStore.loadCustomers()
  } catch (e) { /* 加载失败不阻塞录入 */ }

  // 支持从客户详情页跳转预填关联客户：/schedules/create?customerId=xxx&customerName=xxx
  const qId = route.query.customerId
  const qName = route.query.customerName
  if (qId) {
    const matched = customerStore.customers.find((c) => String(c.id) === String(qId))
    if (matched) {
      form.customerId = matched.id
      form.customerName = matched.name
    } else if (qName) {
      form.customerName = decodeURIComponent(qName)
    }
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
.voice-extra {
  text-align: center;
  margin-top: 12px;
}
.voice-extra span {
  font-size: 13px;
  color: var(--color-primary);
  cursor: pointer;
  padding: 6px 10px;
}

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
  background: rgba(37, 99, 235, 0.12);
  color: var(--color-primary);
  padding: 1px 8px;
  border-radius: 8px;
}
.asr-text { font-size: 14px; color: var(--text-primary); line-height: 1.6; }

.bottom-actions {
  padding: 0 16px;
  margin-top: 16px;
}

/* 表单 */
.form-step { padding-top: 12px; }
/* 全局样式把 inset 卡片 margin 归零，这里恢复统一的 16px 左右边距 */
.form-step :deep(.van-cell-group--inset) {
  margin: 0 16px !important;
}
.form-header { text-align: center; margin-bottom: 12px; }
.badge {
  display: inline-block;
  padding: 4px 12px;
  font-size: 12px;
  border-radius: 12px;
  font-weight: 500;
}
.badge-text { background: rgba(37, 99, 235, 0.12); color: var(--color-primary); }
.badge-voice { background: rgba(6, 182, 212, 0.12); color: #0EA5A5; }
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
  background: var(--primary-container);
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
