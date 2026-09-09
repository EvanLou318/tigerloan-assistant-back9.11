<template>
  <div class="layout-container">
    <div class="layout-content">
      <slot></slot>
    </div>

    <!-- 底部主导航：首页 / 产品 / 客户 / 日程 / 我的 -->
    <nav class="main-tabbar">
      <router-link
        v-for="item in tabs"
        :key="item.to"
        :to="item.to"
        class="tab"
        :class="{ active: isActive(item) }"
      >
        <span class="tab-icon-wrap">
          <van-icon :name="item.icon" :size="22" />
          <span v-if="item.badge && item.badge > 0" class="tab-badge">{{ item.badge > 99 ? '99+' : item.badge }}</span>
        </span>
        <span class="tab-label">{{ item.label }}</span>
      </router-link>
    </nav>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useScheduleStore } from '../stores/schedule'

const route = useRoute()
const scheduleStore = useScheduleStore()

// 日程 tab 带未办角标（今日 + 逾期高优提醒）
const tabs = computed(() => [
  { to: '/home', label: '首页', icon: 'home-o', match: ['/home'] },
  { to: '/products', label: '产品', icon: 'apps-o', match: ['/products'] },
  { to: '/customers', label: '客户', icon: 'friends-o', match: ['/customers'] },
  { to: '/schedules', label: '日程', icon: 'todo-list-o', match: ['/schedules'], badge: scheduleStore.todayCount },
])

function isActive(item) {
  return item.match.some((p) => route.path === p || route.path.startsWith(p + '/'))
}
</script>

<style scoped>
.layout-container {
  min-height: 100vh;
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  background: var(--bg-base);
}

.layout-content {
  flex: 1;
  overflow-y: auto;
  /* 底部留出 tabbar 高度 + 安全区 */
  padding-bottom: calc(64px + env(safe-area-inset-bottom));
}

/* ============ 底部导航：悬浮白色块 + 药丸指示 ============ */
.main-tabbar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 100;
  display: flex;
  background: var(--surface-container-lowest);
  box-shadow: 0 -2px 16px rgba(26, 34, 51, 0.06);
  padding: 6px 4px calc(6px + env(safe-area-inset-bottom));
}

.tab {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 6px 0 4px;
  text-decoration: none;
  color: var(--text-tertiary);
  -webkit-tap-highlight-color: transparent;
  user-select: none;
}

.tab-icon-wrap {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 30px;
  border-radius: 999px;
  transition: background 0.2s ease, transform 0.15s ease;
}

.tab:active .tab-icon-wrap {
  transform: scale(0.9);
}

.tab.active {
  color: var(--color-primary);
}

.tab.active .tab-icon-wrap {
  background: var(--primary-container);
}

.tab-label {
  font-size: 11px;
  line-height: 1.2;
  transition: font-weight 0.2s;
}

.tab.active .tab-label {
  font-weight: 600;
}

.tab-badge {
  position: absolute;
  top: -2px;
  right: 4px;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  border-radius: 999px;
  background: var(--color-danger);
  color: #fff;
  font-size: 10px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}
</style>
