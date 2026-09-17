<template>
  <div class="page-container">
    <van-nav-bar title="新建客户档案" left-arrow @click-left="$router.back()" />

    <div class="create-page">
      <!-- 录入方式选择 -->
      <div class="mode-switch">
        <div class="mode-item" :class="{ active: mode === 'manual' }" @click="switchMode('manual')">
          <AppIcon name="edit" :size="16" />
          <span>手动录入</span>
        </div>
        <div class="mode-item" :class="{ active: mode === 'voice' }" @click="switchMode('voice')">
          <AppIcon name="volume" :size="16" />
          <span>语音录入</span>
        </div>
      </div>

      <!-- ============ 手动录入 ============ -->
      <template v-if="mode === 'manual'">
        <!-- 顶部引导 -->
        <div class="guide-banner">
          <div class="guide-icon">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" fill="#2563EB"/>
            </svg>
          </div>
          <div class="guide-text">
            <div class="guide-title">先建档，后补料</div>
            <div class="guide-desc">只需姓名和手机号即可创建档案，身份、流水、征信等材料后续在档案中陆续补充</div>
          </div>
        </div>

        <!-- 建档表单 -->
        <div class="form-card">
          <div class="card-label required">基础信息</div>
          <van-form @submit="onSave">
            <van-cell-group inset>
              <van-field
                v-model="form.name"
                label="姓名"
                placeholder="客户真实姓名"
                :rules="[{ required: true, message: '请输入客户姓名' }]"
              >
                <template #right-icon>
                  <VoiceMic label="客户姓名" sample="李建国" @confirm="form.name = $event" />
                </template>
              </van-field>
              <van-field
                v-model="form.phone"
                label="手机号"
                type="tel"
                maxlength="11"
                placeholder="客户联系电话"
                :rules="[
                  { required: true, message: '请输入手机号' },
                  { pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确' },
                ]"
              >
                <template #right-icon>
                  <VoiceMic label="手机号" sample="13812345678" @confirm="form.phone = $event" />
                </template>
              </van-field>
            </van-cell-group>

            <div class="card-label" style="margin-top: 20px;">选填信息</div>
            <van-cell-group inset>
              <van-field v-model="form.gender" label="性别" placeholder="请选择" is-link readonly @click="showGender = true" />
              <van-field v-model="form.age" label="年龄" type="digit" placeholder="如 32" />
              <van-field v-model="form.city" label="所在城市" placeholder="如 上海">
                <template #right-icon>
                  <VoiceMic label="所在城市" sample="上海" @confirm="form.city = $event" />
                </template>
              </van-field>
              <van-field v-model="form.occupation" label="职业" placeholder="如 互联网产品经理">
                <template #right-icon>
                  <VoiceMic label="职业" sample="互联网产品经理" @confirm="form.occupation = $event" />
                </template>
              </van-field>
            </van-cell-group>

            <!-- 客户来源 -->
            <div class="card-label" style="margin-top: 20px;">客户来源</div>
            <div class="source-grid">
              <div
                v-for="s in sources"
                :key="s.key"
                class="source-chip"
                :class="{ selected: form.source === s.key }"
                @click="form.source = s.key"
              >
                <span class="source-icon"><AppIcon :name="s.icon" :size="16" color="var(--color-primary)" /></span>
                <span class="source-name">{{ s.name }}</span>
              </div>
            </div>

            <!-- 意向备注 -->
            <div class="card-label" style="margin-top: 20px;">意向备注 <span class="optional">选填</span></div>
            <van-cell-group inset>
              <van-field
                v-model="form.remark"
                rows="2"
                autosize
                type="textarea"
                maxlength="100"
                show-word-limit
                placeholder="如：朋友介绍，意向信用贷 20 万，重点关注利率和放款速度"
              >
                <template #right-icon>
                  <VoiceMic label="意向备注" sample="朋友介绍，意向信用贷20万，重点关注利率和放款速度" @confirm="form.remark = $event" />
                </template>
              </van-field>
            </van-cell-group>

            <div style="margin: 24px 16px 8px;">
              <van-button round block type="primary" native-type="submit" :loading="saving" loading-text="创建中...">
                创建客户档案
              </van-button>
              <p class="form-tip">创建后可随时在客户档案中补充身份证、流水、征信等材料</p>
            </div>
          </van-form>
        </div>
      </template>

      <!-- ============ 语音录入 ============ -->
      <template v-else>
        <!-- 引导说明 -->
        <div class="voice-guide" v-if="voiceStep === 'idle'">
          <div class="voice-guide-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
              <path d="M12 14a3 3 0 0 0 3-3V5a3 3 0 0 0-6 0v6a3 3 0 0 0 3 3zm5-3a5 5 0 0 1-10 0H5a7 7 0 0 0 6 6.92V21h2v-3.08A7 7 0 0 0 19 11h-2z" fill="#2563EB"/>
            </svg>
          </div>
          <div class="voice-guide-text">
            <div class="voice-guide-title">口述客户信息，AI 自动建档</div>
            <div class="voice-guide-desc">说出客户姓名、电话、职业、收入、意向等，AI 自动识别资料类型并归档，无需手动填写</div>
          </div>
        </div>

        <!-- 录音 / 转写 / 识别 舞台 -->
        <div class="voice-stage">
          <!-- idle：开始录音 -->
          <template v-if="voiceStep === 'idle'">
            <div class="mic-btn" @click="startRecord">
              <AppIcon name="mic" :size="34" color="#071a17" />
            </div>
            <div class="stage-tip">
              点击开始录音，建议这样口述：<br>
              <span class="tip-example">"张三，男，32岁，电话13812345678，在上海做产品经理，月收入一万五，朋友介绍，想贷20万信用贷"</span>
            </div>
          </template>

          <!-- recording：录音中 -->
          <template v-else-if="voiceStep === 'recording'">
            <div class="mic-btn recording" @click="stopRecord">
              <span class="pulse p1"></span>
              <span class="pulse p2"></span>
              <span class="pulse p3"></span>
              <AppIcon name="stop" :size="28" color="#ffffff" class="stop-icon" />
            </div>
            <div class="record-time">{{ recordTime }}s</div>
            <div class="stage-tip">正在录音，点击停止结束并开始识别</div>
          </template>

          <!-- transcribing：语音转写 -->
          <template v-else-if="voiceStep === 'transcribing'">
            <div class="ai-anim">
              <van-loading color="#2563EB" size="36" vertical>语音转写中...</van-loading>
            </div>
            <div class="transcript-box" v-if="transcript">
              <AppIcon name="message" :size="14" color="#2563EB" />
              <span>{{ transcript }}</span>
            </div>
          </template>

          <!-- analyzing：AI 识别资料类型 -->
          <template v-else-if="voiceStep === 'analyzing'">
            <div class="ai-anim">
              <van-loading color="#2563EB" size="36" vertical>AI 正在识别资料类型并提取信息...</van-loading>
            </div>
            <div class="type-chips" v-if="recognizedTypes.length">
              <span class="type-chip" v-for="(t, i) in recognizedTypes" :key="t">
                {{ t }}
              </span>
            </div>
          </template>

          <!-- review：识别结果确认 -->
          <template v-if="voiceStep === 'review'">
            <div class="ai-result-card">
              <div class="result-header">
                <div class="result-title">
                  <AppIcon name="check-circle" :size="18" color="#2563EB" />
                  <span>AI 识别结果</span>
                </div>
                <div class="result-summary">{{ aiSummary }}</div>
              </div>

              <!-- 自动识别的资料类型 -->
              <div class="type-chips" style="margin: 12px 0 2px;">
                <span class="type-chip" v-for="t in recognizedTypes" :key="t">{{ t }}</span>
              </div>

              <!-- 字段分组 -->
              <div class="field-group" v-for="(group, gi) in reviewGroups" :key="gi">
                <div class="group-title">{{ group.title }}</div>
                <div class="field-item" v-for="f in group.fields" :key="f.key">
                  <div class="field-label-row">
                    <span class="field-label">{{ f.label }}</span>
                    <span class="conf-tag" :class="{ low: f.confidence < 0.85 }">
                      {{ Math.round(f.confidence * 100) }}%
                    </span>
                  </div>

                  <!-- 客户来源：chips 选择 -->
                  <div v-if="f.type === 'source'" class="source-grid mini">
                    <div
                      v-for="s in sources"
                      :key="s.key"
                      class="source-chip"
                      :class="{ selected: aiForm.source === s.key }"
                      @click="aiForm.source = s.key"
                    >
                      <span class="source-name">{{ s.name }}</span>
                    </div>
                  </div>

                  <!-- 其他字段：输入框 -->
                  <van-field
                    v-else
                    v-model="aiForm[f.key]"
                    :type="f.inputType || 'text'"
                    :placeholder="f.placeholder"
                    class="ai-field"
                  >
                    <template v-if="isVoiceable(f)" #right-icon>
                      <VoiceMic :label="f.label || '字段'" :sample="f.sample || ''" @confirm="aiForm[f.key] = $event" />
                    </template>
                  </van-field>
                </div>
              </div>

              <div class="result-actions">
                <van-button round plain type="primary" class="btn-retry" @click="resetVoice">
                  重新录入
                </van-button>
                <van-button round block type="primary" class="btn-confirm" :loading="saving" loading-text="建档中..." @click="confirmVoice">
                  确认建档
                </van-button>
              </div>
              <p class="form-tip">AI 提取结果可修改，确认后自动创建客户档案</p>
            </div>
          </template>
        </div>
      </template>

      <!-- 性别选择 -->
      <van-popup v-model:show="showGender" position="bottom" round>
        <van-picker
          :columns="genderColumns"
          @confirm="onGenderConfirm"
          @cancel="showGender = false"
          title="选择性别"
        />
      </van-popup>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { showSuccessToast, showToast } from 'vant'
