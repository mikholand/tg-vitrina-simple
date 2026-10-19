import { http } from '@shared/api/http'
import type { Paginated } from '@shared/types/pagination'
import { paginatedProductSchema, productSchema } from './schema'
import type {
  CatalogProductListParams,
  Product,
  SellerProductCreate,
  SellerProductListParams,
  SellerProductPatch,
} from './types'

/** Mirrors backend MAX_PHOTO_BYTES (app/shared/uploads.py) — checked before
 * upload so an oversized file is rejected locally instead of after a slow
 * upload only to be bounced by the server's 413. */
export const MAX_PHOTO_BYTES = 5 * 1024 * 1024
/** Mirrors backend MAX_VIDEO_BYTES. */
export const MAX_VIDEO_BYTES = 50 * 1024 * 1024
/** Mirrors the client-only cap tg-vitrina's own editor enforces (no backend limit on count, just UX). */
export const MAX_PHOTOS = 10

export async function getCatalogProducts(
  params: CatalogProductListParams = {},
): Promise<Paginated<Product>> {
  const { data } = await http.get('/catalog/products', { params })
  return paginatedProductSchema.parse(data)
}

export async function getCatalogProduct(id: number): Promise<Product> {
  const { data } = await http.get(`/catalog/products/${id}`)
  return productSchema.parse(data)
}

export async function getSellerProducts(
  params: SellerProductListParams = {},
): Promise<Paginated<Product>> {
  const { data } = await http.get('/seller/products', { params })
  return paginatedProductSchema.parse(data)
}

export async function getSellerProduct(id: number): Promise<Product> {
  const { data } = await http.get(`/seller/products/${id}`)
  return productSchema.parse(data)
}

export async function createSellerProduct(payload: SellerProductCreate): Promise<Product> {
  const { data } = await http.post('/seller/products', payload)
  return productSchema.parse(data)
}

export async function updateSellerProduct(
  id: number,
  patch: SellerProductPatch,
): Promise<Product> {
  const { data } = await http.patch(`/seller/products/${id}`, patch)
  return productSchema.parse(data)
}

export async function uploadProductPhoto(id: number, file: File): Promise<Product> {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await http.post(`/seller/products/${id}/photos`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return productSchema.parse(data)
}

export async function uploadProductVideo(id: number, file: File): Promise<Product> {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await http.post(`/seller/products/${id}/video`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return productSchema.parse(data)
}

export async function publishProduct(id: number): Promise<Product> {
  const { data } = await http.post(`/seller/products/${id}/publish`)
  return productSchema.parse(data)
}

export async function hideProduct(id: number): Promise<Product> {
  const { data } = await http.post(`/seller/products/${id}/hide`)
  return productSchema.parse(data)
}

/** Permanent, media included — there is no undo. `hideProduct` is the
 * reversible way to pull a product off the storefront. */
export async function deleteProduct(id: number): Promise<void> {
  await http.delete(`/seller/products/${id}`)
}
