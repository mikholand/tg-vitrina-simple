import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { clearAccessToken, getAccessToken, setAccessToken } from '@shared/api/http'
import { getInitDataRaw } from '@shared/telegram/sdk'
import { useFavoriteStore } from '@entities/favorite/store'
import { fetchMe as fetchMeRequest, loginTelegram } from './api'
import type { User } from './types'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(getAccessToken())
  const currentUser = ref<User | null>(null)

  const role = computed(() => currentUser.value?.role ?? null)

  async function fetchMe(): Promise<void> {
    currentUser.value = await fetchMeRequest()
  }

  /**
   * Attempts a silent login using Telegram WebApp init data. No-ops when
   * init data is unavailable (e.g. running outside Telegram). On success,
   * merges any anonymous favorites accumulated before login.
   */
  async function loginWithTelegram(): Promise<void> {
    const initData = getInitDataRaw()
    if (!initData) return

    const response = await loginTelegram(initData)
    token.value = response.token
    setAccessToken(response.token)

    await fetchMe()

    const favoriteStore = useFavoriteStore()
    await favoriteStore.mergeOnLogin()
  }

  function logout(): void {
    token.value = null
    currentUser.value = null
    clearAccessToken()
  }

  return { token, currentUser, role, fetchMe, loginWithTelegram, logout }
})
