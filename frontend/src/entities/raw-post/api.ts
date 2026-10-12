import { http } from '@shared/api/http'
import type { Paginated } from '@shared/types/pagination'
import { paginatedRawPostSchema, rawPostSchema } from './schema'
import type { RawPost, RawPostListParams } from './types'

export async function getRawPosts(params: RawPostListParams = {}): Promise<Paginated<RawPost>> {
  const { data } = await http.get('/seller/raw-posts', { params })
  return paginatedRawPostSchema.parse(data)
}

export async function getRawPost(id: number): Promise<RawPost> {
  const { data } = await http.get(`/seller/raw-posts/${id}`)
  return rawPostSchema.parse(data)
}