import { useCustomerStore } from '../../stores/customer'
import VoiceMic from '../../components/VoiceMic.vue'
import { asr as asrApi, asrAudio, extractCustomerFromVoice } from '../../api/ai'
import { startRecording as launchRecorder } from '../../utils/recorder'

const router = useRouter()
const store = useCustomerStore()

const saving = ref(false)
const showGender = ref(false)
const genderColumns = [
  { text: '男', value: '男' },
  { text: '女', value: '女' },
]

const sources = [
  { key: 'friend', name: '朋友介绍', icon: 'users' },
  { key: 'telemarketing', name: '电话营销', icon: 'phone' },
  { key: 'walkin', name: '门店进件', icon: 'bank' },
  { key: 'online', name: '线上渠道', icon: 'link' },
  { key: 'referral', name: '老客转介绍', icon: 'refresh' },
  { key: 'other', name: '其他', icon: 'tag' },
]

/* ============ 手动录入 ============ */
const form = reactive({
  name: '',
  phone: '',
  gender: '',
  age: '',
  city: '',
  occupation: '',
  source: 'friend',
  remark: '',
})

function onGenderConfirm({ selectedOptions }) {
  form.gender = selectedOptions[0]?.value || ''
  showGender.value = false
}

function onSave() {
  submitCustomer(form)
}

