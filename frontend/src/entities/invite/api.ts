import { http } from '@shared/api/http'
import type { Invite } from './types'

/** The currently live invite link, or null if none has been generated yet
 *  (or the last one was already redeemed/superseded). */
export async function getActiveInvite(): Promise<Invite | null> {
  const { data } = await http.get<Invite | null>('/seller/invites')
  return data
}

/** Generates a new invite link, invalidating any previous one. */
export async function createInvite(): Promise<Invite> {
  const { data } = await http.post<Invite>('/seller/invites')
  return data
}

/** Redeems an invite token for the *currently logged-in* user, promoting
 *  them to moderator. */
export async function redeemInvite(token: string): Promise<void> {
  await http.post('/invites/redeem', { token })
}
