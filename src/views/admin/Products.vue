<template>
  <div class="page">
    <div class="toolbar">
      <input v-model="keyword" class="search-input" placeholder="搜索产品名称 / 机构" />
      <div class="filter-tabs">
        <button
          v-for="t in ['all', 'active', 'disabled']"
          :key="t"
          class="filter-tab"
          :class="{ active: filter === t }"
          @click="filter = t"
        >
          {{ { all: '全部', active: '已启用', disabled: '已禁用' }[t] }}
        </button>
      </div>
      <span class="count-badge">共 {{ filtered.length }} 款产品</span>
    </div>

    <div class="panel">
      <table class="data-table">
        <thead>
          <tr>
            <th>产品名称</th>
            <th>机构</th>
            <th class="num">年利率</th>
            <th class="num">最高额度</th>
            <th>期限</th>
            <th>还款方式</th>
            <th>录入方式</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in filtered" :key="p.id">
            <td class="name-cell">{{ p.productName }}</td>
            <td>{{ p.institution || '--' }}</td>
            <td class="num rate">{{ p.minRate }}-{{ p.maxRate }}%</td>
            <td class="num">{{ fmtAmount(p.maxAmount) }}</td>
            <td>{{ p.loanTerm || '--' }}</td>
            <td>{{ p.repaymentMethod || '--' }}</td>
            <td><span class="tag">{{ sourceLabel(p.source) }}</span></td>
            <td>
              <span class="status" :class="p.status === 'active' ? 'on' : 'off'">
                {{ p.status === 'active' ? '启用中' : '已禁用' }}
              </span>
            </td>
            <td class="op-cell">
              <button class="link-btn" @click="toggle(p)">{{ p.status === 'active' ? '禁用' : '启用' }}</button>
              <button class="link-btn danger" @click="remove(p)">删除</button>
            </td>
          </tr>
          <tr v-if="!filtered.length">
            <td colspan="9" class="empty-cell">暂无匹配产品</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { showConfirmDialog, showSuccessToast, showToast } from 'vant'
import { fetchProducts, toggleProductStatus, deleteProduct as deleteProductApi } from '../../api/products'

const products = ref([])
const keyword = ref('')
const filter = ref('all')

const filtered = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  return products.value.filter((p) => {
    if (filter.value !== 'all' && p.status !== filter.value) return false
    if (!kw) return true
    return (
      p.productName.toLowerCase().includes(kw) ||
      (p.institution || '').toLowerCase().includes(kw)
    )
  })
})

const sourceLabels = { text: '文本', voice: '语音', image: '图片', pdf: 'PDF' }
const sourceLabel = (s) => sourceLabels[s] || s || '文本'

function fmtAmount(v) {
  if (!v) return '--'
  return v >= 10000 ? (v / 10000).toFixed(0) + '万' : Number(v).toLocaleString() + '元'
}

async function toggle(p) {
  const next = p.status === 'active' ? 'disabled' : 'active'
  try {
    await toggleProductStatus(p.id, next)
    p.status = next
    showSuccessToast(next === 'active' ? '已启用' : '已禁用')
  } catch (e) {
    showToast(e.message || '操作失败')
  }
}

async function remove(p) {
  try {
    await showConfirmDialog({
      title: '删除产品',
      message: `确定删除「${p.productName}」吗？删除后不在匹配列表中展示。`,
    })
  } catch {
    return
  }
  try {
    await deleteProductApi(p.id)
    products.value = products.value.filter((x) => x.id !== p.id)
    showSuccessToast('已删除')
  } catch (e) {
    showToast(e.message || '删除失败')
  }
}

onMounted(async () => {
  try {
    products.value = await fetchProducts()
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
}

.search-input:focus {
  border-color: #2E6BFF;
}

.filter-tabs {
  display: flex;
  background: #EBEEF6;
  border-radius: 10px;
  padding: 3px;
}

.filter-tab {
  border: none;
  background: transparent;
  padding: 7px 16px;
  font-size: 13px;
  color: #5A6A8F;
  border-radius: 8px;
  cursor: pointer;
}

.filter-tab.active {
  background: #fff;
  color: #17233D;
  font-weight: 600;
  box-shadow: 0 1px 4px rgba(23, 35, 61, 0.12);
}

.count-badge {
  font-size: 12px;
  color: #7C8DB5;
  margin-left: auto;
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

.num {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.rate {
  color: #2E6BFF;
  font-weight: 600;
}

.name-cell {
  font-weight: 600;
  color: #17233D;
  white-space: nowrap;
}

.tag {
  background: #F0EDFF;
  color: #7C5CFC;
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 999px;
  white-space: nowrap;
}

.status {
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 999px;
  white-space: nowrap;
}

.status.on {
  background: #E6F7F1;
  color: #00A884;
}

.status.off {
  background: #F0F3FA;
  color: #98A5C3;
}

.op-cell {
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
</style>