/* ============ 语音录入 ============ */
const mode = ref('manual')
const voiceStep = ref('idle') // idle | recording | transcribing | analyzing | review
const recordTime = ref(0)
let recordTimer = null
let recorder = null
const transcript = ref('')
const recognizedTypes = ref([])
const aiSummary = ref('')
const aiForm = ref({})
const aiConfidence = ref({})

function switchMode(m) {
  if (mode.value === m) return
  mode.value = m
  if (m === 'voice') resetVoice()
}

async function startRecord() {
  try {
    recorder = await launchRecorder()
  } catch (e) {
    showToast(`${e.message}，已切换为演示模式`)
    recorder = null
  }
  voiceStep.value = 'recording'
  recordTime.value = 0
  recordTimer = setInterval(() => {
    recordTime.value += 1
  }, 1000)
}

async function stopRecord() {
  clearInterval(recordTimer)
  recordTimer = null
  voiceStep.value = 'transcribing'

  // 1. ASR 语音转文字（有真实录音则上传音频，否则走演示文本）
  let asrRes
  try {
    if (recorder) {
      const audio = await recorder.stop()
      recorder = null
      if (audio) asrRes = await asrAudio({ blob: audio.blob, sampleRate: audio.sampleRate })
    }
    if (!asrRes) asrRes = await asrApi()
  } catch (e) {
    showToast(e.message || '语音识别失败')
    voiceStep.value = 'idle'
    return
  }
  if (!(asrRes.text || '').trim()) {
    // 静音/非人声时阿里云返回空串，别让空文本流入大模型
    showToast('没有听清，请靠近麦克风再说一遍')
    voiceStep.value = 'idle'
    return
  }
  transcript.value = asrRes.text
  voiceStep.value = 'analyzing'

  // 2. 大模型自动识别资料类型并提取字段
  let result
  try {
    result = await extractCustomerFromVoice(asrRes.text)
  } catch (e) {
    showToast(e?.message || '信息提取失败，请重试')
    voiceStep.value = 'idle'
    return
  }
  recognizedTypes.value = result.recognizedTypes || []
  aiSummary.value = result.summary || ''
  aiConfidence.value = {}
  Object.entries(result.data || {}).forEach(([k, v]) => {
    aiConfidence.value[k] = v.confidence ?? result.confidence
  })
  aiForm.value = {
    name: result.data?.name?.value ?? '',
    phone: result.data?.phone?.value ?? '',
    gender: result.data?.gender?.value ?? '',
    age: result.data?.age?.value ?? '',
    city: result.data?.city?.value ?? '',
    occupation: result.data?.occupation?.value ?? '',
    source: result.data?.source?.value ?? 'friend',
    remark: result.data?.remark?.value ?? '',
    employer: result.data?.employer?.value ?? '',
    monthlyIncome: result.data?.monthlyIncome?.value ?? 0,
  }
  voiceStep.value = 'review'
}

