<template>
  <div class="page-container">
    <van-nav-bar :title="isEditMode ? '编辑产品' : '录入产品'" left-arrow @click-left="$router.back()" />

    <!-- 录入方式选择 -->
    <div v-if="step === 'select'" class="select-step">
      <div class="select-header">
        <div class="select-icon">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
            <path d="M19 13H13V19H11V13H5V11H11V5H13V11H19V13Z" fill="#2563EB"/>
          </svg>
        </div>
        <h3 class="select-title">选择录入方式</h3>
        <p class="select-desc">AI 将自动提取产品信息，减少手动录入</p>
      </div>

      <div class="method-grid">
        <div class="method-card" @click="selectMethod('text')">
          <div class="method-icon">
            <AppIcon name="edit" :size="24" color="var(--color-primary)" />
          </div>
          <div class="method-info">
            <div class="method-name">文本录入</div>
            <div class="method-desc">手动填写表单</div>
          </div>
          <AppIcon name="chevron-right" color="#94A3B8" />
        </div>

        <div class="method-card" @click="selectMethod('voice')">
          <div class="method-icon">
            <AppIcon name="mic" :size="24" color="var(--color-primary)" />
          </div>
          <div class="method-info">
            <div class="method-name">语音录入</div>
            <div class="method-desc">口述产品信息，AI 自动识别</div>
          </div>
          <AppIcon name="chevron-right" color="#94A3B8" />
        </div>

        <div class="method-card" @click="selectMethod('image')">
          <div class="method-icon">
            <AppIcon name="image" :size="24" color="var(--color-primary)" />
          </div>
          <div class="method-info">
            <div class="method-name">图片录入</div>
            <div class="method-desc">上传产品海报/宣传单照片</div>
          </div>
          <AppIcon name="chevron-right" color="#94A3B8" />
        </div>

        <div class="method-card" @click="selectMethod('pdf')">
          <div class="method-icon">
            <AppIcon name="file-text" :size="24" color="var(--color-primary)" />
          </div>
          <div class="method-info">
            <div class="method-name">PDF录入</div>
            <div class="method-desc">上传产品说明文档</div>
          </div>
          <AppIcon name="chevron-right" color="#94A3B8" />
        </div>
      </div>
    </div>

    <!-- 编辑模式加载中：不展示录入方式选择 -->
    <div v-else-if="step === 'loading'" class="loading-step">
      <van-loading size="22" vertical>加载产品信息…</van-loading>
    </div>

    <!-- 语音录入 -->
    <div v-else-if="step === 'voice'" class="voice-step">
      <div class="voice-container">
        <div class="voice-visualizer" :class="{ recording: isRecording }">
          <div class="wave-bar" v-for="i in 20" :key="i" :style="{ animationDelay: i * 0.05 + 's' }"></div>
        </div>
        <div class="voice-status">
          {{ isRecording ? '录音中...' : (asrResult ? '识别完成' : '点击开始录音') }}
        </div>
        <div class="voice-time" v-if="isRecording">{{ recordTime }}s / 60s</div>
      </div>

      <div v-if="asrResult" class="asr-result">
        <div class="result-label">
          <span>识别结果</span>
          <span class="confidence-tag">置信度 90%</span>
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
        <van-button v-if="asrResult" type="primary" round block :loading="aiProcessing" loading-text="AI提取中..." @click="processWithAI">
          AI提取产品信息
        </van-button>
        <van-button plain round block @click="resetMethod" style="margin-top: 8px;">
          重新选择方式
        </van-button>
      </div>
    </div>

    <!-- 图片/PDF上传 -->
    <div v-else-if="step === 'image' || step === 'pdf'" class="upload-step">
      <div class="upload-area" @click="triggerUpload">
        <input ref="fileInput" type="file" :accept="step === 'image' ? 'image/*' : '.pdf'" style="display: none;" @change="onFileChange" />
        <div class="upload-placeholder">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
            <path d="M19 13H13V19H11V13H5V11H11V5H13V11H19V13Z" fill="#94A3B8"/>
          </svg>
          <p class="upload-text">点击上传{{ step === 'image' ? '图片' : 'PDF文档' }}</p>
          <p class="upload-hint">{{ step === 'image' ? '支持 JPG、PNG，不超过10MB' : '不超过20MB，最多5页' }}</p>
        </div>
      </div>

      <div v-if="uploadedFile" class="upload-preview">
        <div class="preview-info">
          <span class="preview-icon"><AppIcon name="file-text" :size="22" color="var(--color-primary)" /></span>
          <span class="preview-name">{{ uploadedFile }}</span>
        </div>
        <div v-if="ocrProcessing" class="ocr-processing">
          <van-loading size="20" type="spinner" color="#2563EB" />
          <span class="processing-text">OCR 识别中...</span>
        </div>
      </div>

      <div class="upload-actions">
        <van-button v-if="ocrResult" type="primary" round block @click="showPreview">
          查看 AI 提取结果
        </van-button>
        <van-button plain round block @click="resetMethod" style="margin-top: 8px;">
          重新选择方式
        </van-button>
      </div>
    </div>

    <!-- AI 处理中 -->
    <div v-else-if="step === 'processing'" class="processing-step">
      <div class="processing-container">
        <div class="processing-spinner">
          <div class="spinner-ring"></div>
          <div class="spinner-ring"></div>
          <div class="spinner-ring"></div>
        </div>
        <div class="processing-text">AI 正在提取产品信息...</div>
        <div class="processing-steps">
          <div class="proc-step active">✓ 识别输入内容</div>
          <div class="proc-step active">✓ 提取关键字段</div>
          <div class="proc-step">○ 结构化整理中</div>
        </div>
      </div>
    </div>

    <!-- 预览确认 -->
    <div v-else-if="step === 'preview'" class="preview-step">
      <div class="preview-header">
        <div class="ai-badge">{{ badgeText }}</div>
        <p class="preview-tip">{{ badgeTip }}</p>
      </div>

      <van-form @submit="onSave">
        <van-cell-group inset>
          <van-field v-model="formData.productName" label="产品名称" placeholder="请输入产品名称" :rules="[{ required: true, message: '请输入产品名称' }]" />

          <!-- 所属机构：手动输入 + 历史机构联想 -->
          <van-field
            v-model="formData.institution"
            label="所属机构"
            placeholder="请输入所属机构"
            :rules="[{ required: true, message: '请输入所属机构' }]"
            @focus="institutionFocused = true"
            @blur="onInstitutionBlur"
          />
          <div v-if="institutionFocused && institutionSuggestions.length" class="suggest-bar">
            <span class="suggest-label">历史机构</span>
            <span
              v-for="ins in institutionSuggestions"
              :key="ins"
              class="suggest-chip"
              @mousedown.prevent="pickInstitution(ins)"
            >{{ ins }}</span>
          </div>
          <van-field v-model="formData.minRate" label="最低年利率" type="number" placeholder="如 3.45" :rules="[{ required: true, message: '请输入最低年利率' }]">
            <template #button><span style="color: var(--text-tertiary);">%</span></template>
          </van-field>
          <van-field v-model="formData.maxRate" label="最高年利率" type="number" placeholder="如 5.6">
            <template #button><span style="color: var(--text-tertiary);">%</span></template>
          </van-field>
          <van-field v-model="formData.minAmount" label="最低额度" type="digit" placeholder="如 1" :rules="[{ required: true, message: '请输入最低额度' }]">
            <template #button><span style="color: var(--text-tertiary);">万</span></template>
          </van-field>
          <van-field v-model="formData.maxAmount" label="最高额度" type="digit" placeholder="如 30" :rules="[{ required: true, message: '请输入最高额度' }]">
            <template #button><span style="color: var(--text-tertiary);">万</span></template>
          </van-field>
          <!-- 贷款期限：最短 / 最长 月份分别填写 -->
          <div class="range-row">
            <van-field
              v-model="formData.minTerm"
              class="range-field"
              label-width="60"
              label="最短"
              type="digit"
              placeholder="如 12"
              :rules="[{ required: true, message: '请输入最短期限' }]"
            >
              <template #button><span class="unit">个月</span></template>
            </van-field>
            <span class="range-sep">-</span>
            <van-field
              v-model="formData.maxTerm"
              class="range-field"
              label-width="60"
              label="最长"
              type="digit"
              placeholder="如 36"
              :rules="[{ required: true, message: '请输入最长期限' }]"
            >
              <template #button><span class="unit">个月</span></template>
            </van-field>
          </div>

          <!-- 还款方式：常用方式枚举选择 -->
          <van-field
            v-model="formData.repaymentMethod"
            label="还款方式"
            placeholder="请选择还款方式"
            readonly
            is-link
            :rules="[{ required: true, message: '请选择还款方式' }]"
            @click="showRepaymentSheet = true"
          />
          <van-action-sheet
            v-model:show="showRepaymentSheet"
            title="选择还款方式"
            :actions="repaymentActions"
            cancel-text="取消"
            close-on-click-action
            @select="onPickRepayment"
          />
        </van-cell-group>

        <div style="margin: 16px;">
          <div class="conditions-label">准入条件</div>
          <van-field
            v-model="formData.conditions"
            type="textarea"
            placeholder="请输入准入条件"
            rows="3"
            autosize
            :rules="[{ required: true, message: '请输入准入条件' }]"
          >
            <template #right-icon>
              <VoiceMic label="准入条件" sample="年龄22到55周岁，本单位连续工作满6个月，月收入不低于5000元，征信无当前逾期" @confirm="formData.conditions = $event" />
            </template>
          </van-field>
        </div>

        <div style="margin: 24px 16px;">
          <van-button round block type="primary" native-type="submit" :loading="saving" loading-text="保存中...">
            确认保存
          </van-button>
        </div>
      </van-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showSuccessToast } from 'vant'
