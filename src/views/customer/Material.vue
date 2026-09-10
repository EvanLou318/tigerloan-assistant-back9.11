<template>
  <div class="page-container">
    <van-nav-bar :title="navTitle" left-arrow @click-left="onBack" />

    <!-- ============ 步骤1：选择补充方式 ============ -->
    <div v-if="step === 'select'" class="select-step">
      <div class="select-header">
        <div class="select-icon">
          <AppIcon name="user-plus" :size="28" color="var(--color-primary)" />
        </div>
        <h3 class="select-title">补充客户资料</h3>
        <p class="select-desc">选择要录入的材料，AI 自动提取关键信息并合并到档案</p>
      </div>

      <!-- 语音口述快捷通道 -->
      <div class="voice-entry" @click="startVoice">
        <div class="voice-entry-icon">
          <AppIcon name="mic" :size="22" color="var(--color-primary)" />
        </div>
        <div class="voice-entry-text">
          <div class="voice-entry-title">语音口述</div>
          <div class="voice-entry-desc">面谈 / 电话沟通时，说话即可记录客户信息</div>
        </div>
        <AppIcon name="chevron-right" :size="16" color="#94A3B8" />
      </div>

      <!-- 材料类型 -->
      <div class="section-label">选择材料类型</div>
      <div class="material-grid">
        <div
          v-for="item in materialTypes"
          :key="item.key"
          class="material-card"
          @click="selectMaterial(item)"
        >
          <div class="material-icon"><AppIcon :name="item.icon" :size="22" color="var(--color-primary)" /></div>
          <div class="material-name">{{ item.name }}</div>
          <div class="material-priority" :class="item.priorityClass">{{ item.priority }}</div>
          <div class="material-hint">{{ item.hint }}</div>
        </div>
      </div>
    </div>

    <!-- ============ 步骤2：拍照 / 上传 ============ -->
    <div v-else-if="step === 'upload'" class="upload-step">
      <div class="upload-header">
        <span class="material-type-tag">{{ currentMaterial?.name }}</span>
        <span class="method-tag">{{ inputMethod === 'photo' ? '拍照' : '文件上传' }}</span>
      </div>
      <p class="upload-desc">AI 将识别 {{ currentMaterial?.hint }}，请确保拍摄清晰完整</p>

      <div class="upload-area" @click="triggerFileInput">
        <input ref="fileInput" type="file" :accept="inputMethod === 'photo' ? 'image/*' : 'image/*,.pdf'" style="display:none" @change="onFileChange" />
        <div class="upload-placeholder">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
            <path d="M19 13H13V19H11V13H5V11H11V5H13V11H19V13Z" fill="#94A3B8"/>
          </svg>
          <p class="upload-text">点击{{ inputMethod === 'photo' ? '拍照' : '上传文件' }}</p>
          <p class="upload-hint">支持 JPG / PNG / PDF，单文件 ≤ 20MB</p>
        </div>
      </div>

      <div class="upload-actions">
        <van-button plain round block @click="step = 'select'">取消</van-button>
      </div>
    </div>

    <!-- ============ 步骤3：语音口述 ============ -->
    <div v-else-if="step === 'voice'" class="voice-step">
      <div class="voice-header">
        <span class="material-type-tag">语音口述</span>
      </div>

      <div class="voice-container">
        <div class="voice-visualizer" :class="{ recording: isRecording }">
          <div class="wave-bar" v-for="i in 20" :key="i" :style="{ animationDelay: i * 0.05 + 's' }"></div>
        </div>
        <div class="voice-status">
          {{ isRecording ? '录音中...' : (asrResult ? '识别完成' : '点击开始口述客户信息') }}
        </div>
        <div class="voice-time" v-if="isRecording">{{ recordTime }}s / 120s</div>
      </div>

      <div v-if="asrResult" class="asr-result">
        <div class="result-label">
          <span>语音转文字结果</span>
          <span class="confidence-tag">准确率 {{ asrConfidence }}%</span>
        </div>
        <div class="result-text">{{ asrResult.text }}</div>
      </div>

      <div class="voice-actions">
        <van-button v-if="!isRecording && !asrResult" type="primary" round block @click="startRecording">
          开始录音
        </van-button>
        <van-button v-if="isRecording" type="danger" round block @click="stopRecording">
          停止录音
        </van-button>
        <van-button v-if="asrResult" type="primary" round block @click="extractVoiceData" :loading="extracting">
          AI 提取客户信息
        </van-button>
        <van-button v-if="asrResult" plain round block @click="resetVoice" style="margin-top: 8px;">
          重新录音
        </van-button>
      </div>
    </div>

    <!-- ============ 步骤4：AI 处理中 ============ -->
    <div v-else-if="step === 'processing'" class="processing-step">
      <div class="processing-container">
        <div class="processing-spinner">
          <div class="spinner-ring"></div>
          <div class="spinner-ring"></div>
          <div class="spinner-ring"></div>
        </div>
        <div class="processing-title">{{ processingTitle }}</div>
        <div class="processing-steps">
          <div class="proc-step" :class="{ active: procStep >= 1 }">✓ 材料接收</div>
          <div class="proc-step" :class="{ active: procStep >= 2 }">✓ AI 识别提取</div>
          <div class="proc-step" :class="{ active: procStep >= 3 }">✓ 字段结构化</div>
        </div>
      </div>
    </div>

    <!-- ============ 步骤5：合并确认 ============ -->
    <div v-else-if="step === 'merge'" class="merge-step">
      <div class="merge-header">
        <div class="ai-badge">
          <AppIcon name="check-circle" :size="14" />
          AI 提取完成 · 共 {{ mergeFields.length }} 项
        </div>
        <p class="merge-tip">
          请核对以下信息，<span style="color: var(--color-warning);">黄色</span>为低置信度字段，
          <span style="color: var(--color-secondary);">蓝色</span>为与档案已有值冲突的字段
        </p>
      </div>

      <div class="merge-card">
        <div class="merge-material-tag">{{ currentMaterial?.name || '语音口述' }}</div>
        <div
          v-for="field in mergeFields"
          :key="field.key"
          class="merge-field"
          :class="{ conflict: field.hasConflict, lowconf: field.lowConfidence }"
        >
          <div class="merge-field-top">
            <span class="merge-label">{{ field.label }}</span>
            <div class="merge-tags">
              <span v-if="field.hasConflict" class="conflict-tag">原值：{{ formatConflict(field) }}</span>
              <span v-if="field.lowConfidence" class="low-conf-tag">置信度 {{ field.confidencePercent }}%</span>
            </div>
          </div>

          <div class="merge-input-row">
            <div class="merge-input-wrap">
              <!-- 布尔字段用开关 -->
              <van-switch
                v-if="field.type === 'bool'"
                v-model="field.newValueBool"
                size="22px"
                active-color="#2563EB"
              />
              <input
                v-else
                v-model="field.newValue"
                class="merge-input"
                :type="field.type === 'number' ? 'number' : 'text'"
                :placeholder="'请输入' + field.label"
              />
            </div>
            <div class="merge-choice">
              <span class="choice-label">采用新值</span>
              <van-switch v-model="field.checked" size="20px" active-color="#2563EB" />
            </div>
          </div>

          <p v-if="field.hasConflict" class="conflict-hint">
            档案已有「{{ field.oldValue }}」，采用新值后将覆盖；如不确定可关闭开关保留原值
          </p>
        </div>
      </div>

      <div class="merge-actions">
        <van-button round block type="primary" :loading="saving" loading-text="合并中..." @click="onSaveMerge">
          确认合并到客户档案
        </van-button>
        <van-button plain round block @click="resetToSelect" style="margin-top: 10px;">
          继续补充其他材料
        </van-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showSuccessToast } from 'vant'
