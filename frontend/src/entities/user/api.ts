import { http } from '@shared/api/http'
import { loginResponseSchema, meResponseSchema } from './schema'
import type { LoginResponse, User } from './types'

export async function loginTelegram(initData: string): Promise<LoginResponse> {
  const { data } = await http.post('/auth/telegram/login', { init_data: initData })
  return loginResponseSchema.parse(data)
}

/** The website login path (Telegram's OIDC Login Widget) — counterpart to
 * `loginTelegram` above, which only works inside the Mini App. The backend
 * re-verifies `idToken` itself against Telegram's public keys, so nothing
 * from the widget is trusted client-side. Response shape is identical to
 * `loginTelegram`'s, so it reuses the same schema/parse step. */
export async function loginTelegramWidget(idToken: string): Promise<LoginResponse> {
  const { data } = await http.post('/auth/telegram/widget', { id_token: idToken })
  return loginResponseSchema.parse(data)
}

export async function fetchMe(): Promise<User> {
  const { data } = await http.get('/auth/me')
  return meResponseSchema.parse(data)
}