import { useProductStore } from '../../stores/product'
import VoiceMic from '../../components/VoiceMic.vue'
import { asr, extractProduct } from '../../api/ai'

const route = useRoute()
const router = useRouter()
const store = useProductStore()

const editId = route.query.edit || ''
const isEditMode = !!editId

// select, voice, image, pdf, processing, preview, loading（编辑模式加载中）
// 编辑模式直接进 loading，避免闪现「选择录入方式」
const step = ref(isEditMode ? 'loading' : 'select')

// 常用还款方式枚举（保存为文本，兼容历史数据）
const REPAYMENT_OPTIONS = [
  '等额本息',
  '等额本金',
  '先息后本',
  '到期一次性还本付息',
  '按期付息、到期还本',
  '随借随还',
]
const repaymentActions = REPAYMENT_OPTIONS.map((name) => ({ name }))
const showRepaymentSheet = ref(false)
function onPickRepayment(action) {
  formData.repaymentMethod = action.name
}

// 所属机构历史联想
const institutionFocused = ref(false)
const institutionSuggestions = computed(() => {
  const kw = formData.institution.trim()
  const all = [...new Set(store.products.map((p) => p.institution).filter(Boolean))]
  const matched = kw ? all.filter((i) => i.includes(kw) && i !== kw) : all
  return matched.slice(0, 6)
})
function pickInstitution(ins) {
  formData.institution = ins
  institutionFocused.value = false
}
function onInstitutionBlur() {
  // 延迟关闭，保证 chip 的 mousedown 先触发
  setTimeout(() => { institutionFocused.value = false }, 200)
}

