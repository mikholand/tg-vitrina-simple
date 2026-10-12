import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { getVisitorKey } from './visitor'
import { getInitDataRaw } from '@shared/telegram/sdk'

const ACCESS_TOKEN_KEY = 'access_token'

export function getAccessToken(): string | null {
  return sessionStorage.getItem(ACCESS_TOKEN_KEY)
}

export function setAccessToken(token: string): void {
  sessionStorage.setItem(ACCESS_TOKEN_KEY, token)
}

export function clearAccessToken(): void {
  sessionStorage.removeItem(ACCESS_TOKEN_KEY)
}

export const http = axios.create({
  baseURL: '/api/v1',
})

http.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  } else {
    config.headers['X-Visitor-Key'] = getVisitorKey()
  }
  return config
})

interface LoginResponse {
  token: string
  user_id: number
  role: 'admin' | 'seller' | 'customer'
}

let reloginPromise: Promise<string | null> | null = null

/**
 * Attempts to (re)authenticate via Telegram WebApp initData. Returns the new
 * access token on success, or null if initData is unavailable / the request
 * fails.
 */
async function reloginViaTelegram(): Promise<string | null> {
  const initData = getInitDataRaw()
  if (!initData) return null

  try {
    const { data } = await axios.post<LoginResponse>('/api/v1/auth/telegram/login', {
      init_data: initData,
    })
    setAccessToken(data.token)
    return data.token
  } catch {
    return null
  }
}

http.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as (InternalAxiosRequestConfig & { _retried?: boolean }) | undefined

    if (error.response?.status === 401 && originalRequest && !originalRequest._retried) {
      originalRequest._retried = true

      if (!reloginPromise) {
        reloginPromise = reloginViaTelegram().finally(() => {
          reloginPromise = null
        })
      }

      const newToken = await reloginPromise
      if (newToken) {
        originalRequest.headers.Authorization = `Bearer ${newToken}`
        return http(originalRequest)
      }
    }

    return Promise.reject(error)
  },
)
