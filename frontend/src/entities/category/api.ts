import { http } from '@shared/api/http'
import { categoryListSchema, categorySchema } from './schema'
import type { Category } from './types'

export async function getCatalogCategories(): Promise<Category[]> {
  const { data } = await http.get('/catalog/categories')
  return categoryListSchema.parse(data)
}

export async function getSellerCategories(): Promise<Category[]> {
  const { data } = await http.get('/seller/categories')
  return categoryListSchema.parse(data)
}

export async function setCategoryVisibility(id: number, isHidden: boolean): Promise<Category> {
  const { data } = await http.patch(`/seller/categories/${id}/visibility`, {
    is_hidden: isHidden,
  })
  return categorySchema.parse(data)
}
