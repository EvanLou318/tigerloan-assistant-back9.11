<template>
  <van-config-provider :theme-vars="themeVars">
    <router-view v-slot="{ Component }">
      <transition :name="transitionName" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
  </van-config-provider>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { navDirection } from './router'

const route = useRoute()

// Tab 主区间淡切；子页面前进右滑入、返回左滑入
const transitionName = computed(() => {
  if (navDirection.value === 'tab') return 'page-fade'
  if (navDirection.value === 'back') return 'slide-right'
  return 'slide-left'
})

const themeVars = {
  // 浅色插画风：白底 + 蓝/青/紫主调
  primaryColor: '#3B82F6',
  successColor: '#10B981',
  dangerColor: '#EF4444',
  warningColor: '#F59E0B',
  background: '#F8FAFC',
  background2: '#FFFFFF',
  textColor: '#0F172A',
  textColor2: '#475569',
  textColor3: '#94A3B8',
  borderColor: '#E2E8F0',
  cellBackground: '#FFFFFF',
  cellTextColor: '#0F172A',
  navBarBackground: '#F8FAFC',
  navBarTitleTextColor: '#0F172A',
  navBarTextColor: '#0F172A',
  tabbarBackground: 'rgba(255,255,255,0.95)',
  tabbarItemActiveTextColor: '#3B82F6',
  buttonPrimaryBackground: '#3B82F6',
  buttonPrimaryBorderColor: '#3B82F6',
  buttonPrimaryTextColor: '#FFFFFF',
  fieldInputTextColor: '#0F172A',
  fieldPlaceholderTextColor: '#94A3B8',
  popupBackground: '#FFFFFF',
  actionSheetBackground: '#FFFFFF',
  searchBackground: 'transparent',
  tabActiveTextColor: '#3B82F6',
  tagPrimaryColor: '#3B82F6',
  switchOnBackground: '#3B82F6',
}
</script>

<style>
/* ============ 页面转场（非 scoped，作用于路由组件根节点） ============ */

/* Tab 主区间切换：轻淡 */
.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.18s ease;
}
.page-fade-enter-from,
.page-fade-leave-to {
  opacity: 0;
}

/* 前进：新页从右侧滑入 */
.slide-left-enter-active {
  transition: transform 0.28s cubic-bezier(0.22, 0.61, 0.36, 1), opacity 0.28s ease;
}
.slide-left-leave-active {
  transition: opacity 0.2s ease;
}
.slide-left-enter-from {
  transform: translateX(48px);
  opacity: 0;
}
.slide-left-leave-to {
  opacity: 0;
}

/* 返回：页面从左侧滑回 */
.slide-right-enter-active {
  transition: transform 0.28s cubic-bezier(0.22, 0.61, 0.36, 1), opacity 0.28s ease;
}
.slide-right-leave-active {
  transition: opacity 0.2s ease;
}
.slide-right-enter-from {
  transform: translateX(-48px);
  opacity: 0;
}
.slide-right-leave-to {
  opacity: 0;
}
</style>
