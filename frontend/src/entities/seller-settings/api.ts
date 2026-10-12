import { http } from '@shared/api/http'
import type { SellerSettings, SellerSettingsUpdatePayload, SellerStats } from './types'

export async function getSellerSettings(): Promise<SellerSettings> {
  const { data } = await http.get<SellerSettings>('/seller/settings')
  return data
}

export async function updateSellerSettings(
  payload: SellerSettingsUpdatePayload,
): Promise<SellerSettings> {
  const { data } = await http.patch<SellerSettings>('/seller/settings', payload)
  return data
}

export async function uploadStoreLogo(file: File): Promise<SellerSettings> {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await http.post<SellerSettings>('/seller/settings/logo', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function getSellerStats(topLimit?: number): Promise<SellerStats> {
  const { data } = await http.get<SellerStats>('/seller/stats', {
    params: topLimit !== undefined ? { top_limit: topLimit } : undefined,
  })
  return data
}
