<template>
  <div class="page">
    <div class="toolbar">
      <span class="count-badge">共 {{ users.length }} 个账号</span>
      <button class="primary-btn" @click="openCreate">+ 新建用户</button>
    </div>

    <div class="panel">
      <table class="data-table">
        <thead>
          <tr>
            <th>用户</th>
            <th>手机号</th>
            <th>角色</th>
            <th class="num">客户数</th>
            <th class="num">产品数</th>
            <th class="num">日程数</th>
            <th class="num">AI匹配次数</th>
            <th>注册时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.id">
            <td class="name-cell">
              <span class="avatar">{{ u.name[0] }}</span>
              {{ u.name }}
            </td>
            <td class="mono">{{ u.phone }}</td>
            <td>
              <span class="role" :class="u.role === 'admin' ? 'admin' : ''">{{ u.roleName || u.role }}</span>
              <button class="link-btn role-edit" @click="openRoleChange(u)">改角色</button>
            </td>
            <td class="num">{{ u.customerCount }}</td>
            <td class="num">{{ u.productCount }}</td>
            <td class="num">{{ u.scheduleCount }}</td>
            <td class="num">{{ u.simulationCount }}</td>
            <td class="time-cell">{{ (u.createdAt || '').slice(0, 10) }}</td>
            <td class="op-cell">
              <button class="link-btn" @click="openReset(u)">重置密码</button>
              <button class="link-btn danger" @click="remove(u)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 新建用户弹窗 -->
    <teleport to="body">
      <div v-if="showCreate" class="modal-mask" @click.self="showCreate = false">
        <div class="modal">
          <div class="modal-title">新建用户</div>
          <div class="form-item">
            <label>姓名</label>
            <input v-model="createForm.name" placeholder="如 王经理" />
          </div>
          <div class="form-item">
            <label>手机号</label>
            <input v-model="createForm.phone" placeholder="11 位手机号" maxlength="11" />
          </div>
          <div class="form-item">
            <label>初始密码</label>
            <input v-model="createForm.password" type="password" placeholder="至少 6 位" />
          </div>
          <div class="form-item">
            <label>角色</label>
            <div class="role-picker">
              <button
                v-for="r in roles"
                :key="r.code"
                class="role-opt"
                :class="{ active: createForm.role === r.code }"
                @click="createForm.role = r.code"
              >
                {{ r.name }}
              </button>
            </div>
          </div>
          <div class="modal-actions">
            <button class="ghost-btn" @click="showCreate = false">取消</button>
            <button class="primary-btn" :disabled="saving" @click="submitCreate">创建</button>
          </div>
        </div>
      </div>
    </teleport>

    <!-- 改角色弹窗 -->
    <teleport to="body">
      <div v-if="roleTarget" class="modal-mask" @click.self="roleTarget = null">
        <div class="modal">
          <div class="modal-title">调整角色 · {{ roleTarget.name }}</div>
          <div class="form-item">
            <label>当前角色：{{ roleTarget.roleName || roleTarget.role }}</label>
            <div class="role-picker">
              <button
                v-for="r in roles"
                :key="r.code"
                class="role-opt"
                :class="{ active: newRole === r.code }"
                @click="newRole = r.code"
              >
                {{ r.name }}
                <span class="opt-desc">{{ r.description }}</span>
              </button>
            </div>
          </div>
          <div class="form-item tip-line">角色调整后，该用户重新登录即可获得新角色的菜单与接口权限</div>
          <div class="modal-actions">
            <button class="ghost-btn" @click="roleTarget = null">取消</button>
            <button class="primary-btn" :disabled="saving" @click="submitRoleChange">确认调整</button>
          </div>
        </div>
      </div>
    </teleport>

    <!-- 重置密码弹窗 -->
    <teleport to="body">
      <div v-if="resetTarget" class="modal-mask" @click.self="resetTarget = null">
        <div class="modal">
          <div class="modal-title">重置密码 · {{ resetTarget.name }}</div>
          <div class="form-item">
            <label>新密码</label>
            <input v-model="resetPassword" type="password" placeholder="至少 6 位" />
          </div>
          <div class="modal-actions">
            <button class="ghost-btn" @click="resetTarget = null">取消</button>
            <button class="primary-btn" :disabled="saving" @click="submitReset">确认重置</button>
          </div>
        </div>
      </div>
    </teleport>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { showConfirmDialog, showSuccessToast, showToast } from 'vant'
import {
  fetchAdminUsers,
  createAdminUser,
  resetUserPassword,
  deleteAdminUser,
  fetchRoles,
  updateUserRole,
} from '../../api/admin'

