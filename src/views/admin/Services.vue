<template>
  <div class="services-page">
    <div class="page-header">
      <div>
        <h2>三方服务</h2>
        <p class="sub">大模型 / OCR / ASR 供应商配置。配置并启用后该分类自动切换为真实调用，换服务商无需改代码</p>
      </div>
    </div>

    <div v-if="loadError" class="error-banner">
      ⚠️ {{ loadError }}
      <button class="retry-btn" @click="load">重试</button>
    </div>

    <div v-if="loading" class="loading">加载中...</div>

    <div v-for="g in groups" :key="g.category" class="cat-card">
      <div class="cat-head">
        <div class="cat-info">
          <div class="cat-name">{{ g.name }}</div>
          <div class="cat-desc">{{ g.desc }}</div>
        </div>
        <div class="cat-right">
          <span class="mode-badge" :class="g.mode">
            {{ g.mode === 'real' ? '真实调用' : '模拟模式' }}
          </span>
          <span v-if="g.activeProvider" class="active-name">
            当前生效：{{ g.activeProvider.name }}
          </span>
          <span v-else class="active-name muted">未配置，走内置模拟</span>
          <button v-if="canManage" class="add-btn" @click="openCreate(g)">+ 添加供应商</button>
        </div>
      </div>

      <table v-if="g.providers.length" class="table">
        <thead>
          <tr>
            <th>名称</th>
            <th>类型</th>
            <th>Base URL</th>
            <th v-if="g.needsModel">模型</th>
            <th>API Key</th>
            <th>状态</th>
            <th style="width: 260px">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in g.providers" :key="p.id" :class="{ disabled: !p.enabled }">
            <td>
              <span v-if="p.isDefault" class="default-star" title="默认供应商">★</span>
              {{ p.name }}
            </td>
            <td><code class="ptype">{{ p.providerType }}</code></td>
            <td class="mono url-cell">{{ p.baseUrl || '—' }}</td>
            <td v-if="g.needsModel" class="mono">{{ p.model || '—' }}</td>
            <td class="mono">{{ p.apiKeyMasked || '未配置' }}</td>
            <td>
              <span class="status" :class="p.enabled ? 'on' : 'off'">{{ p.enabled ? '启用' : '停用' }}</span>
            </td>
            <td>
              <button class="link-btn" @click="runTest(p)">{{ testing === p.id ? '测试中...' : '测试' }}</button>
              <button v-if="canManage" class="link-btn" @click="openEdit(p, g)">编辑</button>
              <button v-if="canManage && !p.isDefault" class="link-btn" @click="makeDefault(p)">设为默认</button>
              <button v-if="canManage" class="link-btn" @click="toggleEnabled(p)">{{ p.enabled ? '停用' : '启用' }}</button>
              <button v-if="canManage" class="link-btn danger" @click="remove(p)">删除</button>
              <div v-if="testResults[p.id]" class="test-result-inline" :class="testResults[p.id].pass ? 'pass' : 'fail'">
                {{ testResults[p.id].message }}
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty">暂无供应商，点击「添加供应商」接入真实服务</div>
    </div>

    <!-- 新增 / 编辑弹窗 -->
    <div v-if="showForm" class="modal-mask" @click.self="showForm = false">
      <div class="modal">
        <h3>{{ form.id ? '编辑供应商' : `添加${formCategoryName}供应商` }}</h3>

        <div class="form-item">
          <label>名称 <i>*</i></label>
          <input v-model="form.name" placeholder="如：通义千问 / 腾讯云 OCR" />
        </div>

        <div class="form-item">
          <label>服务类型</label>
          <div class="type-picker">
            <button
              v-for="t in formTypes"
              :key="t"
              class="type-opt"
              :class="{ active: form.providerType === t }"
              @click="form.providerType = t"
            >
              {{ typeLabel(t) }}
            </button>
          </div>
        </div>

        <div class="form-item">
          <label>Base URL</label>
          <input v-model="form.baseUrl" :placeholder="form.category === 'llm' ? 'https://api.openai.com/v1' : 'https://ocr.example.com'" />
          <p class="hint" v-if="form.category === 'llm'">OpenAI 兼容协议，末尾无需 /chat/completions</p>
        </div>

        <div class="form-item">
          <label>API Key <i v-if="!form.id">*</i></label>
          <input v-model="form.apiKey" type="password" :placeholder="form.id ? '留空则保持不变' : '服务商控制台获取'" />
        </div>

        <div class="form-item" v-if="form.category !== 'llm'">
          <label>Secret Key</label>
          <input v-model="form.secretKey" type="password" placeholder="部分厂商需要（腾讯云等），留空保持不变" />
        </div>

        <div class="form-item" v-if="form.category === 'llm'">
          <label>模型</label>
          <input v-model="form.model" placeholder="如 gpt-4o-mini / qwen-plus / deepseek-chat" />
        </div>

        <div class="form-item">
          <label>备注</label>
          <input v-model="form.remark" placeholder="内部备注，如采购人 / 到期时间" />
        </div>

        <div class="form-item">
          <label class="checkbox">
            <input type="checkbox" v-model="form.enabled" /> 启用
          </label>
          <label class="checkbox">
            <input type="checkbox" v-model="form.isDefault" /> 设为该分类默认（调用时生效）
          </label>
        </div>

        <div class="modal-actions">
          <button class="btn ghost" @click="showForm = false">取消</button>
          <button class="btn primary" :disabled="saving" @click="save">{{ saving ? '保存中...' : '保存' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { showConfirmDialog, showSuccessToast, showToast } from 'vant'
import {
  fetchServiceGroups,
  createServiceProvider,
  updateServiceProvider,
  setServiceDefault,
  deleteServiceProvider,
  testServiceProvider,
} from '../../api/admin'

const userInfo = JSON.parse(localStorage.getItem('userInfo') || 'null')
const canManage = computed(() => {
  const perms = userInfo?.permissions
  if (!perms) return true
  return perms.includes('admin.services.manage')
})

const groups = ref([])
const loading = ref(false)
const loadError = ref('')
const testing = ref(0)
const testResults = ref({})

const showForm = ref(false)
const saving = ref(false)
const form = ref({})
const formTypes = ref([])
const formCategoryName = ref('')

const TYPE_LABELS = {
  'openai-compatible': 'OpenAI 兼容',
  anthropic: 'Anthropic',
  tencent: '腾讯云',
  aliyun: '阿里云',
  xfyun: '讯飞',
  baidu: '百度',
  custom: '自定义',
}
const typeLabel = (t) => TYPE_LABELS[t] || t

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    groups.value = await fetchServiceGroups()
  } catch (e) {
    loadError.value = `服务配置加载失败：${e.message || '请确认后端服务已启动'}`
  } finally {
    loading.value = false
  }
}