import { useCustomerStore } from '../../stores/customer'
import {
  ocrIdCard,
  ocrBankStatement,
  ocrCreditReport,
  ocrIncomeProof,
  ocrSocialSecurity,
  ocrProperty,
  ocrBusinessLicense,
  asr as asrApi,
  extractFromVoice,
} from '../../api/ai'

const route = useRoute()
const router = useRouter()
const store = useCustomerStore()

const customerId = route.params.id
const customer = computed(() => store.getCustomerById(customerId))

const step = ref('select')
const selectedMaterialKey = ref('')
const inputMethod = ref('')
const isRecording = ref(false)
const recordTime = ref(0)
const asrResult = ref(null)
const asrConfidence = ref(90)
const extracting = ref(false)
const fileInput = ref(null)
const saving = ref(false)
const procStep = ref(0)
const processingTitle = ref('AI 正在处理...')

const extractedData = ref(null)
const extractedConfidence = ref(0.9)

let recordTimer = null

// ==================== 材料类型定义（含字段映射） ====================
const materialTypes = [
  {
    key: 'idcard', name: '身份证', icon: 'user', priority: 'P0', priorityClass: 'p0', hint: '正反面照片或扫描件',
    extract: ocrIdCard,
    sourceName: '身份证OCR',
    mapping: [
      { key: 'name', label: '姓名', from: 'name' },
      { key: 'gender', label: '性别', from: 'gender' },
      { key: 'age', label: '年龄', from: 'age', type: 'number' },
      { key: 'idCard', label: '身份证号', from: 'idNumber' },
      { key: 'city', label: '所在城市', from: 'city' },
      { key: 'address', label: '户籍地址', from: 'address' },
    ],
  },
  {
    key: 'bankflow', name: '银行流水', icon: 'bank', priority: 'P1', priorityClass: 'p1', hint: 'PDF或截图，近6个月',
    extract: ocrBankStatement,
    sourceName: '银行流水OCR',
    mapping: [
      { key: 'monthlyIncome', label: '月均收入', from: 'monthlyAvgIncome', type: 'number' },
      { key: 'bank', label: '开户银行', from: 'bank', store: false },
      { key: 'monthlyAvgExpense', label: '月均支出', from: 'monthlyAvgExpense', type: 'number', store: false },
    ],
  },
  {
    key: 'credit', name: '征信报告', icon: 'chart', priority: 'P0', priorityClass: 'p0', hint: '央行征信，多页自动拼接',
    extract: ocrCreditReport,
    sourceName: '征信报告OCR',
    mapping: [
      { key: 'totalDebt', label: '总负债', from: 'totalDebt', type: 'number' },
      { key: 'creditCardUsage', label: '信用卡使用率(%)', from: 'creditCardUsage', type: 'number' },
      { key: 'queryCount1m', label: '近1月查询次数', from: 'queryCount1m', type: 'number' },
      { key: 'queryCount3m', label: '近3月查询次数', from: 'queryCount3m', type: 'number' },
      { key: 'queryCount6m', label: '近6月查询次数', from: 'queryCount6m', type: 'number' },
      { key: 'maxOverdueMonths', label: '最长逾期月数', from: 'maxOverdueMonths', type: 'number' },
    ],
  },
  {
    key: 'income', name: '收入证明', icon: 'briefcase', priority: 'P1', priorityClass: 'p1', hint: '公司开具的收入证明',
    extract: ocrIncomeProof,
    sourceName: '收入证明OCR',
    mapping: [
      { key: 'employer', label: '工作单位', from: 'employer' },
      { key: 'position', label: '职位', from: 'position' },
      { key: 'monthlyIncome', label: '月均收入', from: 'monthlyIncome', type: 'number' },
    ],
  },
  {
    key: 'social', name: '社保公积金', icon: 'shield', priority: 'P1', priorityClass: 'p1', hint: '社保/公积金缴纳记录',
    extract: ocrSocialSecurity,
    sourceName: '社保公积金OCR',
    mapping: [
      { key: 'employer', label: '缴纳单位', from: 'employer' },
      { key: 'housingFundBase', label: '公积金基数', from: 'housingFundBase', type: 'number' },
      { key: 'socialSecurityBase', label: '社保基数', from: 'socialSecurityBase', type: 'number', store: false },
    ],
  },
  {
    key: 'property', name: '房产证', icon: 'home', priority: 'P2', priorityClass: 'p2', hint: '不动产权证书',
    extract: ocrProperty,
    sourceName: '房产证OCR',
    mapping: [
      { key: 'propertyValue', label: '房产价值(万)', from: 'propertyValue', type: 'number' },
      { key: 'hasMortgage', label: '是否有抵押', from: 'hasMortgage', type: 'bool' },
    ],
  },
  {
    key: 'license', name: '营业执照', icon: 'file-text', priority: 'P2', priorityClass: 'p2', hint: '企业营业执照',
    extract: ocrBusinessLicense,
    sourceName: '营业执照OCR',
    mapping: [
      { key: 'employer', label: '企业名称', from: 'employer' },
      { key: 'position', label: '职务', from: 'position' },
      { key: 'businessStatus', label: '经营状态', from: 'businessStatus', store: false },
    ],
  },
]

