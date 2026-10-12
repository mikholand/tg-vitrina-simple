import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getStoreInfo, recordVisit as recordVisitRequest } from './api'
import type { StoreInfo } from './types'

export const useStoreInfoStore = defineStore('storeInfo', () => {
  const storeInfo = ref<StoreInfo | null>(null)
  const loaded = ref(false)

  // Fetched once (App.vue's header needs it on every customer page, plus
  // Home/ProductDetail each want it too) — cached like categoryStore so
  // navigating between pages doesn't re-request it every time.
  async function fetchStoreInfo(force = false): Promise<void> {
    if (loaded.value && !force) return
    storeInfo.value = await getStoreInfo()
    loaded.value = true
  }

  /** Fire-and-forget visit tracking; failures are intentionally swallowed. */
  function recordVisit(): void {
    recordVisitRequest().catch(() => {
      // Visit tracking is best-effort — ignore network/API failures.
    })
  }

  return { storeInfo, loaded, fetchStoreInfo, recordVisit }
})
