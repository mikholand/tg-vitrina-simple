import { z } from 'zod'
import { http } from '@shared/api/http'
import { productSchema } from '@entities/product/schema'
import type { Product } from '@entities/product/types'
import type { MergeFavoritesPayload } from './types'

const favoriteListSchema = z.array(productSchema)

export async function getFavorites(): Promise<Product[]> {
  const { data } = await http.get('/favorites')
  return favoriteListSchema.parse(data)
}

export async function addFavorite(productId: number): Promise<void> {
  await http.put(`/favorites/${productId}`)
}

export async function removeFavorite(productId: number): Promise<void> {
  await http.delete(`/favorites/${productId}`)
}

export async function mergeFavorites(payload: MergeFavoritesPayload): Promise<void> {
  await http.post('/favorites/merge', payload)
}