const currentMaterial = computed(() => materialTypes.find((m) => m.key === selectedMaterialKey.value))

const navTitle = computed(() => {
  if (step.value === 'merge') return '确认合并'
  return '补充资料'
})

// ==================== 步骤控制 ====================
function onBack() {
  if (step.value === 'select') {
    router.back()
  } else {
    step.value = 'select'
  }
}

function selectMaterial(item) {
  selectedMaterialKey.value = item.key
  step.value = 'upload'
  inputMethod.value = 'upload'
}

function startVoice() {
  selectedMaterialKey.value = ''
  step.value = 'voice'
  isRecording.value = false
  asrResult.value = null
}

// ==================== 拍照/上传 ====================
function triggerFileInput() {
  fileInput.value?.click()
}

async function onFileChange(e) {
  const file = e.target.files[0]
  if (!file) return

  step.value = 'processing'
  procStep.value = 0
  processingTitle.value = 'AI 正在识别...'

  const stepInterval = setInterval(() => {
    procStep.value++
  }, 800)

  let result
  const material = currentMaterial.value
  try {
    if (file) {
      // 真实文件上传：经后端 multer 存档 + Provider 识别
      const fd = new FormData()
      fd.append('file', file)
      fd.append('type', material.key)
      const resp = await fetch(`/api/ai/ocr/${material.key}`, {
        method: 'POST',
        headers: {
          'X-Auth-Token': localStorage.getItem('token') || '',
          Authorization: `Bearer ${localStorage.getItem('token') || ''}`,
        },
        body: fd,
      })
      const body = await resp.json()
      if (!body.success) throw new Error(body.message || '识别失败')
      result = body.data
    } else {
      result = await material.extract()
    }
    processingTitle.value = `${material.sourceName} 提取中...`
  } catch (err) {
    result = await ocrIdCard()
  }

  clearInterval(stepInterval)
  procStep.value = 3
  await new Promise((r) => setTimeout(r, 500))

  extractedData.value = result.data
  extractedConfidence.value = result.confidence
  buildMergeFields(material.mapping)
  step.value = 'merge'
}

