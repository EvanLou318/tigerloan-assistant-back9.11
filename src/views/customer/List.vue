<template>
  <MainLayout>
    <div class="customer-list-page">
      <van-nav-bar title="客户管理" :border="false" />

      <div class="search-bar">
        <van-search
          v-model="store.searchKeyword"
          placeholder="搜索客户姓名或手机号"
          shape="round"
          clearable
        >
          <template #right-icon>
            <VoiceMic label="搜索客户" sample="王建国" @confirm="store.searchKeyword = $event" />
          </template>
        </van-search>
      </div>

      <!-- 客户列表 -->
      <van-pull-refresh v-model="refreshing" @refresh="onRefresh" success-text="已更新">
        <SkeletonList v-if="store.loading && !refreshing" :count="3" />
        <div v-else class="customer-list">
          <div
            v-for="customer in store.filteredCustomers"
            :key="customer.id"
            class="customer-card"
            @click="$router.push(`/customers/${customer.id}`)"
          >
          <div class="card-top">
            <div class="customer-avatar" :class="customer.gender">
              {{ customer.name.charAt(0) }}
            </div>
            <div class="customer-info">
              <div class="info-header">
                <span class="customer-name">{{ customer.name }}</span>
                <span class="customer-age">{{ customer.age }}岁 · {{ customer.gender }}</span>
              </div>
              <div class="customer-phone">{{ customer.phone }}</div>
            </div>
            <div class="match-status" :class="getMatchStatus(customer)">
              {{ getMatchStatusText(customer) }}
            </div>
          </div>

          <div class="card-metrics">
            <div class="metric-item">
              <span class="metric-label">月收入</span>
              <span class="metric-value">{{ formatAmount(customer.monthlyIncome) }}</span>
            </div>
            <div class="metric-divider"></div>
            <div class="metric-item">
              <span class="metric-label">负债</span>
              <span class="metric-value" :class="{ warning: customer.totalDebt > 100000 }">
                {{ formatAmount(customer.totalDebt) }}
              </span>
            </div>
            <div class="metric-divider"></div>
            <div class="metric-item">
              <span class="metric-label">征信查询</span>
              <span class="metric-value" :class="{ warning: customer.queryCount3m > 6 }">
                {{ customer.queryCount3m }}次/3月
              </span>
            </div>
          </div>

          <div class="card-footer">
            <div class="footer-tags">
              <div class="materials-tag">
                <AppIcon name="file-text" :size="12" />
                <span>{{ customer.materials.length }}份资料</span>
              </div>
              <div v-if="upcomingSchedules(customer.id).length > 0" class="schedule-tag" @click.stop="goSchedules">
                <AppIcon name="clock" :size="12" />
                <span>{{ upcomingSchedules(customer.id).length }}项日程</span>
                <span class="schedule-next">最近 {{ formatSchTime(upcomingSchedules(customer.id)[0].startTime) }}</span>
              </div>
            </div>
            <div class="card-time">{{ customer.updatedAt.slice(5, 16) }}</div>
          </div>
        </div>

        <div v-if="store.filteredCustomers.length === 0" class="empty-state">
          <van-empty description="暂无客户数据" />
        </div>
        </div>
      </van-pull-refresh>

      <!-- 新增按钮 -->
      <div class="add-btn" @click="$router.push('/customers/create')">
        <AppIcon name="plus" :size="20" />
        <span>新建客户</span>
      </div>
    </div>
  </MainLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import MainLayout from '../../layouts/MainLayout.vue'
import SkeletonList from '../../components/SkeletonList.vue'
import VoiceMic from '../../components/VoiceMic.vue'
import { useCustomerStore } from '../../stores/customer'
import { useScheduleStore } from '../../stores/schedule'

const router = useRouter()
const store = useCustomerStore()
const scheduleStore = useScheduleStore()
const refreshing = ref(false)

onMounted(() => {
  store.loadCustomers(true)
  scheduleStore.loadSchedules()
})

