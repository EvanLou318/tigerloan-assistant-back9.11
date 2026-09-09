<template>
  <svg
    class="app-icon"
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    :stroke="strokeWidth ? 'currentColor' : 'none'"
    :stroke-width="strokeWidth"
    stroke-linecap="round"
    stroke-linejoin="round"
    :style="{ color: color }"
    v-html="body"
    aria-hidden="true"
  ></svg>
</template>

<script setup>
import { computed } from 'vue'
import { ICONS } from './icons.js'

const props = defineProps({
  name: { type: String, required: true },
  size: { type: [Number, String], default: 20 },
  color: { type: String, default: 'currentColor' },
  /** 线宽；传 0 表示纯填充图标 */
  strokeWidth: { type: [Number, String], default: 1.75 },
})

const body = computed(() => ICONS[props.name] || ICONS.circle)
</script>

<style scoped>
.app-icon {
  display: inline-block;
  vertical-align: middle;
  flex-shrink: 0;
}
</style>