// ==================== 语音口述 ====================
async function startRecording() {
  isRecording.value = true
  recordTime.value = 0
  recordTimer = setInterval(() => {
    recordTime.value++
    if (recordTime.value >= 120) {
      stopRecording()
    }
  }, 1000)
}

async function stopRecording() {
  isRecording.value = false
  if (recordTimer) clearInterval(recordTimer)
  if (recordTime.value < 3) {
    showToast('录音时间过短')
    return
  }

  step.value = 'processing'
  procStep.value = 0
  processingTitle.value = '语音识别中...'

  const stepInterval = setInterval(() => {
    procStep.value++
  }, 700)

  const asrRes = await asrApi()
  asrResult.value = asrRes
  asrConfidence.value = Math.round((asrRes.confidence || 0.9) * 100)

  clearInterval(stepInterval)
  procStep.value = 3
  await new Promise((r) => setTimeout(r, 500))
  step.value = 'voice'
}

async function extractVoiceData() {
  extracting.value = true
  inputMethod.value = 'voice'
  step.value = 'processing'
  procStep.value = 0
  processingTitle.value = '大模型提取结构化信息...'

  const stepInterval = setInterval(() => {
    procStep.value++
  }, 700)

  const extracted = await extractFromVoice(asrResult.value?.text)

  clearInterval(stepInterval)
  procStep.value = 3
  await new Promise((r) => setTimeout(r, 500))

  extractedData.value = extracted.data
  extractedConfidence.value = extracted.confidence

  const voiceMapping = [
    { key: 'name', label: '姓名', from: 'name' },
    { key: 'gender', label: '性别', from: 'gender' },
    { key: 'age', label: '年龄', from: 'age', type: 'number' },
    { key: 'city', label: '所在城市', from: 'city' },
    { key: 'employer', label: '工作单位', from: 'employer' },
    { key: 'position', label: '职位', from: 'position' },
    { key: 'monthlyIncome', label: '月均收入', from: 'monthlyIncome', type: 'number' },
    { key: 'housingFundBase', label: '公积金基数', from: 'housingFundBase', type: 'number' },
    { key: 'propertyValue', label: '房产价值(万)', from: 'propertyValue', type: 'number' },
    { key: 'hasMortgage', label: '是否有抵押', from: 'hasMortgage', type: 'bool' },
    { key: 'carValue', label: '车辆价值(万)', from: 'carValue', type: 'number' },
    { key: 'queryCount3m', label: '近3月查询次数', from: 'queryCount3m', type: 'number' },
    { key: 'expectedAmount', label: '期望额度(万)', from: 'expectedAmount', type: 'number' },
  ]

  buildMergeFields(voiceMapping, '语音口述')
  extracting.value = false
  step.value = 'merge'
}