const method = ref('')
const isRecording = ref(false)

// 顶部徽标：手动填写 / AI 提取 / 编辑产品
const badgeText = computed(() => {
  if (isEditMode) return '编辑产品信息'
  return formData.source === 'text' ? '手动填写' : 'AI 提取完成'
})
const badgeTip = computed(() => {
  if (isEditMode) return '修改后确认保存，将更新原产品'
  return formData.source === 'text' ? '请填写产品信息，保存后进入产品库' : '请确认以下信息，可手动修正'
})
const recordTime = ref(0)
const asrResult = ref(null)
const aiProcessing = ref(false)
const ocrProcessing = ref(false)
const ocrResult = ref(null)
const uploadedFile = ref('')
const fileInput = ref(null)
const saving = ref(false)

let recordTimer = null

const formData = reactive({
  productName: '',
  institution: '',
  minRate: '',
  maxRate: '',
  minAmount: '',
  maxAmount: '',
  loanTerm: '',
  minTerm: '',
  maxTerm: '',
  repaymentMethod: '',
  conditions: '',
  source: 'text',
})

// 贷款期限输入（min/max 月份）与存储字符串互转
function parseLoanTerm(text) {
  const s = String(text || '')
  const range = s.match(/(\d+)\s*(?:[-~—]|到|至)\s*(\d+)/)
  if (range) return { min: range[1], max: range[2] }
  const single = s.match(/(\d+)/)
  return { min: single ? single[1] : '', max: '' }
}
function buildLoanTerm() {
  const min = String(formData.minTerm || '').trim()
  const max = String(formData.maxTerm || '').trim()
  if (min && max) return `${min}-${max}个月`
  if (min) return `${min}个月`
  return ''
}

