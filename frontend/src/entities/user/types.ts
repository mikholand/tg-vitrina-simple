export type UserRole = 'admin' | 'seller' | 'moderator' | 'customer'

export interface User {
  id: number
  tg_username: string | null
  tg_first_name: string | null
  tg_last_name: string | null
  tg_photo_url: string | null
  role: UserRole
}

export interface LoginResponse {
  token: string
  user_id: number
  role: UserRole
}

/** The payload Telegram's Login Widget callback hands the page verbatim —
 * see `shared/telegram/widget.ts`. Sent to `POST /auth/telegram/widget`
 * as-is; the backend re-derives the hash itself, so nothing here is
 * trusted client-side. */
export interface TelegramWidgetAuthData {
  id: number
  first_name: string
  last_name?: string
  username?: string
  photo_url?: string
  auth_date: number
  hash: string
}
