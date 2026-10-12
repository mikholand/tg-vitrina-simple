import { http } from '@shared/api/http'
import { loginResponseSchema, meResponseSchema } from './schema'
import type { LoginResponse, User } from './types'

export async function loginTelegram(initData: string): Promise<LoginResponse> {
  const { data } = await http.post('/auth/telegram/login', { init_data: initData })
  return loginResponseSchema.parse(data)
}

export async function fetchMe(): Promise<User> {
  const { data } = await http.get('/auth/me')
  return meResponseSchema.parse(data)
}
