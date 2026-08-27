<template>
  <div class="page">
    <div class="toolbar">
      <input v-model="keyword" class="search-input" placeholder="搜索客户姓名 / 手机号" />
      <span class="count-badge">共 {{ filtered.length }} 位客户</span>
    </div>

    <div class="panel">
      <table class="data-table">
        <thead>
          <tr>
            <th>客户</th>
            <th>手机号</th>
            <th>城市</th>
            <th>来源</th>
            <th class="num">月收入</th>
            <th class="num">总负债</th>
            <th class="num">逾期(月)</th>
            <th class="num">材料</th>
            <th>风险</th>
            <th>录入时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in filtered" :key="c.id">
            <td class="name-cell">
              <span class="avatar" :class="c.gender === '女' ? 'f' : ''">{{ c.name[0] }}</span>
              {{ c.name }}
              <span class="sub">{{ c.age ? c.age + '岁' : '' }}</span>
            </td>
            <td class="mono">{{ c.phone }}</td>
            <td>{{ c.city || '--' }}</td>
            <td><span class="tag">{{ sourceName(c.source) }}</span></td>
            <td class="num">{{ fmtMoney(c.monthlyIncome) }}</td>
            <td class="num">{{ fmtMoney(c.totalDebt) }}</td>
            <td class="num" :class="{ danger: c.maxOverdueMonths > 0 }">{{ c.maxOverdueMonths }}</td>
            <td class="num">{{ c.materials?.length || 0 }}</td>
            <td>
              <span class="risk" :class="isRisky(c) ? 'bad' : 'good'">{{ isRisky(c) ? '风险' : '优质' }}</span>
            </td>
            <td class="time-cell">{{ (c.createdAt || '').slice(0, 10) }}</td>
            <td>
              <button class="link-btn" @click="viewDetail(c)">详情</button>
              <button class="link-btn danger" @click="removeCustomer(c)">删除</button>
            </td>
          </tr>
          <tr v-if="!filtered.length">
            <td colspan="11" class="empty-cell">暂无匹配客户</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 详情抽屉 -->
    <teleport to="body">
      <div v-if="active" class="drawer-mask" @click="active = null"></div>
      <div v-if="active" class="drawer">
        <div class="drawer-head">
          <div>
            <div class="drawer-name">{{ active.name }}</div>
            <div class="drawer-sub">{{ active.gender }} · {{ active.age }}岁 · {{ sourceName(active.source) }} · {{ active.city }}</div>
          </div>
          <button class="close-btn" @click="active = null">✕</button>
        </div>
        <div class="drawer-body">
          <div class="info-grid">
            <div class="info-item"><label>手机号</label><b>{{ active.phone }}</b></div>
            <div class="info-item"><label>身份证</label><b>{{ active.idCard || '--' }}</b></div>
            <div class="info-item"><label>婚姻/学历</label><b>{{ active.maritalStatus || '--' }} / {{ active.education || '--' }}</b></div>
            <div class="info-item"><label>工作单位</label><b>{{ active.employer || '--' }}</b></div>
            <div class="info-item"><label>月收入</label><b>{{ fmtMoney(active.monthlyIncome) }}</b></div>
            <div class="info-item"><label>公积金基数</label><b>{{ fmtMoney(active.housingFundBase) }}</b></div>
            <div class="info-item"><label>总负债</label><b>{{ fmtMoney(active.totalDebt) }}</b></div>
            <div class="info-item"><label>房产/车辆</label><b>{{ active.propertyValue || 0 }}万 / {{ active.carValue || 0 }}万</b></div>
            <div class="info-item"><label>近3月查询</label><b>{{ active.queryCount3m }}次</b></div>
            <div class="info-item"><label>期望额度/利率</label><b>{{ active.expectedAmount || 0 }}万 / {{ active.expectedRate || 0 }}%</b></div>
          </div>

          <div class="section-label">已录入材料（{{ active.materials?.length || 0 }}）</div>
          <div class="mat-list">
            <div v-for="m in active.materials" :key="m.id" class="mat-item">
              <span class="mat-name">{{ m.type }}</span>
              <span class="mat-conf">置信度 {{ Math.round((m.confidence || 0.9) * 100) }}%</span>
              <span class="mat-time">{{ (m.time || '').slice(5, 16) }}</span>
            </div>
            <div v-if="!active.materials?.length" class="mat-empty">暂无材料</div>
          </div>
        </div>
      </div>
    </teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { showConfirmDialog, showSuccessToast, showToast } from 'vant'
import { fetchCustomers, deleteCustomer as deleteCustomerApi } from '../../api/customers'

const customers = ref([])
const keyword = ref('')
const active = ref(null)

const filtered = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  if (!kw) return customers.value
  return customers.value.filter(
    (c) => c.name.toLowerCase().includes(kw) || (c.phone || '').includes(kw)
  )
})

const sourceNames = {
  friend: '朋友介绍',
  telemarketing: '电话营销',
  walkin: '门店进件',
  online: '线上渠道',
  referral: '老客转介绍',
  other: '其他',
}
const sourceName = (s) => sourceNames[s] || s || '--'

