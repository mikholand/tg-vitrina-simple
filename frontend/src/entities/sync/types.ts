export type SyncStatus = 'idle' | 'requested' | 'running' | 'done' | 'failed' | 'interrupted'

export interface SyncState {
  status: SyncStatus
  cursor: number | null
  stop_id: number | null
  done_count: number
  total_count: number | null
  attempts: number
  retry_at: string | null
  stop_requested: boolean
  last_error: string | null
  updated_at: string
}