function openCreate(g) {
  form.value = {
    id: 0,
    category: g.category,
    name: '',
    providerType: g.providerTypes?.[0] || 'custom',
    baseUrl: '',
    apiKey: '',
    secretKey: '',
    model: '',
    remark: '',
    enabled: true,
    isDefault: false,
  }
  formTypes.value = g.providerTypes || ['custom']
  formCategoryName.value = g.name
  showForm.value = true
}

function openEdit(p, g) {
  form.value = {
    id: p.id,
    category: p.category,
    name: p.name,
    providerType: p.providerType,
    baseUrl: p.baseUrl,
    apiKey: '',
    secretKey: '',
    model: p.model,
    remark: p.remark,
    enabled: p.enabled,
    isDefault: p.isDefault,
  }
  formTypes.value = g.providerTypes || ['custom']
  formCategoryName.value = g.name
  showForm.value = true
}

async function save() {
  const f = form.value
  if (!f.name?.trim()) return showToast('请填写名称')
  if (!f.id && !f.apiKey) return showToast('新增供应商必须填写 API Key')

  saving.value = true
  try {
    if (f.id) {
      const payload = { ...f }
      if (!payload.apiKey) delete payload.apiKey
      if (!payload.secretKey) delete payload.secretKey
      delete payload.id
      delete payload.category
      await updateServiceProvider(f.id, payload)
    } else {
      await createServiceProvider(f)
    }
    showSuccessToast('已保存')
    showForm.value = false
    await load()
  } catch (e) {
    showToast(e.message || '保存失败')
  } finally {
    saving.value = false
  }
}

