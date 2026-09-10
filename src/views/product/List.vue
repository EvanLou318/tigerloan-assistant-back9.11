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
        >
          <template #right-icon>
            <VoiceMic label="搜索产品" sample="公积金贷" @confirm="store.searchKeyword = $event" />
          </template>
        </van-search>
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
      <van-pull-refresh v-model="refreshing" @refresh="onRefresh" success-text="已更新">
        <SkeletonList v-if="store.loading && !refreshing" :count="3" />
        <div v-else class="product-list">
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
                <span class="info-label">{{ product.rateType === 'monthly' ? '月利率' : '年利率' }}</span>
                <span class="info-value rate">{{ product.minRate }}% - {{ product.maxRate }}%</span>
              </div>
              <div class="info-row">
                <span class="info-label">额度</span>
                <span class="info-value">{{ product.minAmount }} - {{ product.maxAmount }}万</span>
              </div>
            </div>

            <div class="card-footer">
              <div class="card-time">{{ product.createdAt.slice(5, 16) }}</div>
            </div>
          </div>

          <div v-if="store.filteredProducts.length === 0" class="empty-state">
            <van-empty description="暂无产品数据" />
          </div>
        </div>
      </van-pull-refresh>

      <!-- 新增按钮 -->
      <div class="add-btn" @click="showMethodSheet = true">
        <AppIcon name="plus" :size="20" />
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
import SkeletonList from '../../components/SkeletonList.vue'
import VoiceMic from '../../components/VoiceMic.vue'
import { useProductStore } from '../../stores/product'

const store = useProductStore()
const showMethodSheet = ref(false)
const refreshing = ref(false)

// 每次进入列表从后端拉取最新数据
onMounted(() => {
  store.loadProducts(true)
})

async function onRefresh() {
  try {
    await store.loadProducts(true)
  } finally {
    refreshing.value = false
  }
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
  background: var(--d-product-50);
  color: var(--d-product-800);
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
  background: var(--surface-container-high);
  color: var(--text-secondary);
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
  background: var(--d-product-50);
  color: var(--d-product-800);
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 6px;
}

.card-footer {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin-top: 12px;
  padding-top: 12px;
  border-top: none;
}

.card-time {
  font-size: 11px;
  color: var(--text-tertiary);
}

/* 新增按钮 */
.add-btn {
  position: fixed;
  bottom: calc(80px + env(safe-area-inset-bottom));
  right: 16px;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  background: var(--d-product-600);
  border-radius: 24px;
  box-shadow: 0 4px 20px rgba(127, 119, 221, 0.3);
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