function resetVoice() {
  clearInterval(recordTimer)
  recordTimer = null
  if (recorder) {
    recorder.cancel()
    recorder = null
  }
  voiceStep.value = 'idle'
  recordTime.value = 0
  transcript.value = ''
  recognizedTypes.value = []
  aiSummary.value = ''
  aiForm.value = {}
  aiConfidence.value = {}
}

const confOf = (key) => aiConfidence.value[key] ?? 0.9

// 离开页面时释放麦克风，避免录音流保持活跃
onBeforeUnmount(() => {
  resetVoice()
})

// 仅文本类字段（非数字/选择器）支持语音回填
const isVoiceable = (f) => f.type !== 'source' && !['number', 'digit'].includes(f.inputType || '')

const reviewGroups = computed(() => [
  {
    title: '客户基本信息',
    fields: [
      { key: 'name', label: '姓名', confidence: confOf('name'), placeholder: '客户真实姓名', sample: '李建国' },
      { key: 'phone', label: '手机号', confidence: confOf('phone'), inputType: 'tel', placeholder: '客户联系电话', sample: '13812345678' },
      { key: 'gender', label: '性别', confidence: confOf('gender'), placeholder: '如 男 / 女', sample: '男' },
      { key: 'age', label: '年龄', confidence: confOf('age'), inputType: 'digit', placeholder: '如 32' },
      { key: 'city', label: '所在城市', confidence: confOf('city'), placeholder: '如 上海', sample: '上海' },
      { key: 'occupation', label: '职业', confidence: confOf('occupation'), placeholder: '如 产品经理', sample: '产品经理' },
    ],
  },
  {
    title: '客户来源与意向',
    fields: [
      { key: 'source', label: '客户来源', confidence: confOf('source'), type: 'source' },
      { key: 'remark', label: '意向备注', confidence: confOf('remark'), placeholder: '意向产品、额度、关注点等', sample: '意向信用贷20万，重点关注放款速度' },
    ],
  },
  {
    title: '收入信息',
    fields: [
      { key: 'employer', label: '工作单位', confidence: confOf('employer'), placeholder: '如 某科技公司', sample: '上海沐光科技有限公司' },
      { key: 'monthlyIncome', label: '月均收入（元）', confidence: confOf('monthlyIncome'), inputType: 'digit', placeholder: '如 15000' },
    ],
  },
])

