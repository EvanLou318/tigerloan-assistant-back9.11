<template>
  <div class="page-container">
    <van-nav-bar title="产品详情" left-arrow @click-left="$router.back()">
      <template #right>
        <van-icon name="ellipsis" size="18" @click="showActionSheet = true" />
      </template>
    </van-nav-bar>

    <div v-if="product" class="detail-page">
      <!-- 产品头部 -->
      <div class="product-header">
        <div class="header-top">
          <h2 class="product-name">{{ product.productName }}</h2>
          <div class="status-badge" :class="product.status">
            {{ product.status === 'active' ? '启用中' : '已禁用' }}
          </div>
        </div>
        <div class="product-institution">{{ product.institution }}</div>
      </div>

      <!-- 核心数据 -->
      <div class="rate-card">
        <div class="rate-row">
          <div class="rate-item">
            <div class="rate-value">{{ product.minRate }}<span class="rate-unit">%</span></div>
            <div class="rate-label">最低年利率</div>
          </div>
          <div class="rate-divider"></div>
          <div class="rate-item">
            <div class="rate-value">{{ product.maxRate }}<span class="rate-unit">%</span></div>
            <div class="rate-label">最高年利率</div>
          </div>
        </div>
        <div class="amount-info">
          <span class="amount-label">贷款额度</span>
          <span class="amount-value">{{ product.minAmount }} - {{ product.maxAmount }} 万</span>
        </div>
      </div>

      <!-- 基本信息 -->
      <div class="info-section">
        <div class="section-title">基本信息</div>
        <div class="info-card">
          <div class="info-item">
            <span class="info-label">贷款期限</span>
            <span class="info-value">{{ product.loanTerm }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">还款方式</span>
            <span class="info-value">{{ product.repaymentMethod }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">录入方式</span>
            <span class="info-value">{{ sourceLabels[product.source] || '文本录入' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">创建时间</span>
            <span class="info-value">{{ product.createdAt }}</span>
          </div>
        </div>
      </div>

      <!-- 准入条件 -->
      <div class="info-section">
        <div class="section-title">准入条件</div>
        <div class="conditions-card">
          <div class="conditions-text">{{ product.conditions }}</div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="action-bar">
        <van-button plain round @click="$router.push(`/products/create?edit=${product.id}`)">
          编辑
        </van-button>
        <van-button round type="primary" @click="goMatch">
          匹配客户
        </van-button>
      </div>
    </div>

    <!-- 操作菜单 -->
    <van-action-sheet
      v-model:show="showActionSheet"
      :actions="actions"
      cancel-text="取消"
      close-on-click-action
      @select="onActionSelect"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showSuccessToast, showConfirmDialog } from 'vant'
import { useProductStore } from '../../stores/product'

const route = useRoute()
const router = useRouter()
const store = useProductStore()
const showActionSheet = ref(false)

// 进入详情页从后端拉取最新数据
onMounted(() => {
  store.loadProducts(true)
})

const product = computed(() => store.getProductById(route.params.id))

const sourceLabels = {
  text: '文本录入',
  voice: '语音录入',
  image: '图片录入',
  pdf: 'PDF录入',
}

const actions = computed(() => {
  if (!product.value) return []
  return [
    { name: product.value.status === 'active' ? '禁用产品' : '启用产品' },
    { name: '删除产品', color: '#EF4444' },
  ]
})

async function onActionSelect(action) {
  if (action.name === '禁用产品' || action.name === '启用产品') {
    try {
      await store.toggleStatus(product.value.id)
      showSuccessToast(action.name === '禁用产品' ? '已禁用' : '已启用')
    } catch (e) {
      showToast(e.message || '操作失败')
    }
  } else if (action.name === '删除产品') {
    showConfirmDialog({
      title: '确认删除',
      message: '删除后产品将不在匹配列表中展示，数据可恢复',
    })
      .then(async () => {
        try {
          await store.deleteProduct(product.value.id)
          showSuccessToast('删除成功')
          setTimeout(() => router.replace('/products'), 800)
        } catch (e) {
          showToast(e.message || '删除失败')
        }
      })
      .catch(() => {})
  }
}

function goMatch() {
  router.push('/customers')
}
</script>

<style scoped>
.detail-page {
  padding: 0 0 80px;
}

.product-header {
  padding: 20px 16px 16px;
  background: transparent;
  border-bottom: none;
}

.header-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 4px;
}

.product-name {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
}

.status-badge {
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 8px;
  font-weight: 500;
  flex-shrink: 0;
  border: none;
}

.status-badge.active {
  background: var(--success-container);
  color: var(--on-success-container);
}

.status-badge.disabled {
  background: var(--danger-container);
  color: var(--on-danger-container);
}

.product-institution {
  font-size: 14px;
  color: var(--text-secondary);
}

/* 核心数据 */
.rate-card {
  margin: 16px;
  padding: 20px;
  background: var(--bg-card);
  border: none;
  border-radius: var(--radius-lg);
  position: relative;
  overflow: hidden;
  box-shadow: var(--shadow-card);
}

.rate-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--gradient-primary);
}

.rate-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
  margin-bottom: 16px;
}

.rate-item {
  text-align: center;
}

.rate-value {
  font-size: 32px;
  font-weight: 700;
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-family: 'DIN', sans-serif;
}

.rate-unit {
  font-size: 16px;
}

.rate-label {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 2px;
}

.rate-divider {
  width: 1px;
  height: 40px;
  background: var(--surface-container-high);
}

.amount-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 16px;
  border-top: none;
}

.amount-label {
  font-size: 14px;
  color: var(--text-secondary);
}

.amount-value {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

/* 信息区 */
.info-section {
  padding: 0 16px;
  margin-bottom: 16px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 10px;
  padding-left: 10px;
  position: relative;
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

.info-card {
  background: var(--bg-card);
  border: none;
  border-radius: var(--radius-md);
  overflow: hidden;
  box-shadow: var(--shadow-card);
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: none;
}

.info-item:last-child {
  border-bottom: none;
}

.info-label {
  font-size: 14px;
  color: var(--text-tertiary);
}

.info-value {
  font-size: 14px;
  color: var(--text-primary);
}

.conditions-card {
  background: var(--bg-card);
  border: none;
  border-radius: var(--radius-md);
  padding: 16px;
  box-shadow: var(--shadow-card);
}

.conditions-text {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.8;
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
  box-shadow: 0 -1px 8px rgba(26, 34, 51, 0.04);
}

.action-bar .van-button {
  flex: 1;
}
</style>
