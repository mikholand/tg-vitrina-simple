import { http } from '@shared/api/http'
import type { SyncState } from './types'

export async function getSyncStatus(): Promise<SyncState> {
  const { data } = await http.get<SyncState>('/seller/sync')
  return data
}

export async function startSync(resume = false): Promise<SyncState> {
  const { data } = await http.post<SyncState>('/seller/sync/start', null, {
    params: { resume },
  })
  return data
}

export async function stopSync(): Promise<SyncState> {
  const { data } = await http.post<SyncState>('/seller/sync/stop')
  return data
}