async function makeDefault(p) {
  try {
    await setServiceDefault(p.id)
    showSuccessToast(`已将「${p.name}」设为默认`)
    await load()
  } catch (e) {
    showToast(e.message || '操作失败')
  }
}

async function toggleEnabled(p) {
  try {
    await updateServiceProvider(p.id, { enabled: !p.enabled, isDefault: p.enabled ? false : p.isDefault })
    await load()
  } catch (e) {
    showToast(e.message || '操作失败')
  }
}

async function remove(p) {
  try {
    await showConfirmDialog({ title: '删除供应商', message: `确定删除「${p.name}」？删除后不可恢复。` })
  } catch {
    return
  }
  try {
    await deleteServiceProvider(p.id)
    showSuccessToast('已删除')
    await load()
  } catch (e) {
    showToast(e.message || '删除失败')
  }
}

async function runTest(p) {
  testing.value = p.id
  try {
    const r = await testServiceProvider(p.id)
    testResults.value = { ...testResults.value, [p.id]: r }
  } catch (e) {
    testResults.value = { ...testResults.value, [p.id]: { pass: false, message: e.message || '测试失败' } }
  } finally {
    testing.value = 0
  }
}

onMounted(load)
</script>

<style scoped>
.error-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #FCEBEB;
  color: #A32D2D;
  border: 1px solid #F5C6C6;
  border-radius: 12px;
  padding: 12px 16px;
  font-size: 13px;
}

.retry-btn {
  border: 1px solid #E0A0A0;
  background: #fff;
  color: #A32D2D;
  border-radius: 8px;
  padding: 5px 14px;
  font-size: 12px;
  cursor: pointer;
}
.retry-btn:hover {
  background: #FBF0F0;
}

.services-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header h2 {
  margin: 0 0 6px;
  font-size: 20px;
  color: #16233F;
}

.page-header .sub {
  margin: 0;
  font-size: 13px;
  color: #7A8499;
}

.loading {
  color: #7A8499;
  padding: 40px;
  text-align: center;
}

/* ---------- 分类卡片 ---------- */
.cat-card {
  background: #fff;
  border-radius: 14px;
  padding: 20px;
  box-shadow: 0 2px 10px rgba(22, 35, 63, 0.06);
}

.cat-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 14px;
}

.cat-name {
  font-size: 15px;
  font-weight: 600;
  color: #16233F;
}

.cat-desc {
  font-size: 12px;
  color: #7A8499;
  margin-top: 4px;
}

.cat-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.mode-badge {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 20px;
  font-weight: 500;
}
.mode-badge.real {
  background: #E1F5EE;
  color: #0F6E56;
}
.mode-badge.mock {
  background: #EEEDFE;
  color: #534AB7;
}

.active-name {
  font-size: 12px;
  color: #45506A;
}
.active-name.muted {
  color: #A0A8B8;
}

.add-btn {
  border: none;
  background: #185FA5;
  color: #fff;
  font-size: 13px;
  padding: 7px 14px;
  border-radius: 8px;
  cursor: pointer;
}
.add-btn:hover {
  background: #0D4E8C;
}

