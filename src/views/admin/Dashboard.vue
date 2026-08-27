<template>
  <div class="dashboard">
    <!-- 统计卡 -->
    <div class="stat-grid">
      <div v-for="card in statCards" :key="card.label" class="stat-card" :style="{ '--accent': card.color }">
        <div class="stat-icon">{{ card.icon }}</div>
        <div class="stat-meta">
          <div class="stat-value">{{ card.value }}</div>
          <div class="stat-label">{{ card.label }}</div>
        </div>
        <div v-if="card.sub" class="stat-sub">{{ card.sub }}</div>
      </div>
    </div>

    <div class="chart-row">
      <!-- 近7日新增客户 -->
      <div class="panel">
        <div class="panel-title">近 7 日新增客户</div>
        <div class="bar-chart">
          <div v-for="t in stats.customerTrend" :key="t.date" class="bar-col">
            <div class="bar-value">{{ t.count }}</div>
            <div class="bar-track">
              <div class="bar-fill" :style="{ height: barHeight(t.count) }"></div>
            </div>
            <div class="bar-label">{{ t.date }}</div>
          </div>
        </div>
      </div>

      <!-- 客户来源分布 -->
      <div class="panel">
        <div class="panel-title">客户来源分布</div>
        <div class="donut-wrap">
          <div class="donut" :style="{ background: donutStyle }">
            <div class="donut-hole">
              <div class="donut-total">{{ stats.customerCount }}</div>
              <div class="donut-total-label">客户总数</div>
            </div>
          </div>
          <div class="legend">
            <div v-for="(s, i) in stats.customerSource" :key="s.key" class="legend-item">
              <span class="dot" :style="{ background: donutColors[i % donutColors.length] }"></span>
              <span class="legend-name">{{ s.name }}</span>
              <span class="legend-count">{{ s.count }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 最近录入客户 -->
    <div class="panel">
      <div class="panel-title">最近录入客户</div>
      <table class="data-table">
        <thead>
          <tr>
            <th>客户</th>
            <th>性别/年龄</th>
            <th>城市</th>
            <th>来源</th>
            <th class="num">月收入</th>
            <th class="num">总负债</th>
            <th>录入时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in stats.recentCustomers" :key="c.id">
            <td class="name-cell">{{ c.name }}</td>
            <td>{{ c.gender || '--' }} / {{ c.age || '--' }}</td>
            <td>{{ c.city || '--' }}</td>
            <td><span class="tag">{{ c.source }}</span></td>
            <td class="num">{{ fmtMoney(c.monthlyIncome) }}</td>
            <td class="num">{{ fmtMoney(c.totalDebt) }}</td>
            <td class="time-cell">{{ c.createdAt }}</td>
          </tr>
          <tr v-if="!stats.recentCustomers?.length">
            <td colspan="7" class="empty-cell">暂无客户数据</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { fetchAdminStats } from '../../api/admin'

const stats = ref({})

const statCards = computed(() => [
  { icon: '👥', label: '客户总数', value: stats.value.customerCount ?? '-', sub: `今日 +${stats.value.customerTodayCount ?? 0}`, color: '#2E6BFF' },
  { icon: '📦', label: '产品总数', value: stats.value.productCount ?? '-', sub: `启用 ${stats.value.productActiveCount ?? 0}`, color: '#00A884' },
  { icon: '📅', label: '日程总数', value: stats.value.scheduleCount ?? '-', sub: `今日 ${stats.value.scheduleTodayCount ?? 0}`, color: '#8B5CF6' },
  { icon: '🤖', label: 'AI 匹配次数', value: stats.value.simulationCount ?? '-', sub: `材料 ${stats.value.materialCount ?? 0} 份`, color: '#F59E0B' },
  { icon: '🔑', label: '注册用户', value: stats.value.userCount ?? '-', sub: `风险客户 ${stats.value.riskCount ?? 0}`, color: '#EF5350' },
])

const donutColors = ['#2E6BFF', '#00C2A8', '#8B5CF6', '#F59E0B', '#EF5350', '#94A3B8']

const donutStyle = computed(() => {
  const list = stats.value.customerSource || []
  const total = list.reduce((s, x) => s + x.count, 0)
  if (!total) return 'conic-gradient(#E5E9F2 0deg 360deg)'
  let acc = 0
  const parts = []
  list.forEach((s, i) => {
    const start = (acc / total) * 360
    acc += s.count
    const end = (acc / total) * 360
    parts.push(`${donutColors[i % donutColors.length]} ${start}deg ${end}deg`)
  })
  return `conic-gradient(${parts.join(', ')})`
})

function barHeight(count) {
  const list = stats.value.customerTrend || []
  const max = Math.max(1, ...list.map((x) => x.count))
  return `${Math.max(6, (count / max) * 100)}%`
}

function fmtMoney(v) {
  if (!v) return '0'
  return v >= 10000 ? (v / 10000).toFixed(1) + '万' : Number(v).toLocaleString() + '元'
}

onMounted(async () => {
  try {
    stats.value = await fetchAdminStats()
  } catch (e) { /* 拦截器已提示 */ }
})
</script>

<style scoped>
.stat-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  position: relative;
  background: #fff;
  border-radius: 14px;
  padding: 18px;
  display: flex;
  align-items: center;
  gap: 14px;
  box-shadow: 0 2px 10px rgba(23, 35, 61, 0.05);
  overflow: hidden;
}