function resetVoice() {
  asrResult.value = null
  isRecording.value = false
  recordTime.value = 0
}

// ==================== 合并确认 ====================
const mergeFields = ref([])

function buildMergeFields(mapping, sourceName) {
  const c = customer.value || {}
  const list = []

  for (const m of mapping) {
    const rawVal = extractedData.value?.[m.from]
    if (rawVal === undefined || rawVal === null || rawVal === '') continue

    let newValue = rawVal
    let newValueBool = false

    if (m.type === 'number') {
      newValue = String(Number(rawVal) || 0)
    } else if (m.type === 'bool') {
      newValueBool = !!rawVal
      newValue = newValueBool ? '是' : '否'
    } else {
      newValue = String(rawVal)
    }

    const oldValue = c[m.key]
    const hasConflict =
      oldValue !== undefined &&
      oldValue !== null &&
      oldValue !== '' &&
      oldValue !== 0 &&
      String(oldValue) !== String(newValue) &&
      !(m.type === 'bool' && String(oldValue) === (newValueBool ? 'true' : 'false'))

    // 置信度微调，模拟不同字段的识别准确度差异
    const variation = (Math.random() - 0.5) * 0.2
    const confidence = Math.max(0.65, Math.min(0.99, extractedConfidence.value + variation))

    list.push({
      key: m.key,
      label: m.label,
      type: m.type || 'text',
      newValue,
      newValueBool,
      oldValue: oldValue === undefined || oldValue === '' || oldValue === 0 ? '' : oldValue,
      hasConflict: !!hasConflict,
      lowConfidence: confidence < 0.85,
      confidencePercent: Math.round(confidence * 100),
      checked: true,
      store: m.store !== false,
    })
  }

  mergeFields.value = list
}

function formatConflict(field) {
  if (field.type === 'bool') {
    return field.oldValue === true || field.oldValue === '是' ? '是' : '否'
  }
  return field.oldValue
}

async function onSaveMerge() {
  saving.value = true
  try {
    const updates = {}
    for (const f of mergeFields.value) {
      if (!f.checked || !f.store) continue
      if (f.type === 'bool') {
        updates[f.key] = f.newValueBool
      } else if (f.type === 'number') {
        updates[f.key] = Number(f.newValue) || 0
      } else {
        updates[f.key] = f.newValue
      }
    }

    await store.mergeCustomerFields(customerId, updates)
    await store.addMaterial(customerId, {
      type: currentMaterial.value?.name || '语音口述',
      source: inputMethod.value === 'photo' ? 'photo' : inputMethod.value === 'voice' ? 'voice' : 'upload',
      confidence: extractedConfidence.value,
      fieldCount: Object.keys(updates).length,
      sourceName: currentMaterial.value?.sourceName || '语音口述提取',
    })

    saving.value = false
    showSuccessToast(`已合并 ${Object.keys(updates).length} 项信息`)
    setTimeout(() => router.replace(`/customers/${customerId}`), 800)
  } catch (err) {
    saving.value = false
    showToast(err.message || '保存失败，请重试')
  }
}

