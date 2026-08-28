<template>
  <div class="page">
    <!-- 脱敏开关 -->
    <div class="panel mask-panel" v-if="canManageSettings">
      <div class="mask-head">
        <div>
          <div class="panel-title">敏感字段脱敏展示</div>
          <div class="mask-desc">
            开启后，手机号 / 身份证号在接口层统一返回掩码（如 138****6688）；
            拥有「查看敏感字段明文」权限的角色不受影响。当前你的角色
            <b :class="maskStatus.canSeeRaw ? 'ok-text' : ''">{{ maskStatus.canSeeRaw ? '可查看明文' : '同样被脱敏' }}</b>。
          </div>
        </div>
        <label class="switch">
          <input type="checkbox" :checked="settings.maskSensitive" @change="toggleMask" />
          <span class="slider"></span>
        </label>
      </div>
      <div class="mask-preview">
        <span class="preview-label">脱敏效果预览</span>
        <span class="preview-chip">手机号 {{ settings.maskSensitive ? '138****6688' : '13812346688' }}</span>
        <span class="preview-chip">身份证 {{ settings.maskSensitive ? '3101**********1234' : '310101199001011234' }}</span>
      </div>
    </div>
    <div v-else-if="settingsLoaded" class="panel mask-readonly">
      敏感字段脱敏：<b>{{ settings.maskSensitive ? '已开启' : '已关闭' }}</b>（如需调整请联系管理员）
    </div>

    <!-- 角色权限矩阵 -->
    <div class="panel matrix-panel">
      <div class="matrix-head">
        <div class="panel-title">角色权限矩阵</div>
        <div class="role-tabs">
          <button
            v-for="r in roles"
            :key="r.code"
            class="role-tab"
            :class="{ active: currentRole?.code === r.code }"
            @click="selectRole(r)"
          >
            {{ r.name }}
          </button>
        </div>
      </div>

      <div v-if="currentRole" class="role-desc">{{ currentRole.description }}</div>

      <div v-if="currentRole && canManageRoles" class="perm-groups">
        <div v-for="(perms, module) in groupedPermissions" :key="module" class="perm-group">
          <div class="group-label">{{ module }}</div>
          <div class="group-items">
            <label v-for="p in perms" :key="p.code" class="perm-item" :class="{ checked: draft.includes(p.code) }">
              <input type="checkbox" :checked="draft.includes(p.code)" @change="togglePerm(p.code)" />
              <span>{{ p.name }}</span>
              <code class="perm-code">{{ p.code }}</code>
            </label>
          </div>
        </div>
      </div>

      <table v-else-if="currentRole" class="data-table perm-read-table">
        <thead>
          <tr><th>权限</th><th>权限码</th></tr>
        </thead>
        <tbody>
          <tr v-for="c in catalog.filter(p => currentRole.permissions.includes(p.code))" :key="c.code">
            <td>{{ c.name }}</td>
            <td><code class="perm-code">{{ c.code }}</code></td>
          </tr>
        </tbody>
      </table>

      <div v-if="canManageRoles && dirty" class="save-bar">
        <span class="dirty-tip">权限已修改但未保存（{{ draft.length }} 项授权）</span>
        <button class="ghost-btn" @click="resetDraft">放弃</button>
        <button class="primary-btn" :disabled="saving" @click="savePerms">保存授权</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { showSuccessToast, showToast } from 'vant'
import {
  fetchPermissions,
  fetchRoles,
  updateRolePermissions,
  fetchSettings,
  updateSettings,
  fetchMaskStatus,
} from '../../api/admin'

const catalog = ref([])
const roles = ref([])
const currentRole = ref(null)
const draft = ref([])
const saving = ref(false)
const settings = ref({ maskSensitive: true, maskedPhoneVisibleChars: 3 })
const settingsLoaded = ref(false)
const maskStatus = ref({ maskOn: true, canSeeRaw: false })

const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}')
const userPerms = userInfo.permissions ?? null // null = 旧版本登录态，放行展示
const hasPermUI = (code) => userPerms === null || userPerms.includes(code)
const canManageRoles = hasPermUI('admin.roles.manage')
const canManageSettings = hasPermUI('admin.settings.manage')

// 按模块分组
const groupedPermissions = computed(() => {
  const map = {}
  for (const p of catalog.value) {
    ;(map[p.module] ||= []).push(p)
  }
  return map
})

const dirty = computed(() => {
  if (!currentRole.value) return false
  const origin = [...currentRole.value.permissions].sort().join(',')
  return origin !== [...draft.value].sort().join(',')
})

function selectRole(r) {
  // 有未保存修改时提醒
  if (dirty.value) {
    showToast('有未保存的权限修改，已丢弃')
  }
  currentRole.value = r
  resetDraft()
}

function resetDraft() {
  draft.value = [...(currentRole.value?.permissions || [])]
}

function togglePerm(code) {
  const i = draft.value.indexOf(code)
  if (i === -1) draft.value.push(code)
  else draft.value.splice(i, 1)
}

async function savePerms() {
  saving.value = true
  try {
    await updateRolePermissions(currentRole.value.code, draft.value)
    currentRole.value.permissions = [...draft.value]
    showSuccessToast(`「${currentRole.value.name}」授权已更新`)
    // 若改的是自己的角色，提示重新登录生效
    if (userInfo.role === currentRole.value.code) {
      showToast('你刚修改了自己角色的权限，重新登录后菜单随之刷新')
    }
  } catch (e) {
    showToast(e.message || '保存失败')
  } finally {
    saving.value = false
  }
}

