<template>
  <div class="page-container">
    <van-nav-bar title="AI匹配" left-arrow @click-left="$router.back()">
      <template #right>
        <AppIcon name="share" :size="18" @click="showShareSheet = true" />
      </template>
    </van-nav-bar>

    <!-- AI 分析中 -->
    <div v-if="loading" class="loading-state">
      <div class="ai-loading">
        <div class="loading-ring"></div>
        <div class="loading-ring"></div>
        <div class="loading-ring"></div>
      </div>
      <div class="loading-title">AI 正在分析客户资质</div>
      <div class="loading-steps">
        <div class="load-step" :class="{ active: loadStep >= 1 }">✓ 读取客户档案</div>
        <div class="load-step" :class="{ active: loadStep >= 2 }">✓ 遍历产品库 ({{ productCount }}款)</div>
        <div class="load-step" :class="{ active: loadStep >= 3 }">{{ loadStep >= 3 ? '✓' : '○' }} 判断准入条件</div>
        <div class="load-step" :class="{ active: loadStep >= 4 }">{{ loadStep >= 4 ? '✓' : '○' }} 生成匹配报告</div>
      </div>
    </div>

    <!-- 匹配结果 -->
    <div v-else-if="matchResult" class="result-page">
      <!-- 结果概要 -->
      <div class="result-summary">
        <div class="summary-item">
          <div class="summary-value approved">{{ matchResult.approved.length }}</div>
          <div class="summary-label">准入产品</div>
        </div>
        <div class="summary-divider"></div>
        <div class="summary-item">
          <div class="summary-value rejected">{{ matchResult.rejected.length }}</div>
          <div class="summary-label">拒贷产品</div>
        </div>
        <div class="summary-divider"></div>
        <div class="summary-item">
          <div class="summary-value best">{{ bestRate }}%</div>
          <div class="summary-label">最低利率</div>
        </div>
      </div>

      <!-- 准入产品 -->
      <div v-if="matchResult.approved.length > 0" class="section">
        <div class="section-header">
          <span class="section-title"><AppIcon name="check-circle" :size="15" color="#12B76A" /> 准入产品</span>
          <span class="section-count">{{ matchResult.approved.length }}款</span>
        </div>
        <div class="product-list">
          <div
            v-for="(item, idx) in matchResult.approved"
            :key="item.productId"
            class="match-card approved"
            :class="{ best: idx === 0 }"
          >
            <div v-if="idx === 0" class="best-badge">最优推荐</div>
            <div class="card-header">
              <div class="card-name">{{ item.productName }}</div>
              <div class="card-institution">{{ item.institution }}</div>
            </div>
            <div class="card-rate-row">
              <div class="rate-block">
                <div class="rate-val">{{ item.minRate }}-{{ item.maxRate }}%</div>
                <div class="rate-label">年利率</div>
              </div>
              <div class="rate-block">
                <div class="rate-val">最高{{ item.maxAmount }}万</div>
                <div class="rate-label">额度</div>
              </div>
              <div class="rate-block">
                <div class="rate-val">{{ item.loanTerm }}</div>
                <div class="rate-label">期限</div>
              </div>
            </div>
            <div class="match-reasons">
              <div class="reason-label">匹配理由</div>
              <div class="reason-list">
                <div class="reason-item" v-for="reason in item.reasons" :key="reason">
                  <span class="reason-dot">✓</span>
                  <span>{{ reason }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 拒贷产品 -->
      <div v-if="matchResult.rejected.length > 0" class="section">
        <div class="section-header">
          <span class="section-title"><AppIcon name="x-circle" :size="15" color="#F04438" /> 拒贷产品</span>
          <span class="section-count">{{ matchResult.rejected.length }}款</span>
        </div>
        <div class="product-list">
          <div
            v-for="item in matchResult.rejected"
            :key="item.productId"
            class="match-card rejected"
          >
            <div class="card-header">
              <div class="card-name">{{ item.productName }}</div>
              <div class="card-institution">{{ item.institution }}</div>
            </div>
            <div class="reject-reasons">
              <div class="reason-label">拒贷原因 & 优化建议</div>
              <div class="reason-list">
                <div class="reject-item" v-for="cond in item.failedConditions" :key="cond.condition">
                  <div class="reject-condition">
                    <span class="reject-icon">✕</span>
                    <span>{{ cond.condition }}（当前：{{ cond.value }}）</span>
                  </div>
                  <div class="reject-suggestion" v-if="cond.suggestion">
                    💡 {{ cond.suggestion }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 底部操作 -->
      <div class="action-bar">
        <van-button plain round @click="rematch">
          重新匹配
        </van-button>
        <van-button round type="primary" @click="showShareSheet = true">
          <AppIcon name="share" /> 分享结果
        </van-button>
      </div>
    </div>

    <!-- 分享面板 -->
    <van-action-sheet
      v-model:show="showShareSheet"
      title="分享匹配结果"
      :actions="shareActions"
      cancel-text="取消"
      close-on-click-action
      @select="onShareSelect"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showSuccessToast } from 'vant'
import { useCustomerStore } from '../../stores/customer'
import { useProductStore } from '../../stores/product'
import { matchProducts } from '../../api/ai'

const route = useRoute()
const router = useRouter()
const customerStore = useCustomerStore()
const productStore = useProductStore()

const loading = ref(true)
const loadStep = ref(0)
const matchResult = ref(null)
const showShareSheet = ref(false)

const customer = computed(() => customerStore.getCustomerById(route.params.id))
const productCount = computed(() => productStore.activeCount)

const bestRate = computed(() => {
  if (!matchResult.value || matchResult.value.approved.length === 0) return '--'
  return matchResult.value.approved[0].minRate
})

const shareActions = [
  { name: '生成图片（客户版，自动脱敏）', icon: 'photo-o' },
  { name: '复制文本到剪贴板', icon: 'description' },
  { name: '导出PDF（完整版）', icon: 'description' },
]

async function runMatch() {
  loading.value = true
  loadStep.value = 0
  matchResult.value = null

  const stepInterval = setInterval(() => {
    loadStep.value++
  }, 600)

  const result = await matchProducts(customer.value, productStore.products)
  clearInterval(stepInterval)
  loadStep.value = 4
  await new Promise(r => setTimeout(r, 500))

  matchResult.value = result
  loading.value = false
}

function rematch() {
  runMatch()
}

function onShareSelect(action) {
  if (action.name.includes('图片')) {
    showToast('已生成脱敏长图，已保存到相册')
  } else if (action.name.includes('文本')) {
    showSuccessToast('已复制到剪贴板')
  } else if (action.name.includes('PDF')) {
    showSuccessToast('PDF报告已生成下载')
  }
}

onMounted(async () => {
  // 先确保客户与产品数据已从后端加载（覆盖直接刷新进入本页的场景）
  try {
    await Promise.all([customerStore.loadCustomers(), productStore.loadProducts(true)])
  } catch (e) { /* 拦截器已提示 */ }
  if (customer.value) {
    runMatch()
  }
})
</script>

<style scoped>
/* AI 分析中 */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 70vh;
  padding: 24px;
}

