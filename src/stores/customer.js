import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  fetchCustomers,
  createCustomer,
  updateCustomer as updateCustomerApi,
  deleteCustomer as deleteCustomerApi,
  addMaterial as addMaterialApi,
  removeMaterial as removeMaterialApi,
  updateMaterial as updateMaterialApi,
  fetchSimulations,
  createSimulation,
  deleteSimulation as deleteSimulationApi,
} from '../api/customers'

export const useCustomerStore = defineStore('customer', () => {
  const customers = ref([])
  const simulations = ref([])
  const searchKeyword = ref('')
  const loaded = ref(false)
  const loading = ref(false)

  // 从后端加载客户列表（force=true 强制刷新）
  async function loadCustomers(force = false) {
    if (loading.value) return
    if (loaded.value && !force) return
    loading.value = true
    try {
      customers.value = await fetchCustomers()
      loaded.value = true
    } finally {
      loading.value = false
    }
  }

  // 加载某客户的推演历史
  async function loadSimulations(customerId) {
    if (!customerId) return []
    simulations.value = await fetchSimulations(customerId)
    return simulations.value
  }

  const filteredCustomers = computed(() => {
    let result = customers.value
    if (searchKeyword.value) {
      const kw = searchKeyword.value.toLowerCase()
      result = result.filter(
        (c) =>
          c.name.toLowerCase().includes(kw) ||
          c.phone.includes(kw)
      )
    }
    return [...result].sort((a, b) => b.createdAt.localeCompare(a.createdAt))
  })

  function getCustomerById(id) {
    return customers.value.find((c) => c.id === id)
  }

  async function addCustomer(data) {
    const newCustomer = await createCustomer(data)
    customers.value.unshift(newCustomer)
    return newCustomer
  }

  async function updateCustomer(id, data) {
    const updated = await updateCustomerApi(id, data)
    const idx = customers.value.findIndex((c) => c.id === id)
    if (idx !== -1) customers.value[idx] = updated
    return updated
  }

  // 合并 AI 提取字段到客户档案（只覆盖本次确认的字段）
  async function mergeCustomerFields(id, fields) {
    return updateCustomer(id, fields)
  }

  async function deleteCustomer(id) {
    await deleteCustomerApi(id)
    customers.value = customers.value.filter((c) => c.id !== id)
  }

  async function addMaterial(customerId, material) {
    const created = await addMaterialApi(customerId, material)
    const customer = getCustomerById(customerId)
    if (customer) {
      customer.materials = customer.materials || []
      customer.materials.unshift(created)
      customer.updatedAt = created.time
    }
    return created
  }

  // 删除客户材料
  async function removeMaterial(customerId, materialId) {
    await removeMaterialApi(customerId, materialId)
    const customer = getCustomerById(customerId)
    if (customer) {
      customer.materials = customer.materials.filter((m) => m.id !== materialId)
    }
  }

  // 修改材料类型（AI 识别错误时更正）
  async function updateMaterialType(customerId, materialId, newType) {
    const updated = await updateMaterialApi(customerId, materialId, { type: newType })
    const customer = getCustomerById(customerId)
    if (customer) {
      const idx = customer.materials.findIndex((m) => m.id === materialId)
      if (idx !== -1) customer.materials[idx] = { ...customer.materials[idx], ...updated }
    }
    return updated
  }

  function getSimulationsByCustomerId(customerId) {
    return simulations.value
      .filter((s) => s.customerId === customerId)
      .sort((a, b) => b.createdAt.localeCompare(a.createdAt))
  }

  async function addSimulation(data) {
    const newSim = await createSimulation(data.customerId, data)
    simulations.value.unshift(newSim)
    return newSim
  }

  async function deleteSimulation(customerId, id) {
    await deleteSimulationApi(customerId, id)
    simulations.value = simulations.value.filter((s) => s.id !== id)
  }

  return {
    customers,
    simulations,
    searchKeyword,
    loaded,
    loading,
    filteredCustomers,
    getCustomerById,
    loadCustomers,
    loadSimulations,
    addCustomer,
    updateCustomer,
    mergeCustomerFields,
    deleteCustomer,
    addMaterial,
    removeMaterial,
    updateMaterialType,
    getSimulationsByCustomerId,
    addSimulation,
    deleteSimulation,
  }
})
