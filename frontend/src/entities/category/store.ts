import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { getCatalogCategories } from './api'
import { buildCategoryTree } from './tree'
import type { Category, CategoryTreeNode } from './types'

export const useCategoryStore = defineStore('category', () => {
  const categories = ref<Category[]>([])
  const loaded = ref(false)

  const tree = computed<CategoryTreeNode[]>(() => buildCategoryTree(categories.value))

  async function fetchCategories(force = false): Promise<void> {
    if (loaded.value && !force) return
    categories.value = await getCatalogCategories()
    loaded.value = true
  }

  return { categories, tree, loaded, fetchCategories }
})