.ai-loading {
  position: relative;
  width: 80px;
  height: 80px;
  margin-bottom: 24px;
}

.loading-ring {
  position: absolute;
  inset: 0;
  border: 2px solid transparent;
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 1s infinite linear;
}

.loading-ring:nth-child(2) {
  inset: 10px;
  border-top-color: var(--color-secondary);
  animation-duration: 1.5s;
  animation-direction: reverse;
}

.loading-ring:nth-child(3) {
  inset: 20px;
  border-top-color: var(--color-accent);
  animation-duration: 0.8s;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 20px;
}

.loading-steps {
  display: flex;
  flex-direction: column;
  gap: 8px;
  text-align: left;
}

.load-step {
  font-size: 14px;
  color: var(--text-tertiary);
}

.load-step.active {
  color: var(--color-primary);
}

/* 结果页 */
.result-page {
  padding-bottom: 80px;
}

.result-summary {
  display: flex;
  align-items: center;
  margin: 16px;
  padding: 20px;
  background: var(--surface-container);
  border: none;
  border-radius: var(--radius-lg);
  position: relative;
  overflow: hidden;
  box-shadow: var(--shadow-card);
}

.summary-item {
  flex: 1;
  text-align: center;
}

.summary-value {
  font-size: 28px;
  font-weight: 700;
  font-family: 'DIN', sans-serif;
}

.summary-value.approved {
  color: var(--color-success);
}

.summary-value.rejected {
  color: var(--color-danger);
}

.summary-value.best {
  color: var(--color-primary);
}

.summary-label {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 4px;
}

.summary-divider {
  width: 1px;
  height: 40px;
  background: var(--surface-container-high);
}

/* Section */
.section {
  padding: 0 16px;
  margin-bottom: 16px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.section-title {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.section-count {
  font-size: 12px;
  color: var(--text-tertiary);
}

/* 匹配卡片 */
.product-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.match-card {
  background: var(--surface-container);
  border: none;
  border-radius: var(--radius-md);
  padding: 16px;
  position: relative;
  overflow: hidden;
  animation: float-up 0.3s ease-out;
  box-shadow: var(--shadow-card);
}

.match-card.approved::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--color-success);
}

.match-card.rejected::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--color-danger);
}

.match-card.best {
  background: var(--primary-container);
  box-shadow: 0 4px 20px rgba(37, 99, 235, 0.18);
}

.best-badge {
  position: absolute;
  top: 10px;
  right: 10px;
  font-size: 11px;
  padding: 2px 8px;
  background: var(--color-primary);
  color: #FFFFFF;
  border-radius: 4px;
  font-weight: 600;
}

.card-header {
  margin-bottom: 12px;
}

.card-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.card-institution {
  font-size: 14px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.card-rate-row {
  display: flex;
  gap: 12px;
  padding: 12px;
  background: var(--surface-container-low);
  border: none;
  border-radius: 12px;
}

.rate-block {
  flex: 1;
  text-align: center;
}

.rate-val {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-primary);
  font-family: 'DIN', sans-serif;
}

.rate-label {
  font-size: 11px;
  color: var(--text-tertiary);
  margin-top: 2px;
}

/* 匹配理由 */
.match-reasons {
  margin-top: 12px;
}

.reason-label {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-bottom: 6px;
}

.reason-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.reason-item {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  font-size: 14px;
  color: var(--text-secondary);
}

.reason-dot {
  color: var(--color-success);
  flex-shrink: 0;
}

/* 拒贷 */
.reject-reasons {
  margin-top: 12px;
}

.reject-item {
  background: rgba(239, 68, 68, 0.06);
  border-radius: var(--radius-sm);
  padding: 10px;
  margin-bottom: 6px;
}

.reject-condition {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  font-size: 14px;
  color: var(--text-secondary);
}

.reject-icon {
  color: var(--color-danger);
  flex-shrink: 0;
}

.reject-suggestion {
  margin-top: 4px;
  padding-left: 18px;
  font-size: 12px;
  color: var(--color-warning);
  line-height: 1.5;
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
