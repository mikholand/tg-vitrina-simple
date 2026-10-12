import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getCatalogBanners } from './api'
import type { Banner } from './types'

export const useBannerStore = defineStore('banner', () => {
  const banners = ref<Banner[]>([])
  const loaded = ref(false)

  async function fetchBanners(force = false): Promise<void> {
    if (loaded.value && !force) return
    try {
      banners.value = await getCatalogBanners()
    } catch {
      banners.value = []
    }
    loaded.value = true
  }

  return { banners, loaded, fetchBanners }
})