// 录入/编辑页都需要产品列表：编辑用于回填，录入用于机构联想
onMounted(async () => {
  await store.loadProducts(true)
  if (isEditMode) {
    const product = store.getProductById(editId)
    if (product) {
      fillFormData(product)
      formData.source = product.source || 'text'
      step.value = 'preview'
    } else {
      showToast('产品不存在或已被删除')
      router.back()
    }
  }
})

// 列表页底部弹框直达：携带 method 参数跳过方式选择步骤
const presetMethod = route.query.method
if (!isEditMode && presetMethod && ['text', 'voice', 'image', 'pdf'].includes(presetMethod)) {
  selectMethod(presetMethod)
}

function selectMethod(m) {
  method.value = m
  formData.source = m
  // 文本录入没有 AI 提取环节，直接进入表单填写
  if (m === 'text') {
    step.value = 'preview'
  } else {
    step.value = m
  }
}

function resetMethod() {
  step.value = 'select'
  method.value = ''
  formData.minTerm = ''
  formData.maxTerm = ''
  isRecording.value = false
  asrResult.value = null
  ocrResult.value = null
  uploadedFile.value = ''
  recordTime.value = 0
  if (recordTimer) clearInterval(recordTimer)
}

function startRecording() {
  isRecording.value = true
  recordTime.value = 0
  recordTimer = setInterval(() => {
    recordTime.value++
    if (recordTime.value >= 60) {
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
  try {
    // ASR 识别（后端 AI Provider）
    const result = await asr()
    asrResult.value = result
  } catch (e) {
    showToast(e.message || '语音识别失败')
  }
}

async function processWithAI() {
  aiProcessing.value = true
  step.value = 'processing'
  try {
    // AI 提取（后端 AI Provider）
    const result = await extractProduct(asrResult.value?.text)
    fillFormData(result.data)
  } catch (e) {
    showToast(e.message || 'AI 提取失败')
  } finally {
    aiProcessing.value = false
    step.value = 'preview'
  }
}

function triggerUpload() {
  fileInput.value?.click()
}

async function onFileChange(e) {
  const file = e.target.files[0]
  if (!file) return
  uploadedFile.value = file.name
  ocrProcessing.value = true

  try {
    // AI 提取（后端 AI Provider，含文件解析延迟）
    const result = await extractProduct()
    ocrResult.value = result
    fillFormData(result.data)
  } catch (e) {
    showToast(e.message || 'AI 提取失败')
  } finally {
    ocrProcessing.value = false
    step.value = 'preview'
  }
}

function showPreview() {
  step.value = 'processing'
  setTimeout(() => {
    fillFormData(ocrResult.value.data)
    step.value = 'preview'
  }, 1500)
}

function fillFormData(data) {
  Object.assign(formData, {
    productName: data.productName || '',
    institution: data.institution || '',
    minRate: String(data.minRate || ''),
    maxRate: String(data.maxRate || ''),
    minAmount: String(data.minAmount || ''),
    maxAmount: String(data.maxAmount || ''),
    loanTerm: data.loanTerm || '',
    repaymentMethod: data.repaymentMethod || '',
    conditions: data.conditions || '',
  })
  // 期限回填到「最短/最长」两个输入框
  const { min, max } = parseLoanTerm(data.loanTerm)
  formData.minTerm = min
  formData.maxTerm = max
}

async function onSave() {
  // 校验利率区间
  if (formData.maxRate && Number(formData.minRate) > Number(formData.maxRate)) {
    showToast('最低年利率不能大于最高年利率')
    return
  }
  // 校验额度区间
  if (Number(formData.minAmount) > Number(formData.maxAmount)) {
    showToast('最低额度不能大于最高额度')
    return
  }
  // 校验期限区间（最短/最长月数）
  if (formData.minTerm && formData.maxTerm && Number(formData.minTerm) > Number(formData.maxTerm)) {
    showToast('最短期限不能大于最长期限')
    return
  }

  saving.value = true
  try {
    const payload = {
      ...formData,
      loanTerm: buildLoanTerm(),
      minRate: Number(formData.minRate),
      maxRate: Number(formData.maxRate),
      minAmount: Number(formData.minAmount),
      maxAmount: Number(formData.maxAmount),
    }
    if (isEditMode) {
      await store.updateProduct(editId, payload)
      showSuccessToast('产品更新成功')
      setTimeout(() => router.replace(`/products/${editId}`), 800)
    } else {
      await store.addProduct(payload)
      showSuccessToast('产品录入成功')
      setTimeout(() => router.replace('/products'), 800)
    }
  } catch (e) {
    showToast(e.message || '保存失败')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.select-step {
  padding: 24px 16px;
}

.loading-step {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 240px;
}

/* 所属机构历史联想 */
.suggest-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  padding: 6px 16px 12px;
  background: var(--surface-container);
}

.suggest-label {
  font-size: 11px;
  color: var(--text-tertiary);
  margin-right: 2px;
}

.suggest-chip {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 999px;
  background: var(--surface-container-high);
  color: var(--text-secondary);
  cursor: pointer;
}

.suggest-chip:active {
  background: var(--primary-container);
  color: var(--color-primary);
}

/* 贷款期限区间输入 */
.range-row {
  display: flex;
  align-items: center;
  background: var(--surface-container);
}

.range-field {
  flex: 1;
  min-width: 0;
}

.range-sep {
  color: var(--text-tertiary);
  padding: 0 2px;
  flex-shrink: 0;
}

.unit {
  color: var(--text-tertiary);
  font-size: 13px;
}

.select-header {
  text-align: center;
  margin-bottom: 32px;
}

.select-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  background: var(--primary-container);
  border: none;
}

.select-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.select-desc {
  font-size: 14px;
  color: var(--text-tertiary);
}

.method-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.method-card {
  display: flex;
  align-items: center;
  gap: 14px;
  background: var(--bg-card);
  border: none;
  border-radius: var(--radius-md);
  padding: 16px;
  cursor: pointer;
  box-shadow: var(--shadow-card);
  transition: all 0.2s;
}

.method-card:active {
  transform: scale(0.98);
  background: var(--bg-card-hover);
}

.method-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: var(--primary-container);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border: none;
  background: var(--surface-container-low);
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

/* 语音录入 */
.voice-step {
  padding: 40px 24px;
}

.voice-container {
  text-align: center;
  margin-bottom: 32px;
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
  transition: height 0.3s;
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
  background: var(--bg-card);
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
  background: var(--primary-container);
  color: var(--on-primary-container);
  border-radius: 8px;
  border: none;
}

.result-text {
  font-size: 14px;
  color: var(--text-primary);
  line-height: 1.6;
}

.voice-actions {
  padding: 0 16px;
}

/* 上传 */
.upload-step {
  padding: 40px 24px;
}

.upload-area {
  border: 2px dashed var(--border-color);
  border-radius: var(--radius-lg);
  padding: 40px;
  text-align: center;
  cursor: pointer;
  background: var(--surface-container-low);
  transition: all 0.2s;
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

.upload-preview {
  margin-top: 16px;
  background: var(--bg-card);
  border: none;
  border-radius: var(--radius-md);
  padding: 14px;
  box-shadow: var(--shadow-card);
}

.preview-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--text-primary);
}

.ocr-processing {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  font-size: 14px;
  color: var(--color-primary);
}

/* AI 处理中 */
.processing-step {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 80vh;
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

.processing-text {
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

/* 预览 */
.preview-step {
  padding: 16px 0;
}

.preview-header {
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

.preview-tip {
  font-size: 14px;
  color: var(--text-tertiary);
  margin-top: 8px;
}

.conditions-label {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 8px;
  padding-left: 4px;
}
</style>
