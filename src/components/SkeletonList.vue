<template>
  <div class="skeleton-list" aria-hidden="true">
    <div v-for="i in count" :key="i" class="skeleton-card">
      <div class="sk-row">
        <div class="sk sk-title" style="width: 45%"></div>
        <div class="sk sk-tag" style="width: 52px; height: 22px; border-radius: 8px"></div>
      </div>
      <div class="sk sk-line" style="width: 70%"></div>
      <div class="sk sk-line" style="width: 55%"></div>
      <div class="sk sk-line" style="width: 35%"></div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  count: { type: Number, default: 3 },
})
</script>

<style scoped>
.skeleton-list {
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.skeleton-card {
  background: var(--bg-card);
  border-radius: var(--radius-md);
  padding: var(--space-card-pad);
  box-shadow: var(--shadow-card);
}

.sk-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.sk {
  background: linear-gradient(
    90deg,
    var(--surface-container-high) 25%,
    var(--surface-container-highest) 50%,
    var(--surface-container-high) 75%
  );
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.4s ease-in-out infinite;
  border-radius: 6px;
}

.sk-title { height: 18px; }
.sk-line { height: 13px; margin-bottom: 10px; }
.sk-line:last-child { margin-bottom: 0; }

@keyframes skeleton-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