function confirmVoice() {
  if (!aiForm.value.name?.trim()) {
    showToast('AI 未识别到姓名，请手动补充')
    return
  }
  const phone = (aiForm.value.phone || '').replace(/\s/g, '')
  if (!/^1[3-9]\d{9}$/.test(phone)) {
    showToast('手机号格式不正确，请修正')
    return
  }
  submitCustomer({
    name: aiForm.value.name.trim(),
    phone,
    gender: aiForm.value.gender,
    age: aiForm.value.age,
    city: aiForm.value.city,
    occupation: aiForm.value.occupation,
    source: aiForm.value.source,
    remark: aiForm.value.remark,
    employer: aiForm.value.employer,
    monthlyIncome: Number(aiForm.value.monthlyIncome) || 0,
  })
}

/* ============ 建档公共逻辑 ============ */
async function submitCustomer(data) {
  // 检查是否已存在相同手机号的客户
  const phone = (data.phone || '').replace(/\s/g, '')
  const existing = store.customers.find((c) => c.phone.replace(/\s/g, '') === phone)
  if (existing) {
    showToast('该手机号已存在客户档案，已为你更新信息')
    await store.updateCustomer(existing.id, {
      name: data.name,
      gender: data.gender || existing.gender,
      age: Number(data.age) || existing.age,
      city: data.city || existing.city,
      occupation: data.occupation || existing.occupation,
      source: data.source || existing.source,
      remark: data.remark || existing.remark,
      employer: data.employer || existing.employer,
      monthlyIncome: Number(data.monthlyIncome) || existing.monthlyIncome,
    })
    setTimeout(() => router.replace(`/customers/${existing.id}`), 800)
    return
  }

  saving.value = true
  try {
    const created = await store.addCustomer({
      name: data.name,
      phone,
      gender: data.gender || '未知',
      age: Number(data.age) || 0,
      city: data.city || '',
      occupation: data.occupation || '',
      source: data.source,
      remark: data.remark || '',
      employer: data.employer || '',
      monthlyIncome: Number(data.monthlyIncome) || 0,
    })
    saving.value = false
    showSuccessToast('客户档案创建成功')
    setTimeout(() => router.replace(`/customers/${created.id}`), 800)
  } catch (err) {
    saving.value = false
    showToast(err.message || '创建失败，请重试')
  }
}
</script>

<style scoped>
.create-page {
  padding: 16px 0 32px;
}

/* ============ 录入方式切换 ============ */
.mode-switch {
  display: flex;
  margin: 0 16px 20px;
  padding: 4px;
  background: var(--surface-container);
  border: none;
  border-radius: 12px;
}

.mode-item {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 9px 0;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-tertiary);
  border-radius: 9px;
  cursor: pointer;
  transition: all 0.25s;
}

.mode-item.active {
  color: var(--on-primary-container);
  background: var(--primary-container);
  font-weight: 600;
  box-shadow: none;
}

/* ============ 手动录入 ============ */
.guide-banner {
  display: flex;
  align-items: center;
  gap: 14px;
  margin: 0 16px 20px;
  padding: 14px 16px;
  background: var(--primary-container);
  border: none;
  border-radius: var(--radius-md);
}

.guide-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: var(--surface-container-lowest);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.guide-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-primary);
  margin-bottom: 4px;
}

.guide-desc {
  font-size: 12px;
  color: var(--text-tertiary);
  line-height: 1.5;
}

.form-card {
  padding: 0 16px;
}

.card-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  padding-left: 4px;
  margin-bottom: 10px;
}

.card-label.required::after {
  content: ' *';
  color: var(--color-danger);
}

.card-label .optional {
  font-size: 11px;
  color: var(--text-tertiary);
  font-weight: 400;
}

.source-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-bottom: 4px;
}

.source-chip {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 14px 8px;
  background: var(--surface-container-low);
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s;
}

.source-chip.selected {
  background: var(--primary-container);
  box-shadow: none;
}

.source-icon {
  font-size: 20px;
}

.source-name {
  font-size: 12px;
  color: var(--text-primary);
}

.form-tip {
  text-align: center;
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 12px;
}

/* ============ 语音录入 ============ */
.voice-guide {
  display: flex;
  align-items: center;
  gap: 14px;
  margin: 0 16px 20px;
  padding: 14px 16px;
  background: var(--primary-container);
  border: none;
  border-radius: var(--radius-md);
}