const users = ref([])
const roles = ref([])
const showCreate = ref(false)
const createForm = ref({ name: '', phone: '', password: '', role: 'loan_manager' })
const resetTarget = ref(null)
const resetPassword = ref('')
const roleTarget = ref(null)
const newRole = ref('')
const saving = ref(false)

async function load() {
  try {
    users.value = await fetchAdminUsers()
  } catch (e) { /* 拦截器已提示 */ }
}

function openCreate() {
  createForm.value = { name: '', phone: '', password: '', role: roles.value[roles.value.length - 1]?.code || 'loan_manager' }
  showCreate.value = true
}

async function submitCreate() {
  saving.value = true
  try {
    await createAdminUser(createForm.value)
    showCreate.value = false
    showSuccessToast('用户已创建')
    await load()
  } catch (e) {
    showToast(e.message || '创建失败')
  } finally {
    saving.value = false
  }
}

function openReset(u) {
  resetTarget.value = u
  resetPassword.value = ''
}

function openRoleChange(u) {
  roleTarget.value = u
  newRole.value = u.role
}

async function submitRoleChange() {
  saving.value = true
  try {
    await updateUserRole(roleTarget.value.id, newRole.value)
    roleTarget.value = null
    showSuccessToast('角色已调整')
    await load()
  } catch (e) {
    showToast(e.message || '调整失败')
  } finally {
    saving.value = false
  }
}

async function submitReset() {
  saving.value = true
  try {
    await resetUserPassword(resetTarget.value.id, resetPassword.value)
    resetTarget.value = null
    showSuccessToast('密码已重置')
  } catch (e) {
    showToast(e.message || '重置失败')
  } finally {
    saving.value = false
  }
}

async function remove(u) {
  try {
    await showConfirmDialog({
      title: '删除用户',
      message: `确定删除「${u.name}（${u.phone}）」吗？`,
    })
  } catch {
    return
  }
  try {
    await deleteAdminUser(u.id)
    showSuccessToast('已删除')
    await load()
  } catch (e) {
    showToast(e.message || '删除失败')
  }
}

onMounted(() => {
  load()
  fetchRoles().then((rs) => (roles.value = rs)).catch(() => {})
})
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 14px;
}

.count-badge {
  font-size: 12px;
  color: #7C8DB5;
}

.primary-btn {
  margin-left: auto;
  background: linear-gradient(90deg, #2E6BFF, #4C86FF);
  color: #fff;
  border: none;
  padding: 9px 20px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(46, 107, 255, 0.3);
}

.primary-btn:hover {
  filter: brightness(1.05);
}

.primary-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
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

.name-cell {
  font-weight: 600;
  color: #17233D;
  white-space: nowrap;
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

.mono {
  font-variant-numeric: tabular-nums;
}

.role {
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 999px;
  background: #F0F3FA;
  color: #5A6A8F;
  white-space: nowrap;
}

.role.admin {
  background: #FFF4E5;
  color: #F59E0B;
}

.role-edit {
  font-size: 11px;
  padding: 2px 6px;
  margin-left: 4px;
}

.opt-desc {
  display: block;
  font-size: 10px;
  color: #98A5C3;
  margin-top: 3px;
  white-space: normal;
}

.tip-line {
  font-size: 12px;
  color: #BA7517;
}

.time-cell {
  color: #98A5C3;
  font-size: 12px;
  white-space: nowrap;
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

/* 弹窗 */
.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(13, 27, 62, 0.45);
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal {
  width: 400px;
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 20px 60px rgba(13, 27, 62, 0.25);
}

.modal-title {
  font-size: 16px;
  font-weight: 700;
  color: #17233D;
  margin-bottom: 18px;
}

.form-item {
  margin-bottom: 14px;
}

.form-item label {
  display: block;
  font-size: 12px;
  color: #7C8DB5;
  margin-bottom: 6px;
}

.form-item input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #E0E5F0;
  border-radius: 10px;
  font-size: 13px;
  outline: none;
  box-sizing: border-box;
  transition: border 0.15s;
}

.form-item input:focus {
  border-color: #2E6BFF;
}

.role-picker {
  display: flex;
  gap: 10px;
}

.role-opt {
  flex: 1;
  padding: 9px;
  border: 1px solid #E0E5F0;
  border-radius: 10px;
  background: #fff;
  font-size: 13px;
  color: #5A6A8F;
  cursor: pointer;
}

.role-opt.active {
  border-color: #2E6BFF;
  background: #EBF1FF;
  color: #2E6BFF;
  font-weight: 600;
}

.modal-actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
}

.ghost-btn {
  flex: 1;
  padding: 10px;
  border: 1px solid #E0E5F0;
  border-radius: 10px;
  background: #fff;
  font-size: 13px;
  color: #5A6A8F;
  cursor: pointer;
}

.modal-actions .primary-btn {
  flex: 1;
  margin-left: 0;
}
</style>