/* ---------- 表格 ---------- */
.table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.table th {
  text-align: left;
  padding: 10px 12px;
  color: #7A8499;
  font-weight: 500;
  font-size: 12px;
  border-bottom: 1px solid #EDF0F5;
  white-space: nowrap;
}
.table td {
  padding: 12px;
  color: #2A3448;
  border-bottom: 1px solid #F2F4F8;
  vertical-align: middle;
}
.table tr.disabled td {
  color: #A0A8B8;
}
.table tr:last-child td {
  border-bottom: none;
}

.mono {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
}
.url-cell {
  max-width: 260px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ptype {
  background: #F1F4FA;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 12px;
  color: #45506A;
}

.default-star {
  color: #F59E0B;
  margin-right: 4px;
}

.status {
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 20px;
}
.status.on {
  background: #E1F5EE;
  color: #0F6E56;
}
.status.off {
  background: #F2F4F8;
  color: #A0A8B8;
}

.link-btn {
  border: none;
  background: none;
  color: #185FA5;
  font-size: 13px;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 6px;
}
.link-btn:hover {
  background: #E6F1FB;
}
.link-btn.danger {
  color: #C0392B;
}
.link-btn.danger:hover {
  background: #FCEBEB;
}

.empty {
  padding: 24px;
  text-align: center;
  color: #A0A8B8;
  font-size: 13px;
  background: #FAFBFD;
  border-radius: 10px;
}

.test-result {
  margin-top: 12px;
  padding: 10px 14px;
  border-radius: 10px;
  font-size: 13px;
}
.test-result.pass {
  background: #E1F5EE;
  color: #0F6E56;
}
.test-result.fail {
  background: #FCEBEB;
  color: #A32D2D;
}

/* ---------- 弹窗 ---------- */
.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(13, 27, 62, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.modal {
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  width: 460px;
  max-height: 86vh;
  overflow-y: auto;
}
.modal h3 {
  margin: 0 0 18px;
  font-size: 17px;
  color: #16233F;
}

.form-item {
  margin-bottom: 14px;
}
.form-item label {
  display: block;
  font-size: 12px;
  color: #7A8499;
  margin-bottom: 6px;
}
.form-item label i {
  color: #C0392B;
  font-style: normal;
}
.form-item input[type='text'],
.form-item input:not([type]) {
  width: 100%;
  box-sizing: border-box;
  border: 1px solid #DEE4EE;
  border-radius: 8px;
  padding: 9px 12px;
  font-size: 13px;
  outline: none;
}
.form-item input:focus {
  border-color: #185FA5;
}
.form-item input[type='password'] {
  width: 100%;
  box-sizing: border-box;
  border: 1px solid #DEE4EE;
  border-radius: 8px;
  padding: 9px 12px;
  font-size: 13px;
  outline: none;
}
.form-item input[type='password']:focus {
  border-color: #185FA5;
}
.form-item .hint {
  margin: 4px 0 0;
  font-size: 11px;
  color: #A0A8B8;
}

.type-picker {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.type-opt {
  border: 1px solid #DEE4EE;
  background: #fff;
  border-radius: 8px;
  padding: 6px 12px;
  font-size: 12px;
  color: #45506A;
  cursor: pointer;
}
.type-opt.active {
  border-color: #185FA5;
  background: #E6F1FB;
  color: #185FA5;
}

.checkbox {
  display: inline-flex !important;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #2A3448;
  margin-right: 18px;
  cursor: pointer;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}
.btn {
  border: none;
  border-radius: 8px;
  padding: 9px 20px;
  font-size: 13px;
  cursor: pointer;
}
.btn.primary {
  background: #185FA5;
  color: #fff;
}
.btn.primary:disabled {
  opacity: 0.6;
}
.btn.ghost {
  background: #F2F4F8;
  color: #45506A;
}
.test-result-inline {
  margin-top: 8px;
  padding: 6px 10px;
  border-radius: 8px;
  font-size: 12px;
}
.test-result-inline.pass {
  background: #E1F5EE;
  color: #0F6E56;
}
.test-result-inline.fail {
  background: #FCEBEB;
  color: #A32D2D;
}
</style>