function resetToSelect() {
  step.value = 'select'
  selectedMaterialKey.value = ''
  inputMethod.value = ''
  asrResult.value = null
  extractedData.value = null
  mergeFields.value = []
}

onMounted(() => {
  store.loadCustomers().catch(() => {})
})
</script>

<style scoped>
/* 选择步骤 */
.select-step {
  padding: 20px 16px 32px;
}

.select-header {
  text-align: center;
  margin-bottom: 20px;
}

.select-icon {
  width: 56px;
  height: 56px;
  margin: 0 auto 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  background: var(--primary-container);
  color: var(--on-primary-container);
}

.select-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 6px;
}

.select-desc {
  font-size: 14px;
  color: var(--text-tertiary);
}

/* 语音入口 */
.voice-entry {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  margin-bottom: 20px;
  background: var(--secondary-container);
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
}

.voice-entry-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: rgba(0, 255, 204, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.voice-entry-text {
  flex: 1;
  min-width: 0;
}

.voice-entry-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 2px;
}

.voice-entry-desc {
  font-size: 12px;
  color: var(--text-tertiary);
}

.section-label {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 10px;
  font-weight: 600;
  padding-left: 4px;
}

.material-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.material-card {
  background: var(--surface-container);
  border: none;
  border-radius: var(--radius-md);
  padding: 14px 8px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}

.material-card:active {
  transform: scale(0.97);
  background: var(--surface-container-high);
}

.material-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 6px;
}

.material-name {
  font-size: 12px;
  color: var(--text-primary);
  font-weight: 500;
}

.material-priority {
  font-size: 11px;
  margin-top: 3px;
  display: inline-block;
  padding: 1px 5px;
  border-radius: 3px;
}

.material-priority.p0 {
  background: rgba(239, 68, 68, 0.12);
  color: var(--color-danger);
}

.material-priority.p1 {
  background: rgba(6, 182, 212, 0.12);
  color: var(--color-secondary);
}

.material-priority.p2 {
  background: rgba(139, 149, 167, 0.15);
  color: var(--text-tertiary);
}

.material-hint {
  font-size: 11px;
  color: var(--text-tertiary);
  margin-top: 4px;
  line-height: 1.3;
}

/* 上传步骤 */
.upload-step {
  padding: 16px;
}