function isRisky(c) {
  return c.maxOverdueMonths > 0 || c.totalDebt > 100000 || c.queryCount3m > 8
}

function fmtMoney(v) {
  if (!v) return '0'
  return v >= 10000 ? (v / 10000).toFixed(1) + '万' : Number(v).toLocaleString() + '元'
}

function viewDetail(c) {
  active.value = c
}

async function removeCustomer(c) {
  try {
    await showConfirmDialog({
      title: '删除客户',
      message: `确定删除「${c.name}」的档案吗？其材料与关联日程将一并失效。`,
    })
  } catch {
    return
  }
  try {
    await deleteCustomerApi(c.id)
    customers.value = customers.value.filter((x) => x.id !== c.id)
    showSuccessToast('已删除')
  } catch (e) {
    showToast(e.message || '删除失败')
  }
}

onMounted(async () => {
  try {
    customers.value = await fetchCustomers()
  } catch (e) { /* 拦截器已提示 */ }
})
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 14px;
}

.search-input {
  width: 280px;
  padding: 9px 14px;
  border: 1px solid #E0E5F0;
  border-radius: 10px;
  font-size: 13px;
  outline: none;
  background: #fff;
  transition: border 0.15s;
}

.search-input:focus {
  border-color: #2E6BFF;
}

.count-badge {
  font-size: 12px;
  color: #7C8DB5;
}

.panel {
  background: #fff;
  border-radius: 14px;
  padding: 8px 16px 16px;
  box-shadow: 0 2px 10px rgba(23, 35, 61, 0.05);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.data-table th {
  text-align: left;
  padding: 12px;
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

.data-table .num {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.name-cell {
  font-weight: 600;
  color: #17233D;
  white-space: nowrap;
}

.sub {
  font-weight: 400;
  color: #98A5C3;
  font-size: 12px;
  margin-left: 4px;
}

.mono {
  font-variant-numeric: tabular-nums;
}

.avatar {
  display: inline-flex;
  width: 26px;
  height: 26px;
  border-radius: 8px;
  background: #EBF1FF;
  color: #2E6BFF;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  margin-right: 6px;
  vertical-align: middle;
}

.avatar.f {
  background: #FDEBEE;
  color: #EF5350;
}

.tag {
  background: #EBF1FF;
  color: #2E6BFF;
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 999px;
  white-space: nowrap;
}

.risk {
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 999px;
  white-space: nowrap;
}

.risk.good {
  background: #E6F7F1;
  color: #00A884;
}

.risk.bad {
  background: #FDEBEE;
  color: #EF5350;
}

.danger {
  color: #EF5350 !important;
  font-weight: 600;
}

.time-cell {
  color: #98A5C3;
  font-size: 12px;
  white-space: nowrap;
}

.link-btn {
  border: none;
  background: none;
  color: #2E6BFF;
  font-size: 13px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
}

.link-btn:hover {
  background: #EBF1FF;
}

.link-btn.danger {
  color: #EF5350;
}

.link-btn.danger:hover {
  background: #FDEBEE;
}

.empty-cell {
  text-align: center;
  color: #98A5C3;
  padding: 30px !important;
}

/* 抽屉 */
.drawer-mask {
  position: fixed;
  inset: 0;
  background: rgba(13, 27, 62, 0.4);
  z-index: 100;
}

.drawer {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  width: 460px;
  background: #fff;
  z-index: 101;
  box-shadow: -8px 0 30px rgba(13, 27, 62, 0.15);
  display: flex;
  flex-direction: column;
}

.drawer-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid #EDF0F7;
}

.drawer-name {
  font-size: 18px;
  font-weight: 700;
  color: #17233D;
}

.drawer-sub {
  font-size: 12px;
  color: #7C8DB5;
  margin-top: 4px;
}

.close-btn {
  border: none;
  background: #F0F3FA;
  width: 30px;
  height: 30px;
  border-radius: 8px;
  cursor: pointer;
  color: #7C8DB5;
}

.close-btn:hover {
  background: #E5E9F2;
}

.drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px 18px;
  margin-bottom: 24px;
}

.info-item label {
  display: block;
  font-size: 11px;
  color: #98A5C3;
  margin-bottom: 4px;
}

.info-item b {
  font-size: 13px;
  color: #17233D;
  font-weight: 600;
  word-break: break-all;
}

.section-label {
  font-size: 13px;
  font-weight: 600;
  color: #17233D;
  margin-bottom: 10px;
}

.mat-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: #F7F9FD;
  border-radius: 10px;
  margin-bottom: 8px;
  font-size: 12px;
}

.mat-name {
  font-weight: 600;
  color: #17233D;
}

.mat-conf {
  color: #00A884;
}

.mat-time {
  margin-left: auto;
  color: #98A5C3;
}

.mat-empty {
  font-size: 12px;
  color: #98A5C3;
  text-align: center;
  padding: 16px;
  background: #F7F9FD;
  border-radius: 10px;
}
</style>
