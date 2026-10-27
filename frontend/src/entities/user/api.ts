import { http } from '@shared/api/http'
import { loginResponseSchema, meResponseSchema } from './schema'
import type { LoginResponse, TelegramWidgetAuthData, User } from './types'

export async function loginTelegram(initData: string): Promise<LoginResponse> {
  const { data } = await http.post('/auth/telegram/login', { init_data: initData })
  return loginResponseSchema.parse(data)
}

/** The website login path (Telegram Login Widget) — counterpart to
 * `loginTelegram` above, which only works inside the Mini App. Response
 * shape is identical, so it reuses the same schema/parse step. */
export async function loginTelegramWidget(authData: TelegramWidgetAuthData): Promise<LoginResponse> {
  const { data } = await http.post('/auth/telegram/widget', authData)
  return loginResponseSchema.parse(data)
}

export async function fetchMe(): Promise<User> {
  const { data } = await http.get('/auth/me')
  return meResponseSchema.parse(data)
}
