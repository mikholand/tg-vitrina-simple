import { http } from '@shared/api/http'
import { bannerListSchema, bannerSchema } from './schema'
import type { Banner, BannerUpdatePayload } from './types'

export async function getCatalogBanners(): Promise<Banner[]> {
  const { data } = await http.get('/catalog/banners')
  return bannerListSchema.parse(data)
}

export async function getSellerBanners(): Promise<Banner[]> {
  const { data } = await http.get('/seller/banners')
  return bannerListSchema.parse(data)
}

export async function createBanner(file: File): Promise<Banner> {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await http.post('/seller/banners', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return bannerSchema.parse(data)
}

export async function updateBanner(id: number, payload: BannerUpdatePayload): Promise<Banner> {
  const { data } = await http.patch(`/seller/banners/${id}`, payload)
  return bannerSchema.parse(data)
}

export async function deleteBanner(id: number): Promise<void> {
  await http.delete(`/seller/banners/${id}`)
}
