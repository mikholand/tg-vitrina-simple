export interface Category {
  id: number
  parent_id: number | null
  name: string
  code: string
  sort_order: number
  depth: number
  is_fallback: boolean
  is_hidden: boolean
}

export interface CategoryTreeNode extends Category {
  children: CategoryTreeNode[]
}
