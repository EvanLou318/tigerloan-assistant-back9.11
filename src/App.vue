<template>
  <van-config-provider :theme-vars="themeVars">
    <router-view v-slot="{ Component }">
      <transition :name="transitionName" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
    <!-- 全局语音输入面板：任意输入框唤起 ASR -->
    <VoiceInputSheet />
  </van-config-provider>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { navDirection } from './router'
import VoiceInputSheet from './components/VoiceInputSheet.vue'

const route = useRoute()

// Tab 主区间淡切；子页面前进右滑入、返回左滑入
const transitionName = computed(() => {
  if (navDirection.value === 'tab') return 'page-fade'
  if (navDirection.value === 'back') return 'slide-right'
  return 'slide-left'
})

const themeVars = {
  // 浅色插画风：白底 + 蓝/青/紫主调
  primaryColor: '#2563EB',
  successColor: '#12B76A',
  dangerColor: '#F04438',
  warningColor: '#F79009',
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
  tabbarItemActiveTextColor: '#2563EB',
  buttonPrimaryBackground: '#2563EB',
  buttonPrimaryBorderColor: '#2563EB',
  buttonPrimaryTextColor: '#FFFFFF',
  fieldInputTextColor: '#0F172A',
  fieldPlaceholderTextColor: '#94A3B8',
  popupBackground: '#FFFFFF',
  actionSheetBackground: '#FFFFFF',
  searchBackground: 'transparent',
  tabActiveTextColor: '#2563EB',
  tagPrimaryColor: '#2563EB',
  switchOnBackground: '#2563EB',
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
