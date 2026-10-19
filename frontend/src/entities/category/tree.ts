import type { Category, CategoryTreeNode } from './types'

function sortTree(nodes: CategoryTreeNode[]): void {
  nodes.sort((a, b) => a.sort_order - b.sort_order)
  for (const node of nodes) sortTree(node.children)
}

/**
 * Turns the flat, parent_id-linked list the API returns into a nested tree,
 * sorted by sort_order at every level.
 *
 * Shared by the customer-facing category store (breadcrumbs on the product
 * page) and the seller categories page, which renders it as a collapsible
 * tree — same shape tg-vitrina's admin view works from.
 */
export function buildCategoryTree(categories: Category[]): CategoryTreeNode[] {
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
