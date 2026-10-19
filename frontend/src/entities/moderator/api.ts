import { http } from '@shared/api/http'
import type { Moderator } from './types'

export async function getModerators(): Promise<Moderator[]> {
  const { data } = await http.get<Moderator[]>('/seller/moderators')
  return data
}

export async function removeModerator(userId: number): Promise<void> {
  await http.delete(`/seller/moderators/${userId}`)
}
