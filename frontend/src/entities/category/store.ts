import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { getCatalogCategories } from './api'
import type { Category, CategoryTreeNode } from './types'

function sortTree(nodes: CategoryTreeNode[]): void {
  nodes.sort((a, b) => a.sort_order - b.sort_order)
  for (const node of nodes) sortTree(node.children)
}

function buildTree(categories: Category[]): CategoryTreeNode[] {
  const nodesById = new Map<number, CategoryTreeNode>()
  for (const category of categories) {
    nodesById.set(category.id, { ...category, children: [] })
  }

  const roots: CategoryTreeNode[] = []
  for (const node of nodesById.values()) {
    const parent = node.parent_id !== null ? nodesById.get(node.parent_id) : undefined
    if (parent) {
      parent.children.push(node)
    } else {
      roots.push(node)
    }
  }

  sortTree(roots)
  return roots
}

export const useCategoryStore = defineStore('category', () => {
  const categories = ref<Category[]>([])
  const loaded = ref(false)

  const tree = computed<CategoryTreeNode[]>(() => buildTree(categories.value))

  async function fetchCategories(force = false): Promise<void> {
    if (loaded.value && !force) return
    categories.value = await getCatalogCategories()
    loaded.value = true
  }

  return { categories, tree, loaded, fetchCategories }
})
