import { http } from '@shared/api/http'
import type { StoreInfo } from './types'

export async function getStoreInfo(): Promise<StoreInfo> {
  const { data } = await http.get<StoreInfo>('/catalog/store')
  return data
}

export async function recordVisit(): Promise<void> {
  await http.post('/catalog/visit')
}