.stat-card::after {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: var(--accent);
}

.stat-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: color-mix(in srgb, var(--accent) 12%, #fff);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #17233D;
  line-height: 1.1;
}

.stat-label {
  font-size: 12px;
  color: #7C8DB5;
  margin-top: 4px;
}

.stat-sub {
  position: absolute;
  right: 14px;
  top: 14px;
  font-size: 11px;
  color: var(--accent);
  background: color-mix(in srgb, var(--accent) 10%, #fff);
  padding: 3px 8px;
  border-radius: 999px;
}

.chart-row {
  display: grid;
  grid-template-columns: 3fr 2fr;
  gap: 16px;
  margin-bottom: 20px;
}

.panel {
  background: #fff;
  border-radius: 14px;
  padding: 20px;
  box-shadow: 0 2px 10px rgba(23, 35, 61, 0.05);
}

.panel-title {
  font-size: 15px;
  font-weight: 600;
  color: #17233D;
  margin-bottom: 18px;
}

/* 柱状图 */
.bar-chart {
  display: flex;
  align-items: flex-end;
  gap: 14px;
  height: 170px;
}

.bar-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  height: 100%;
}

.bar-value {
  font-size: 12px;
  font-weight: 600;
  color: #2E6BFF;
}

.bar-track {
  flex: 1;
  width: 100%;
  max-width: 38px;
  background: #F0F3FA;
  border-radius: 8px;
  display: flex;
  align-items: flex-end;
  overflow: hidden;
}

.bar-fill {
  width: 100%;
  background: linear-gradient(180deg, #2E6BFF, #6C9BFF);
  border-radius: 8px 8px 0 0;
  transition: height 0.5s ease;
}

.bar-label {
  font-size: 11px;
  color: #7C8DB5;
}

/* 环形图 */
.donut-wrap {
  display: flex;
  align-items: center;
  gap: 24px;
}

.donut {
  width: 150px;
  height: 150px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.donut-hole {
  width: 96px;
  height: 96px;
  border-radius: 50%;
  background: #fff;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.donut-total {
  font-size: 22px;
  font-weight: 700;
  color: #17233D;
}

.donut-total-label {
  font-size: 11px;
  color: #7C8DB5;
}

.legend {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #3D4A6B;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 3px;
}

.legend-count {
  margin-left: auto;
  font-weight: 600;
  color: #17233D;
  padding-left: 18px;
}

/* 表格 */
.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.data-table th {
  text-align: left;
  padding: 10px 12px;
  color: #7C8DB5;
  font-weight: 500;
  border-bottom: 1px solid #EDF0F7;
  white-space: nowrap;
}

.data-table td {
  padding: 12px;
  border-bottom: 1px solid #F4F6FB;
  color: #3D4A6B;
}

.data-table tr:last-child td {
  border-bottom: none;
}

.data-table .num {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.name-cell {
  font-weight: 600;
  color: #17233D;
}

.time-cell {
  color: #98A5C3;
  font-size: 12px;
  white-space: nowrap;
}

.tag {
  background: #EBF1FF;
  color: #2E6BFF;
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 999px;
  white-space: nowrap;
}

.empty-cell {
  text-align: center;
  color: #98A5C3;
  padding: 30px !important;
}
</style>
