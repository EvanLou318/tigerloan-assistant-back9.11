import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  fetchSchedules,
  createSchedule,
  updateSchedule as updateScheduleApi,
  deleteSchedule as deleteScheduleApi,
} from '../api/schedules'

export const useScheduleStore = defineStore('schedule', () => {
  const schedules = ref([])
  const searchKeyword = ref('')
  const activeTab = ref('today') // today | all | done
  const loaded = ref(false)
  const loading = ref(false)

  // 从后端加载日程列表（force=true 强制刷新）
  async function loadSchedules(force = false) {
    if (loading.value) return
    if (loaded.value && !force) return
    loading.value = true
    try {
      schedules.value = await fetchSchedules()
      loaded.value = true
    } finally {
      loading.value = false
    }
  }

  // 今日日程（按开始时间升序）
  const todaySchedules = computed(() => {
    const start = new Date()
    start.setHours(0, 0, 0, 0)
    const end = new Date(start)
    end.setDate(end.getDate() + 1)
    return schedules.value
      .filter((s) => {
        const t = new Date(s.startTime)
        return t >= start && t < end && !s.done
      })
      .sort((a, b) => new Date(a.startTime) - new Date(b.startTime))
  })

  // 全部未完成
  const pendingSchedules = computed(() => {
    return [...schedules.value]
      .filter((s) => !s.done)
      .sort((a, b) => new Date(a.startTime) - new Date(b.startTime))
  })

  // 已完成
  const doneSchedules = computed(() => {
    return [...schedules.value]
      .filter((s) => s.done)
      .sort((a, b) => new Date(b.startTime) - new Date(a.startTime))
  })

  // 按显示列表
  const displaySchedules = computed(() => {
    if (activeTab.value === 'today') return todaySchedules.value
    if (activeTab.value === 'done') return doneSchedules.value
    return pendingSchedules.value
  })

  // 今日数量（用于首页概览）
  const todayCount = computed(() => todaySchedules.value.length)
  const pendingCount = computed(() => pendingSchedules.value.length)
  const overdueCount = computed(() => {
    const now = new Date()
    return schedules.value.filter(
      (s) => !s.done && new Date(s.endTime) < now
    ).length
  })

  async function addSchedule(data) {
    const newSch = await createSchedule(data)
    schedules.value.unshift(newSch)
    return newSch
  }

  async function updateSchedule(id, data) {
    const updated = await updateScheduleApi(id, data)
    const idx = schedules.value.findIndex((s) => s.id === id)
    if (idx !== -1) schedules.value[idx] = updated
    return updated
  }

  async function toggleDone(id) {
    const sch = schedules.value.find((s) => s.id === id)
    if (!sch) return
    const updated = await updateScheduleApi(id, { done: !sch.done })
    const idx = schedules.value.findIndex((s) => s.id === id)
    if (idx !== -1) schedules.value[idx] = updated
  }

  async function deleteSchedule(id) {
    await deleteScheduleApi(id)
    schedules.value = schedules.value.filter((s) => s.id !== id)
  }

  return {
    schedules,
    searchKeyword,
    activeTab,
    loaded,
    loading,
    todaySchedules,
    pendingSchedules,
    doneSchedules,
    displaySchedules,
    todayCount,
    pendingCount,
    overdueCount,
    loadSchedules,
    addSchedule,
    updateSchedule,
    toggleDone,
    deleteSchedule,
  }
})
