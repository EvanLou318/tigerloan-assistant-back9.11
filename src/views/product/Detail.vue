<template>
  <div class="page-container">
    <van-nav-bar title="产品详情" left-arrow @click-left="$router.back()">
      <template #right>
        <AppIcon name="more" :size="18" @click="showActionSheet = true" />
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
        <div class="product-institution">
          <AppIcon name="bank" :size="14" class="inst-icon" />
          <span>{{ product.institution }}</span>
        </div>
      </div>

      <!-- 核心数据 -->
      <div class="rate-card">
        <div class="rate-row">
          <div class="rate-item">
            <div class="rate-value">{{ product.minRate }}<span class="rate-unit">%</span></div>
            <div class="rate-label">最低年利率</div>
          </div>
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
    { name: '删除产品', color: '#F04438' },
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
  padding: 12px 16px calc(88px + env(safe-area-inset-bottom));
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 头部：与其余区块统一为白卡，同一套圆角与内边距 */
.product-header {
  background: var(--surface-container);
  border-radius: var(--radius-md);
  padding: 16px;
  box-shadow: var(--shadow-card);
}

.header-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 6px;
}

.product-name {
  flex: 1;
  min-width: 0;
  font-size: 20px;
  font-weight: 700;
  line-height: 1.35;
  color: var(--text-primary);
}

.status-badge {
  font-size: 11px;
  padding: 4px 10px;
  border-radius: 8px;
  font-weight: 600;
  flex-shrink: 0;
  border: none;
}

.status-badge.active {
  background: var(--success-container);
  color: var(--on-success-container);
}

.status-badge.disabled {
  background: var(--surface-container-high);
  color: var(--text-secondary);
}

.product-institution {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  color: var(--text-secondary);
}

.inst-icon { color: var(--color-secondary); }

/* 核心数据：白卡 + tonal 色块，不用线条分隔 */
.rate-card {
  background: var(--surface-container);
  border-radius: var(--radius-md);
  padding: 16px;
  box-shadow: var(--shadow-card);
}

.rate-row {
  display: flex;
  align-items: stretch;
  gap: 12px;
  margin-bottom: 12px;
}

.rate-item {
  flex: 1;
  text-align: center;
  padding: 14px 8px;
  border-radius: var(--radius-sm);
  background: var(--d-product-50);
}

.rate-value {
  font-size: 28px;
  font-weight: 700;
  line-height: 1.2;
  color: var(--d-product-800);
  font-family: 'DIN', 'Roboto', sans-serif;
}

.rate-unit {
  font-size: 14px;
  font-weight: 600;
}

.rate-label {
  font-size: 12px;
  color: var(--d-product-600);
  margin-top: 4px;
}

.amount-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: var(--radius-sm);
  background: var(--d-product-50);
}

.amount-label {
  font-size: 12px;
  color: var(--d-product-600);
}

.amount-value {
  font-size: 16px;
  font-weight: 700;
  color: var(--d-product-800);
}

/* 信息区 */
.info-section { margin: 0; }

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 8px;
  padding-left: 2px;
}

.info-card {
  background: var(--surface-container);
  border-radius: var(--radius-md);
  padding: 4px 16px;
  box-shadow: var(--shadow-card);
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 13px 0;
}

.info-label {
  font-size: 14px;
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.info-value {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  text-align: right;
  min-width: 0;
  word-break: break-all;
}

.conditions-card {
  background: var(--surface-container);
  border-radius: var(--radius-md);
  padding: 16px;
  box-shadow: var(--shadow-card);
}

.conditions-text {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.7;
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
  box-shadow: 0 -1px 8px rgba(26, 34, 51, 0.04);
}

.action-bar .van-button {
  flex: 1;
  height: 46px;
}
</style>
