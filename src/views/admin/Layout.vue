<template>
  <div class="admin-shell">
    <!-- 侧边栏 -->
    <aside class="admin-sidebar">
      <div class="brand">
        <div class="brand-logo">智</div>
        <div class="brand-text">
          <div class="brand-name">智贷助手</div>
          <div class="brand-sub">管理后台</div>
        </div>
      </div>

      <nav class="admin-nav">
        <router-link
          v-for="item in visibleNavItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: isActive(item.path) }"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </router-link>
        <div v-if="!allVisible" class="perm-note">按当前角色权限展示菜单</div>
      </nav>

      <div class="sidebar-footer">
        <div class="admin-user">
          <div class="avatar">{{ (userInfo?.name || '管')[0] }}</div>
          <div class="user-meta">
            <div class="user-name">{{ userInfo?.name || '管理员' }}</div>
            <div class="user-role">{{ userInfo?.roleName || '管理员' }}</div>
          </div>
        </div>
        <button class="exit-btn" @click="onExit">返回移动端</button>
      </div>
    </aside>

    <!-- 内容区 -->
    <main class="admin-main">
      <header class="admin-topbar">
        <h1 class="page-title">{{ pageTitle }}</h1>
        <div class="topbar-right">
          <span class="env-badge">Demo 环境 · AI Provider: Mock</span>
        </div>
      </header>
      <div class="admin-content">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const userInfo = JSON.parse(localStorage.getItem('userInfo') || 'null')

const navItems = [
  { path: '/admin/dashboard', label: '数据看板', icon: '📊', perm: 'admin.dashboard.view' },
  { path: '/admin/customers', label: '客户管理', icon: '👥', perm: 'admin.customers.view' },
  { path: '/admin/products', label: '产品管理', icon: '📦', perm: 'admin.products.view' },
  { path: '/admin/schedules', label: '日程管理', icon: '📅', perm: 'admin.schedules.view' },
  { path: '/admin/users', label: '用户管理', icon: '🔑', perm: 'admin.users.view' },
  { path: '/admin/security', label: '权限与安全', icon: '🛡️', perm: 'admin.roles.manage' },
  { path: '/admin/services', label: '三方服务', icon: '🔌', perm: 'admin.services.view' },
]

// RBAC：按登录时返回的权限过滤菜单；旧登录态无 permissions 字段则全量展示
const userPerms = userInfo?.permissions ?? null
const visibleNavItems = navItems.filter((item) => !userPerms || userPerms.includes(item.perm))
const allVisible = !userPerms

const pageTitle = computed(() => route.meta.title || '管理后台')

function isActive(path) {
  return route.path.startsWith(path)
}

function onExit() {
  router.push('/home')
}
</script>

<style scoped>
.admin-shell {
  display: flex;
  min-height: 100vh;
  background: #F3F5FA;
  font-family: -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

/* ---------- 侧边栏 ---------- */
.admin-sidebar {
  width: 232px;
  flex-shrink: 0;
  background: linear-gradient(180deg, #0D1B3E 0%, #10264F 100%);
  color: #fff;
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 0;
  height: 100vh;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 24px 20px;
}

.brand-logo {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: linear-gradient(135deg, #2E6BFF, #00C2A8);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 700;
}

.brand-name {
  font-size: 16px;
  font-weight: 600;
}

.brand-sub {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.55);
  margin-top: 2px;
}

.admin-nav {
  flex: 1;
  padding: 8px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 11px 14px;
  border-radius: 10px;
  color: rgba(255, 255, 255, 0.72);
  text-decoration: none;
  font-size: 14px;
  transition: all 0.15s;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}

.nav-item.active {
  background: linear-gradient(90deg, rgba(46, 107, 255, 0.9), rgba(0, 194, 168, 0.55));
  color: #fff;
  font-weight: 600;
  box-shadow: 0 4px 14px rgba(46, 107, 255, 0.35);
}

.nav-icon {
  font-size: 16px;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.admin-user {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: rgba(46, 107, 255, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
}

.user-name {
  font-size: 13px;
  font-weight: 600;
}

.user-role {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.5);
}

.exit-btn {
  width: 100%;
  padding: 8px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 8px;
  background: transparent;
  color: rgba(255, 255, 255, 0.75);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s;
}

.exit-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}

.perm-note {
  margin-top: auto;
  padding: 10px;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.35);
  text-align: center;
}

/* ---------- 内容区 ---------- */
.admin-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.admin-topbar {
  height: 60px;
  background: #fff;
  border-bottom: 1px solid #E5E9F2;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 28px;
}

.page-title {
  font-size: 17px;
  font-weight: 600;
  color: #17233D;
}

.env-badge {
  font-size: 12px;
  color: #2E6BFF;
  background: #EBF1FF;
  padding: 5px 12px;
  border-radius: 999px;
}

.admin-content {
  flex: 1;
  padding: 24px 28px;
}
</style>
