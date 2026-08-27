<template>
  <div class="page-container">
    <van-nav-bar title="场景推演" left-arrow @click-left="$router.back()">
      <template #right>
        <span class="save-btn" @click="showSaveDialog = true">保存</span>
      </template>
    </van-nav-bar>

    <div v-if="customer" class="simulation-page">
      <!-- 提示 -->
      <div class="tip-banner">
        <van-icon name="info-o" size="14" color="#06B6D4" />
        <span>推演模式下的调整不会影响客户真实档案</span>
      </div>

      <!-- 可调整指标 -->
      <div class="section">
        <div class="section-title">调整客户指标</div>
        <p class="section-desc">修改以下指标后点击「重新匹配」查看推演结果</p>

        <!-- 基础信息 -->
        <div class="adjust-group">
          <div class="group-label">基础信息</div>
          <div class="adjust-item" v-for="field in adjustFields.basic" :key="field.key">
            <span class="adjust-label">{{ field.label }}</span>
            <div class="adjust-control">
              <van-stepper
                v-model="simData[field.key]"
                :min="field.min ?? 0"
                :max="field.max ?? 999"
                :step="field.step ?? 1"
                :input-width="field.inputWidth || '60px'"
                button-size="24px"
              />
              <span class="adjust-unit">{{ field.unit }}</span>
            </div>
          </div>
        </div>

        <!-- 收入类 -->
        <div class="adjust-group">
          <div class="group-label">收入类</div>
          <div class="adjust-item" v-for="field in adjustFields.income" :key="field.key">
            <span class="adjust-label">{{ field.label }}</span>
            <div class="adjust-control">
              <van-stepper
                v-model="simData[field.key]"
                :min="field.min ?? 0"
                :step="field.step ?? 500"
                :input-width="field.inputWidth || '60px'"
                button-size="24px"
              />
              <span class="adjust-unit">{{ field.unit }}</span>
            </div>
            <span v-if="simData[field.key] !== originalData[field.key]" class="changed-tag">
              {{ simData[field.key] > originalData[field.key] ? '↑' : '↓' }} {{ Math.abs(simData[field.key] - originalData[field.key]) }}
            </span>
          </div>
        </div>

        <!-- 负债类 -->
        <div class="adjust-group">
          <div class="group-label">负债类</div>
          <div class="adjust-item" v-for="field in adjustFields.debt" :key="field.key">
            <span class="adjust-label">{{ field.label }}</span>
            <div class="adjust-control">
              <van-stepper
                v-model="simData[field.key]"
                :min="0"
                :step="field.step ?? 1000"
                :input-width="field.inputWidth || '60px'"
                button-size="24px"
              />
              <span class="adjust-unit">{{ field.unit }}</span>
            </div>
            <span v-if="simData[field.key] !== originalData[field.key]" class="changed-tag">
              {{ simData[field.key] > originalData[field.key] ? '↑' : '↓' }} {{ Math.abs(simData[field.key] - originalData[field.key]) }}
            </span>
          </div>
          <div class="adjust-item slider-item">
            <span class="adjust-label">信用卡使用率</span>
            <div class="adjust-control">
              <van-slider v-model="simData.creditCardUsage" :min="0" :max="100" :step="5" style="width: 120px;" bar-height="4px" active-color="#3B82F6" />
              <span class="adjust-unit">{{ simData.creditCardUsage }}%</span>
            </div>
          </div>
        </div>

        <!-- 征信类 -->
        <div class="adjust-group">
          <div class="group-label">征信类</div>
          <div class="adjust-item" v-for="field in adjustFields.credit" :key="field.key">
            <span class="adjust-label">{{ field.label }}</span>
            <div class="adjust-control">
              <van-stepper
                v-model="simData[field.key]"
                :min="0"
                :max="field.max ?? 99"
                :input-width="'50px'"
                button-size="24px"
              />
              <span class="adjust-unit">{{ field.unit }}</span>
            </div>
            <span v-if="simData[field.key] !== originalData[field.key]" class="changed-tag">
              {{ simData[field.key] > originalData[field.key] ? '↑' : '↓' }} {{ Math.abs(simData[field.key] - originalData[field.key]) }}
            </span>
          </div>
        </div>

        <!-- 资产类 -->
        <div class="adjust-group">
          <div class="group-label">资产类</div>
          <div class="adjust-item" v-for="field in adjustFields.asset" :key="field.key">
            <span class="adjust-label">{{ field.label }}</span>
            <div class="adjust-control">
              <van-stepper
                v-model="simData[field.key]"
                :min="0"
                :input-width="'60px'"
                button-size="24px"
              />
              <span class="adjust-unit">{{ field.unit }}</span>
            </div>
          </div>
          <div class="adjust-item">
            <span class="adjust-label">是否有抵押</span>
            <div class="adjust-control">
              <van-switch v-model="simData.hasMortgage" size="20px" />
            </div>
          </div>
        </div>

        <!-- 期望条件 -->
        <div class="adjust-group">
          <div class="group-label">期望条件</div>
          <div class="adjust-item" v-for="field in adjustFields.expect" :key="field.key">
            <span class="adjust-label">{{ field.label }}</span>
            <div class="adjust-control">
              <van-stepper
                v-model="simData[field.key]"
                :min="0"
                :input-width="'60px'"
                button-size="24px"
                :step="field.step ?? 1"
              />
              <span class="adjust-unit">{{ field.unit }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 变更对照 -->
      <div v-if="hasChanges" class="section">
        <div class="section-title">变更对照</div>
        <div class="changes-list">
          <div class="change-item" v-for="(change, key) in changes" :key="key">
            <span class="change-field">{{ fieldLabels[key] || key }}</span>
            <span class="change-old">{{ formatValue(key, change.old) }}</span>
            <van-icon name="arrow" size="12" color="#475569" />
            <span class="change-new" :class="change.new > change.old ? 'up' : 'down'">{{ formatValue(key, change.new) }}</span>
          </div>
        </div>
      </div>

      <!-- 推演结果 -->
      <div v-if="simResult" ref="resultSection" :key="resultKey" class="section result-section">
        <div class="section-title">推演匹配结果</div>

        <!-- 结果概要 -->
        <div class="sim-summary">
          <div class="sim-stat">
            <div class="sim-stat-value approved">{{ simResult.approved.length }}</div>
            <div class="sim-stat-label">准入</div>
          </div>
          <div class="sim-stat">
            <div class="sim-stat-value rejected">{{ simResult.rejected.length }}</div>
            <div class="sim-stat-label">拒贷</div>
          </div>
        </div>

        <!-- 准入产品 -->
        <div v-if="simResult.approved.length > 0" class="result-list">
          <div v-for="item in simResult.approved" :key="item.productId" class="result-card approved">
            <div class="result-name">{{ item.productName }}</div>
            <div class="result-institution">{{ item.institution }}</div>
            <div class="result-reason" v-for="reason in item.reasons" :key="reason">
              <span class="check">✓</span> {{ reason }}
            </div>
          </div>
        </div>

        <!-- 拒贷产品 -->
        <div v-if="simResult.rejected.length > 0" class="result-list">
          <div v-for="item in simResult.rejected" :key="item.productId" class="result-card rejected">
            <div class="result-name">{{ item.productName }}</div>
            <div class="result-institution">{{ item.institution }}</div>
            <div class="result-reason" v-for="cond in item.failedConditions" :key="cond.condition">
              <span class="cross">✕</span> {{ cond.condition }}（{{ cond.value }}）
              <div v-if="cond.suggestion" class="suggestion">💡 {{ cond.suggestion }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 重新匹配按钮 -->
      <div class="action-bar">
        <van-button plain round @click="resetAdjustments" :disabled="!hasChanges">
          重置
        </van-button>
        <van-button round type="primary" :loading="matching" loading-text="AI匹配中..." @click="runSimulation">
          重新匹配
        </van-button>
      </div>
    </div>

    <!-- 保存弹窗 -->
    <van-dialog
      v-model:show="showSaveDialog"
      title="保存推演记录"
      confirm-button-text="保存"
      @confirm="saveSimulation"
    >
      <div style="padding: 16px;">
        <van-field
          v-model="saveName"
          label="推演名称"
          placeholder="如：调高收入+降低负债方案"
        />
      </div>
    </van-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showSuccessToast } from 'vant'
import { useCustomerStore } from '../../stores/customer'
import { useProductStore } from '../../stores/product'
import { matchProducts } from '../../api/ai'

const route = useRoute()
const router = useRouter()
const customerStore = useCustomerStore()
const productStore = useProductStore()

const customer = computed(() => customerStore.getCustomerById(route.params.id))
const matching = ref(false)
const simResult = ref(null)
const showSaveDialog = ref(false)
const saveName = ref('')
const resultSection = ref(null)
const resultKey = ref(0) // 每次新结果 +1，触发结果区重新挂载以重播入场动画

const originalData = reactive({})
const simData = reactive({})

const adjustFields = {
  basic: [
    { key: 'age', label: '年龄', unit: '岁', min: 18, max: 100 },
  ],
  income: [
    { key: 'monthlyIncome', label: '月均收入', unit: '元', step: 500 },
    { key: 'housingFundBase', label: '公积金基数', unit: '元', step: 100 },
  ],
  debt: [
    { key: 'totalDebt', label: '总负债', unit: '元', step: 1000 },
  ],
  credit: [
    { key: 'queryCount1m', label: '近1月查询', unit: '次' },
    { key: 'queryCount3m', label: '近3月查询', unit: '次' },
    { key: 'queryCount6m', label: '近6月查询', unit: '次' },
    { key: 'maxOverdueMonths', label: '最长逾期', unit: '月', max: 12 },
  ],
  asset: [
    { key: 'propertyValue', label: '房产价值', unit: '万' },
    { key: 'carValue', label: '车辆价值', unit: '万' },
  ],
  expect: [
    { key: 'expectedAmount', label: '期望额度', unit: '万' },
    { key: 'expectedRate', label: '期望利率上限', unit: '%', max: 100, step: 0.5 },
  ],
}

const fieldLabels = {
  age: '年龄',
  monthlyIncome: '月均收入',
  housingFundBase: '公积金基数',
  totalDebt: '总负债',
  creditCardUsage: '信用卡使用率',
  queryCount1m: '近1月查询',
  queryCount3m: '近3月查询',
  queryCount6m: '近6月查询',
  maxOverdueMonths: '最长逾期',
  propertyValue: '房产价值',
  carValue: '车辆价值',
  expectedAmount: '期望额度',
  expectedRate: '期望利率上限',
  hasMortgage: '是否有抵押',
}

const hasChanges = computed(() => {
  for (const key in originalData) {
    if (simData[key] !== originalData[key]) return true
  }
  return false
})

const changes = computed(() => {
  const result = {}
  for (const key in originalData) {
    if (simData[key] !== originalData[key]) {
      result[key] = { old: originalData[key], new: simData[key] }
    }
  }
  return result
})

function formatValue(key, val) {
  if (key === 'hasMortgage') return val ? '是' : '否'
  if (key === 'creditCardUsage') return val + '%'
  if (['monthlyIncome', 'housingFundBase', 'totalDebt'].includes(key)) {
    return val >= 10000 ? (val / 10000).toFixed(1) + '万' : val + '元'
  }
  if (['propertyValue', 'carValue', 'expectedAmount'].includes(key)) return val + '万'
  if (key === 'expectedRate') return val + '%'
  return val
}

function initSimData() {
  if (!customer.value) return
  const c = customer.value
  const fields = ['age', 'monthlyIncome', 'housingFundBase', 'totalDebt', 'creditCardUsage',
    'queryCount1m', 'queryCount3m', 'queryCount6m', 'maxOverdueMonths',
    'propertyValue', 'carValue', 'expectedAmount', 'expectedRate']
  
  for (const key of fields) {
    simData[key] = c[key]
    originalData[key] = c[key]
  }
  simData.hasMortgage = c.hasMortgage
  originalData.hasMortgage = c.hasMortgage
}

function resetAdjustments() {
  for (const key in originalData) {
    simData[key] = originalData[key]
  }
  simResult.value = null
  showToast('已重置')
}

async function runSimulation() {
  matching.value = true
  // 构建模拟客户数据
  const simCustomer = {
    ...customer.value,
    ...simData,
  }
  const result = await matchProducts(simCustomer, productStore.products)
  simResult.value = result
  matching.value = false

  // 结果产生后：重播入场动画 + 自动平滑上滑到结果第一屏
  resultKey.value++
  await nextTick()
  resultSection.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

async function saveSimulation() {
  if (!saveName.value) {
    showToast('请输入推演名称')
    return
  }
  const adjustments = {}
  for (const key in originalData) {
    if (simData[key] !== originalData[key]) {
      adjustments[key] = { old: originalData[key], new: simData[key] }
    }
  }
  await customerStore.addSimulation({
    customerId: customer.value.id,
    name: saveName.value,
    adjustments,
    matchResult: simResult.value,
  })
  saveName.value = ''
  showSuccessToast('推演记录已保存')
}

onMounted(async () => {
  // 先加载客户与推演历史（覆盖直接刷新进入本页的场景）
  try {
    await customerStore.loadCustomers()
    await customerStore.loadSimulations(route.params.id)
    await productStore.loadProducts(true)
  } catch (e) { /* 拦截器已提示 */ }
  initSimData()
  // 如果是加载历史推演
  if (route.query.load) {
    const sim = customerStore.simulations.find(s => s.id === route.query.load)
    if (sim) {
      // 恢复调整项
      for (const key in sim.adjustments) {
        simData[key] = sim.adjustments[key].new
      }
      simResult.value = sim.matchResult
      showToast('已加载历史推演记录')
    }
  }
})
</script>

<style scoped>
.simulation-page {
  padding-bottom: 80px;
}

/* 结果区：入场动画（每次新结果重播）+ 滚动定位留出导航高度 */
.result-section {
  scroll-margin-top: 56px;
  animation: result-in 0.45s cubic-bezier(0.2, 0, 0, 1);
}

@keyframes result-in {
  from {
    opacity: 0;
    transform: translateY(18px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.tip-banner {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  background: var(--secondary-container);
  border-bottom: none;
  font-size: 12px;
  color: var(--on-secondary-container);
}

.save-btn {
  color: var(--color-primary);
  font-size: 14px;
  font-weight: 500;
}

.section {
  padding: 16px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
  position: relative;
  padding-left: 10px;
}

.section-title::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 14px;
  border-radius: 2px;
  background: var(--gradient-primary);
}

.section-desc {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-bottom: 16px;
  padding-left: 10px;
}

/* 调整组 */
.adjust-group {
  margin-bottom: 16px;
}

.group-label {
  font-size: 12px;
  color: var(--color-secondary);
  font-weight: 600;
  margin-bottom: 8px;
  padding-left: 4px;
}

.adjust-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background: var(--surface-container);
  border: none;
  border-radius: var(--radius-sm);
  margin-bottom: 6px;
}

.adjust-label {
  font-size: 14px;
  color: var(--text-secondary);
  flex-shrink: 0;
}

.adjust-control {
  display: flex;
  align-items: center;
  gap: 6px;
}

.adjust-unit {
  font-size: 12px;
  color: var(--text-tertiary);
  min-width: 24px;
}

.changed-tag {
  font-size: 11px;
  padding: 1px 6px;
  background: rgba(59, 130, 246, 0.12);
  color: var(--color-primary);
  border-radius: 4px;
}

/* 滑块 */
.slider-item .adjust-control {
  gap: 10px;
}

/* 变更对照 */
.changes-list {
  background: var(--surface-container);
  border: none;
  border-radius: var(--radius-md);
  padding: 12px 16px;
  box-shadow: var(--shadow-card);
}

.change-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  border-bottom: none;
  font-size: 14px;
}

.change-item:last-child {
  border-bottom: none;
}

.change-field {
  flex: 1;
  color: var(--text-secondary);
}

.change-old {
  color: var(--text-tertiary);
  text-decoration: line-through;
}

.change-new.up {
  color: var(--color-success);
}

.change-new.down {
  color: var(--color-warning);
}

/* 推演结果 */
.sim-summary {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}

.sim-stat {
  flex: 1;
  text-align: center;
  padding: 12px;
  background: var(--surface-container);
  border: none;
  border-radius: var(--radius-sm);
}

.sim-stat-value {
  font-size: 24px;
  font-weight: 700;
  font-family: 'DIN', sans-serif;
}

.sim-stat-value.approved { color: var(--color-success); }
.sim-stat-value.rejected { color: var(--color-danger); }

.sim-stat-label {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 2px;
}

.result-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.result-card {
  background: var(--surface-container);
  border: none;
  border-radius: var(--radius-sm);
  padding: 14px;
  box-shadow: var(--shadow-card);
}

.result-card.approved {
  border-left: 3px solid var(--color-success);
}

.result-card.rejected {
  border-left: 3px solid var(--color-danger);
}

.result-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.result-institution {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-bottom: 6px;
}

.result-reason {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.6;
}

.check {
  color: var(--color-success);
}

.cross {
  color: var(--color-danger);
}

.suggestion {
  margin-top: 4px;
  padding-left: 16px;
  color: var(--color-warning);
  font-size: 11px;
}

/* 操作栏 */
.action-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  gap: 12px;
  padding: 12px 16px;
  padding-bottom: calc(12px + env(safe-area-inset-bottom));
  background: var(--surface-container-lowest);
  border-top: none;
  box-shadow: 0 -4px 16px rgba(0, 0, 0, 0.06);
}

.action-bar .van-button {
  flex: 1;
}
</style>
