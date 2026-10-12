export type RawPostStatus = 'new' | 'extracted' | 'failed'

export interface RawPost {
  id: number
  channel_id: number
  message_id: number
  media_group_id: number | null
  raw_text: string | null
  photo_paths: string[]
  posted_at: string
  status: RawPostStatus
  product_id: number | null
  created_at: string
}

export interface RawPostListParams {
  status?: RawPostStatus
  limit?: number
  offset?: number
}