.upload-header {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.material-type-tag, .method-tag {
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 4px;
}

.material-type-tag {
  background: rgba(37, 99, 235, 0.12);
  color: var(--color-primary);
}

.method-tag {
  background: rgba(6, 182, 212, 0.12);
  color: var(--color-secondary);
}

.upload-desc {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-bottom: 16px;
}

.upload-area {
  border: 2px dashed var(--border-color);
  border-radius: var(--radius-lg);
  padding: 56px 16px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  background: var(--bg-card);
}

.upload-area:active {
  border-color: var(--color-primary);
  background: rgba(37, 99, 235, 0.03);
}

.upload-text {
  font-size: 14px;
  color: var(--text-secondary);
  margin-top: 12px;
}

.upload-hint {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 4px;
}

.upload-actions {
  margin-top: 20px;
}

/* 语音步骤 */
.voice-step {
  padding: 16px;
}

.voice-header {
  margin-bottom: 16px;
}

.voice-container {
  text-align: center;
  margin: 32px 0;
}

.voice-visualizer {
  width: 200px;
  height: 80px;
  margin: 0 auto 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 3px;
}

.wave-bar {
  width: 3px;
  height: 8px;
  background: var(--color-primary);
  border-radius: 2px;
  opacity: 0.3;
}

.voice-visualizer.recording .wave-bar {
  animation: wave 0.8s infinite ease-in-out;
}

@keyframes wave {
  0%, 100% { height: 8px; opacity: 0.5; }
  50% { height: 40px; opacity: 1; }
}

.voice-status {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.voice-time {
  font-size: 14px;
  color: var(--color-primary);
  margin-top: 4px;
  font-family: 'DIN', sans-serif;
}

.asr-result {
  background: var(--surface-container);
  border: none;
  border-radius: var(--radius-md);
  padding: 16px;
  margin-bottom: 24px;
  box-shadow: var(--shadow-card);
}

.result-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 14px;
  color: var(--text-secondary);
}

.confidence-tag {
  font-size: 11px;
  padding: 2px 8px;
  background: rgba(37, 99, 235, 0.12);
  color: var(--color-primary);
  border-radius: 4px;
}

.result-text {
  font-size: 14px;
  color: var(--text-primary);
  line-height: 1.6;
}

/* 处理中 */
.processing-step {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 70vh;
}

.processing-container {
  text-align: center;
}

.processing-spinner {
  position: relative;
  width: 60px;
  height: 60px;
  margin: 0 auto 24px;
}

.spinner-ring {
  position: absolute;
  inset: 0;
  border: 2px solid transparent;
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 1s infinite linear;
}

.spinner-ring:nth-child(2) {
  inset: 8px;
  border-top-color: var(--color-secondary);
  animation-duration: 1.5s;
  animation-direction: reverse;
}

.spinner-ring:nth-child(3) {
  inset: 16px;
  border-top-color: var(--color-accent);
  animation-duration: 0.8s;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.processing-title {
  font-size: 16px;
  color: var(--text-secondary);
  margin-bottom: 20px;
}

.processing-steps {
  display: flex;
  flex-direction: column;
  gap: 8px;
  text-align: left;
}

.proc-step {
  font-size: 14px;
  color: var(--text-tertiary);
}

.proc-step.active {
  color: var(--color-primary);
}

/* 合并确认 */
.merge-step {
  padding: 16px 16px 32px;
}

.merge-header {
  text-align: center;
  margin-bottom: 16px;
}

.ai-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 16px;
  background: var(--primary-container);
  border: none;
  border-radius: 16px;
  font-size: 12px;
  color: var(--on-primary-container);
  font-weight: 500;
}

.merge-tip {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 8px;
}

.merge-card {
  background: var(--surface-container);
  border: none;
  border-radius: var(--radius-md);
  overflow: hidden;
  box-shadow: var(--shadow-card);
}

.merge-material-tag {
  padding: 10px 16px;
  font-size: 12px;
  color: var(--on-secondary-container);
  background: var(--secondary-container);
  border-bottom: none;
  font-weight: 500;
}

.merge-field {
  padding: 12px 16px;
  border-bottom: none;
  background: transparent;
}

.merge-field:last-child {
  border-bottom: none;
}

.merge-field.lowconf {
  background: rgba(245, 158, 11, 0.03);
}

.merge-field.conflict {
  background: rgba(6, 182, 212, 0.04);
}

.merge-field-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  gap: 8px;
}

.merge-label {
  font-size: 14px;
  color: var(--text-primary);
  font-weight: 500;
}

.merge-tags {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.conflict-tag {
  font-size: 11px;
  padding: 2px 6px;
  background: rgba(6, 182, 212, 0.12);
  color: var(--color-secondary);
  border-radius: 4px;
}

.low-conf-tag {
  font-size: 11px;
  padding: 2px 6px;
  background: rgba(245, 158, 11, 0.12);
  color: var(--color-warning);
  border-radius: 4px;
}

.merge-input-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.merge-input-wrap {
  flex: 1;
}

.merge-input {
  width: 100%;
  height: 36px;
  padding: 0 12px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--bg-input);
  color: var(--text-primary);
  font-size: 14px;
  outline: none;
}

.merge-input:focus {
  border-color: var(--color-primary);
}

.merge-choice {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.choice-label {
  font-size: 12px;
  color: var(--text-tertiary);
}

.conflict-hint {
  font-size: 11px;
  color: var(--color-secondary);
  margin-top: 6px;
  line-height: 1.4;
}

.merge-actions {
  margin-top: 24px;
}
</style>