async function onRefresh() {
  try {
    await Promise.all([store.loadCustomers(true), scheduleStore.loadSchedules(true)])
  } finally {
    refreshing.value = false
  }
}

// 某客户的未来未完成日程（按开始时间升序）
function upcomingSchedules(customerId) {
  const now = new Date()
  return scheduleStore.schedules
    .filter((s) => s.customerId === customerId && !s.done && new Date(s.startTime) >= now)
    .sort((a, b) => new Date(a.startTime) - new Date(b.startTime))
}

function formatSchTime(iso) {
  const d = new Date(iso)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getMonth() + 1}/${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function goSchedules() {
  router.push('/schedules')
}

function formatAmount(val) {
  if (val >= 10000) {
    return (val / 10000).toFixed(1) + '万'
  }
  return val + '元'
}

function getMatchStatus(customer) {
  if (customer.queryCount3m > 8 || customer.totalDebt > 100000 || customer.maxOverdueMonths > 0) {
    return 'risky'
  }
  return 'good'
}

function getMatchStatusText(customer) {
  const status = getMatchStatus(customer)
  if (status === 'risky') return '风险'
  return '优质'
}
</script>

<style scoped>
.customer-list-page {
  min-height: 100vh;
  background: var(--bg-base);
  padding-bottom: 80px;
}

.search-bar {
  padding: 0 8px;
  background: transparent;
}

.customer-list {
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.customer-card {
  background: var(--bg-card);
  border: none;
  border-radius: var(--radius-md);
  padding: var(--space-card-pad);
  cursor: pointer;
  position: relative;
  overflow: hidden;
  box-shadow: var(--shadow-card);
  animation: float-up 0.3s ease-out;
  transition: transform 0.15s ease;
}
.customer-card:active { transform: scale(0.98); background: var(--bg-card-hover); }

.card-top {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.customer-avatar {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 600;
  flex-shrink: 0;
}

.customer-avatar.男 {
  background: var(--primary-container);
  color: var(--on-primary-container);
  border: none;
}

.customer-avatar.女 {
  background: var(--danger-container);
  color: var(--on-danger-container);
  border: none;
}

.customer-info {
  flex: 1;
  min-width: 0;
}

.info-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.customer-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.customer-age {
  font-size: 12px;
  color: var(--text-tertiary);
}

.customer-phone {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 2px;
  font-family: 'DIN', sans-serif;
}

.match-status {
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 8px;
  flex-shrink: 0;
  border: none;
}

.match-status.good {
  background: var(--success-container);
  color: var(--on-success-container);
}

.match-status.risky {
  background: var(--warning-container);
  color: var(--on-warning-container);
}

.card-metrics {
  display: flex;
  align-items: center;
  padding: 10px 0;
  margin-top: 10px;
  background: var(--surface-container-low);
  border-radius: var(--radius-sm);
  border-top: none;
  border-bottom: none;
}

.metric-item {
  flex: 1;
  text-align: center;
  border-right: none;
}
.metric-item:last-child { border-right: none; }

.metric-label {
  display: block;
  font-size: 11px;
  color: var(--text-tertiary);
  margin-bottom: 2px;
}

.metric-value {
  font-size: 14px;
  color: var(--text-primary);
  font-weight: 600;
  font-family: 'DIN', sans-serif;
}

.metric-value.warning {
  color: var(--color-warning);
}

.metric-divider {
  width: 1px;
  height: 24px;
  background: var(--surface-container-high);
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
}

.materials-tag {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--text-tertiary);
}

.footer-tags {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.schedule-tag {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--on-primary-container);
  background: var(--primary-container);
  border-radius: 8px;
  padding: 2px 8px;
  border: none;
}

.schedule-next {
  color: var(--text-tertiary);
}

.card-time {
  font-size: 11px;
  color: var(--text-tertiary);
}

.add-btn {
  position: fixed;
  bottom: calc(80px + env(safe-area-inset-bottom));
  right: 16px;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  background: var(--gradient-primary);
  border-radius: 24px;
  box-shadow: 0 4px 20px rgba(37, 99, 235, 0.3);
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
