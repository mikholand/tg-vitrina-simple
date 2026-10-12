export type UserRole = 'admin' | 'seller' | 'customer'

export interface User {
  id: number
  tg_username: string | null
  tg_first_name: string | null
  tg_last_name: string | null
  role: UserRole
}

export interface LoginResponse {
  token: string
  user_id: number
  role: UserRole
}
