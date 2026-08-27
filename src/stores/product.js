import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  fetchProducts,
  createProduct,
  updateProduct as updateProductApi,
  toggleProductStatus,
  deleteProduct as deleteProductApi,
} from '../api/products'

export const useProductStore = defineStore('product', () => {
  const products = ref([])
  const searchKeyword = ref('')
  const filterStatus = ref('') // '', 'active', 'disabled'
  const loaded = ref(false)
  const loading = ref(false)

  // 从后端加载产品列表（force=true 强制刷新）
  async function loadProducts(force = false) {
    if (loading.value) return
    if (loaded.value && !force) return
    loading.value = true
    try {
      products.value = await fetchProducts()
      loaded.value = true
    } finally {
      loading.value = false
    }
  }

  const filteredProducts = computed(() => {
    let result = products.value
    if (searchKeyword.value) {
      const kw = searchKeyword.value.toLowerCase()
      result = result.filter(
        (p) =>
          p.productName.toLowerCase().includes(kw) ||
          p.institution.toLowerCase().includes(kw)
      )
    }
    if (filterStatus.value) {
      result = result.filter((p) => p.status === filterStatus.value)
    }
    return [...result].sort((a, b) => b.createdAt.localeCompare(a.createdAt))
  })

  const activeCount = computed(() => products.value.filter((p) => p.status === 'active').length)

  function getProductById(id) {
    return products.value.find((p) => p.id === id)
  }

  async function addProduct(data) {
    const newProduct = await createProduct(data)
    products.value.unshift(newProduct)
    return newProduct
  }

  async function updateProduct(id, data) {
    const updated = await updateProductApi(id, data)
    const idx = products.value.findIndex((p) => p.id === id)
    if (idx !== -1) products.value[idx] = updated
    return updated
  }

  async function deleteProduct(id) {
    await deleteProductApi(id)
    products.value = products.value.filter((p) => p.id !== id)
  }

  async function toggleStatus(id) {
    const product = getProductById(id)
    if (!product) return
    const next = product.status === 'active' ? 'disabled' : 'active'
    const updated = await toggleProductStatus(id, next)
    const idx = products.value.findIndex((p) => p.id === id)
    if (idx !== -1) products.value[idx] = updated
  }

  return {
    products,
    searchKeyword,
    filterStatus,
    loaded,
    loading,
    filteredProducts,
    activeCount,
    getProductById,
    loadProducts,
    addProduct,
    updateProduct,
    deleteProduct,
    toggleStatus,
  }
})
