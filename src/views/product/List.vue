<template>
  <MainLayout>
    <div class="product-list-page">
      <van-nav-bar title="智能产品库" :border="false" />

      <!-- 搜索栏 -->
      <div class="search-bar">
        <van-search
          v-model="store.searchKeyword"
          placeholder="搜索产品名称或机构"
          shape="round"
          :clearable="true"
        />
      </div>

      <!-- 筛选标签 -->
      <div class="filter-tabs">
        <div
          class="filter-tab"
          :class="{ active: store.filterStatus === '' }"
          @click="store.filterStatus = ''"
        >
          全部 <span class="count">{{ store.products.length }}</span>
        </div>
        <div
          class="filter-tab"
          :class="{ active: store.filterStatus === 'active' }"
          @click="store.filterStatus = 'active'"
        >
          启用 <span class="count">{{ store.activeCount }}</span>
        </div>
        <div
          class="filter-tab"
          :class="{ active: store.filterStatus === 'disabled' }"
          @click="store.filterStatus = 'disabled'"
        >
          禁用
        </div>
      </div>

      <!-- 产品列表 -->
      <div class="product-list">
        <div
          v-for="product in store.filteredProducts"
          :key="product.id"
          class="product-card"
          @click="$router.push(`/products/${product.id}`)"
        >
          <div class="card-header">
            <div class="product-name">{{ product.productName }}</div>
            <div class="status-badge" :class="product.status">
              {{ product.status === 'active' ? '启用' : '已禁用' }}
            </div>
          </div>

          <div class="card-body">
            <div class="info-row">
              <span class="info-label">机构</span>
              <span class="info-value">{{ product.institution }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">利率</span>
              <span class="info-value rate">{{ product.minRate }}% - {{ product.maxRate }}%</span>
            </div>
            <div class="info-row">
              <span class="info-label">额度</span>
              <span class="info-value">{{ product.minAmount }} - {{ product.maxAmount }}万</span>
            </div>
          </div>

          <div class="card-footer">
            <div class="source-tag">
              <span class="source-icon" v-html="getSourceIcon(product.source)"></span>
              {{ getSourceLabel(product.source) }}
            </div>
            <div class="card-time">{{ product.createdAt.slice(5, 16) }}</div>
          </div>
        </div>

        <div v-if="store.filteredProducts.length === 0" class="empty-state">
          <van-empty description="暂无产品数据" />
        </div>
      </div>

      <!-- 新增按钮 -->
      <div class="add-btn" @click="showMethodSheet = true">
        <van-icon name="plus" size="20" />
        <span>录入产品</span>
      </div>

      <!-- 录入方式选择弹框 -->
      <ProductMethodSheet v-model:show="showMethodSheet" />
    </div>
  </MainLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import MainLayout from '../../layouts/MainLayout.vue'
import ProductMethodSheet from '../../components/ProductMethodSheet.vue'
import { useProductStore } from '../../stores/product'

const store = useProductStore()
const showMethodSheet = ref(false)

// 每次进入列表从后端拉取最新数据
onMounted(() => {
  store.loadProducts(true)
})

function getSourceIcon(source) {
  const icons = {
    text: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none"><path d="M14 2H6C4.9 2 4 2.9 4 4V20C4 21.1 4.9 22 6 22H18C19.1 22 20 21.1 20 20V8L14 2Z" fill="#475569"/></svg>',
    voice: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none"><path d="M12 14C13.1 14 14 13.1 14 12V6C14 4.9 13.1 4 12 4C10.9 4 10 4.9 10 6V12C10 13.1 10.9 14 12 14ZM17 12C17 14.8 14.8 17 12 17C9.2 17 7 14.8 7 12H5C5 15.3 7.4 18.1 10.5 18.8V22H13.5V18.8C16.6 18.1 19 15.3 19 12H17Z" fill="#475569"/></svg>',
    image: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none"><path d="M21 19V5C21 3.9 20.1 3 19 3H5C3.9 3 3 3.9 3 5V19C3 20.1 3.9 21 5 21H19C20.1 21 21 20.1 21 19ZM8.5 13.5L11 16.5L14.5 12L19 18H5L8.5 13.5Z" fill="#475569"/></svg>',
    pdf: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none"><path d="M14 2H6C4.9 2 4 2.9 4 4V20C4 21.1 4.9 22 6 22H18C19.1 22 20 21.1 20 20V8L14 2Z" fill="#475569"/></svg>',
  }
  return icons[source] || icons.text
}

function getSourceLabel(source) {
  const labels = { text: '文本录入', voice: '语音录入', image: '图片录入', pdf: 'PDF录入' }
  return labels[source] || '文本录入'
}
</script>

<style scoped>
.product-list-page {
  min-height: 100vh;
  background: var(--bg-base);
  padding-bottom: 80px;
}

.search-bar {
  padding: 0 8px;
  background: transparent;
}

.filter-tabs {
  display: flex;
  gap: 8px;
  padding: 8px 16px 12px;
  overflow-x: auto;
  background: transparent;
  border-bottom: none;
}

.filter-tab {
  flex-shrink: 0;
  padding: 7px 14px;
  border-radius: 16px;
  background: var(--surface-container);
  font-size: 14px;
  color: var(--text-secondary);
  border: none;
  cursor: pointer;
  transition: all 0.2s;
}

.filter-tab.active {
  background: var(--primary-container);
  color: var(--on-primary-container);
  font-weight: 600;
  border: none;
}

.filter-tab .count {
  font-size: 11px;
  opacity: 0.7;
}

.product-list {
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.product-card {
  background: var(--bg-card);
  border: none;
  border-radius: var(--radius-md);
  padding: var(--space-card-pad);
  position: relative;
  overflow: hidden;
  cursor: pointer;
  box-shadow: var(--shadow-card);
  animation: float-up 0.3s ease-out;
  transition: transform 0.15s ease;
}
.product-card:active { transform: scale(0.98); background: var(--bg-card-hover); }

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.product-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.status-badge {
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 8px;
  font-weight: 500;
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

.card-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.info-row {
  display: flex;
  align-items: center;
  font-size: 14px;
}

.info-label {
  width: 40px;
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.info-value {
  color: var(--text-secondary);
}

.info-value.rate {
  color: var(--color-primary);
  font-weight: 600;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
  padding-top: 12px;
  border-top: none;
}

.source-tag {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--text-tertiary);
}

.card-time {
  font-size: 11px;
  color: var(--text-tertiary);
}

/* 新增按钮 */
.add-btn {
  position: fixed;
  bottom: 70px;
  right: 16px;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  background: var(--gradient-primary);
  border-radius: 24px;
  box-shadow: 0 4px 20px rgba(59, 130, 246, 0.3);
  color: #FFFFFF;
  font-size: 14px;
  font-weight: 600;
  z-index: 100;
  cursor: pointer;
  transition: transform 0.2s;
}

.add-btn:active {
  transform: scale(0.95);
}
</style>
