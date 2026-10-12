import { http } from '@shared/api/http'
import type { Paginated } from '@shared/types/pagination'
import { paginatedProductSchema, productSchema } from './schema'
import type {
  CatalogProductListParams,
  Product,
  SellerProductListParams,
  SellerProductPatch,
} from './types'

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

export async function publishProduct(id: number): Promise<Product> {
  const { data } = await http.post(`/seller/products/${id}/publish`)
  return productSchema.parse(data)
}

export async function hideProduct(id: number): Promise<Product> {
  const { data } = await http.post(`/seller/products/${id}/hide`)
  return productSchema.parse(data)
}