.voice-guide-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: var(--surface-container-lowest);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.voice-guide-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-primary);
  margin-bottom: 4px;
}

.voice-guide-desc {
  font-size: 12px;
  color: var(--text-tertiary);
  line-height: 1.5;
}

/* 舞台 */
.voice-stage {
  padding: 10px 16px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* 麦克风按钮 */
.mic-btn {
  width: 96px;
  height: 96px;
  border-radius: 50%;
  background: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 28px rgba(37, 99, 235, 0.35);
  cursor: pointer;
  transition: transform 0.15s;
}

.mic-btn:active {
  transform: scale(0.95);
}

/* 录音中 */
.mic-btn.recording {
  background: var(--color-danger);
  box-shadow: 0 8px 28px rgba(240, 68, 56, 0.35);
  position: relative;
}

.stop-icon {
  position: relative;
  z-index: 2;
}

.pulse {
  position: absolute;
  border-radius: 50%;
  border: 2px solid rgba(255, 92, 92, 0.6);
  animation: pulse-ring 1.6s ease-out infinite;
}

.pulse.p1 { width: 100%; height: 100%; }
.pulse.p2 { width: 100%; height: 100%; animation-delay: 0.4s; }
.pulse.p3 { width: 100%; height: 100%; animation-delay: 0.8s; }

@keyframes pulse-ring {
  0% { transform: scale(1); opacity: 0.9; }
  100% { transform: scale(1.9); opacity: 0; }
}

.record-time {
  margin-top: 18px;
  font-size: 28px;
  font-weight: 700;
  color: #ff5c5c;
  font-variant-numeric: tabular-nums;
}

.stage-tip {
  margin-top: 16px;
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.8;
  text-align: center;
  padding: 0 24px;
}

.tip-example {
  color: var(--text-tertiary);
  font-size: 12px;
}

/* AI 处理动画 */
.ai-anim {
  display: flex;
  justify-content: center;
  padding: 46px 0 10px;
}

.transcript-box {
  width: 100%;
  margin-top: 16px;
  padding: 14px 16px;
  background: var(--surface-container);
  border: none;
  border-radius: var(--radius-md);
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-primary);
  display: flex;
  gap: 8px;
}

/* 资料类型 chips */
.type-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
  margin-top: 14px;
}

.type-chip {
  font-size: 12px;
  padding: 5px 12px;
  border-radius: 16px;
  background: var(--primary-container);
  border: none;
  color: var(--on-primary-container);
}

/* 识别结果卡片 */
.ai-result-card {
  width: 100%;
  margin-top: 4px;
  padding: 16px;
  background: var(--bg-card);
  border: none;
  border-radius: var(--radius-lg, 14px);
  box-shadow: var(--shadow-card);
}

.result-header {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.result-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.result-summary {
  font-size: 12px;
  color: var(--text-tertiary);
}

/* 字段分组 */
.field-group {
  margin-top: 16px;
}

.group-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-tertiary);
  margin-bottom: 8px;
  padding-left: 4px;
}

.field-item {
  margin-bottom: 10px;
}

.field-label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 4px;
  margin-bottom: 6px;
}

.field-label {
  font-size: 14px;
  color: var(--text-secondary);
}

.conf-tag {
  font-size: 11px;
  padding: 1px 7px;
  border-radius: 8px;
  background: var(--primary-container);
  color: var(--on-primary-container);
  border: none;
}

.conf-tag.low {
  background: var(--warning-container);
  color: var(--on-warning-container);
}

.ai-field {
  background: var(--surface-container);
  border: none;
  border-radius: 10px;
  padding: 4px 4px;
}

/* 来源 mini 选择 */
.source-grid.mini {
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.source-grid.mini .source-chip {
  flex-direction: row;
  justify-content: center;
  padding: 8px 4px;
  gap: 4px;
}

/* 操作按钮 */
.result-actions {
  display: flex;
  gap: 10px;
  margin-top: 22px;
}

.btn-retry {
  width: 110px;
  flex-shrink: 0;
}

.btn-confirm {
  flex: 1;
}
</style>