async function toggleMask(e) {
  const next = e.target.checked
  try {
    settings.value = await updateSettings({ maskSensitive: next })
    showSuccessToast(next ? '脱敏已开启' : '脱敏已关闭')
  } catch (err) {
    e.target.checked = !next
    showToast(err.message || '设置失败')
  }
}

onMounted(async () => {
  try {
    const [cats, rs] = await Promise.all([fetchPermissions(), fetchRoles()])
    catalog.value = cats
    roles.value = rs
    currentRole.value = rs[0] || null
    resetDraft()
  } catch (e) { /* 拦截器已提示 */ }

  try {
    settings.value = await fetchSettings()
  } catch (e) { /* 无 settings.manage 权限时读取失败，维持默认 */ }
  settingsLoaded.value = true

  fetchMaskStatus().then((s) => (maskStatus.value = s)).catch(() => {})
})
</script>

<style scoped>
.panel {
  background: #fff;
  border-radius: 14px;
  padding: 20px;
  box-shadow: 0 2px 10px rgba(23, 35, 61, 0.05);
  margin-bottom: 16px;
}

.panel-title {
  font-size: 15px;
  font-weight: 600;
  color: #17233D;
}

/* 脱敏开关 */
.mask-panel {
  display: block;
}

.mask-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
}

.mask-desc {
  font-size: 13px;
  color: #5A6A8F;
  margin-top: 8px;
  line-height: 1.7;
  max-width: 640px;
}

.mask-desc b {
  color: #98A5C3;
  font-weight: 600;
}

.mask-desc b.ok-text {
  color: #00A884;
}

.switch {
  position: relative;
  width: 48px;
  height: 27px;
  flex-shrink: 0;
  cursor: pointer;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  inset: 0;
  background: #CDD5E5;
  border-radius: 999px;
  transition: background 0.2s;
}

.slider::before {
  content: '';
  position: absolute;
  width: 21px;
  height: 21px;
  left: 3px;
  top: 3px;
  border-radius: 50%;
  background: #fff;
  transition: transform 0.2s;
}

.switch input:checked + .slider {
  background: linear-gradient(90deg, #2E6BFF, #00C2A8);
}

.switch input:checked + .slider::before {
  transform: translateX(21px);
}

.mask-preview {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 14px;
  flex-wrap: wrap;
}

.preview-label {
  font-size: 12px;
  color: #98A5C3;
}

.preview-chip {
  font-size: 12px;
  background: #F0F3FA;
  color: #3D4A6B;
  padding: 5px 12px;
  border-radius: 999px;
  font-variant-numeric: tabular-nums;
}

.mask-readonly {
  font-size: 13px;
  color: #5A6A8F;
}

.mask-readonly b {
  color: #17233D;
}

/* 权限矩阵 */
.matrix-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 6px;
}

.role-tabs {
  display: flex;
  background: #EBEEF6;
  border-radius: 10px;
  padding: 3px;
}

.role-tab {
  border: none;
  background: transparent;
  padding: 7px 18px;
  font-size: 13px;
  color: #5A6A8F;
  border-radius: 8px;
  cursor: pointer;
}

.role-tab.active {
  background: #fff;
  color: #17233D;
  font-weight: 600;
  box-shadow: 0 1px 4px rgba(23, 35, 61, 0.12);
}

.role-desc {
  font-size: 12px;
  color: #7C8DB5;
  margin-bottom: 16px;
}

.perm-groups {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.group-label {
  font-size: 12px;
  font-weight: 600;
  color: #2E6BFF;
  margin-bottom: 8px;
}

.group-items {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 10px;
}

.perm-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 11px 14px;
  border: 1px solid #E5E9F2;
  border-radius: 10px;
  cursor: pointer;
  font-size: 13px;
  color: #3D4A6B;
  transition: all 0.15s;
  user-select: none;
}

.perm-item:hover {
  border-color: #85B7EB;
}

.perm-item.checked {
  border-color: #2E6BFF;
  background: #F3F8FF;
  color: #17233D;
}

.perm-item input {
  accent-color: #2E6BFF;
  width: 15px;
  height: 15px;
}

.perm-code {
  margin-left: auto;
  font-size: 11px;
  color: #98A5C3;
  font-family: Menlo, Consolas, monospace;
}

.perm-read-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.perm-read-table th {
  text-align: left;
  padding: 10px 8px;
  color: #7C8DB5;
  font-weight: 500;
  border-bottom: 1px solid #EDF0F7;
}

.perm-read-table td {
  padding: 10px 8px;
  border-bottom: 1px solid #F4F6FB;
  color: #3D4A6B;
}

.save-bar {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #EDF0F7;
}

.dirty-tip {
  font-size: 12px;
  color: #BA7517;
}

.primary-btn {
  background: linear-gradient(90deg, #2E6BFF, #4C86FF);
  color: #fff;
  border: none;
  padding: 9px 22px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

.primary-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.ghost-btn {
  padding: 9px 18px;
  border: 1px solid #E0E5F0;
  border-radius: 10px;
  background: #fff;
  font-size: 13px;
  color: #5A6A8F;
  cursor: pointer;
}
</style>
