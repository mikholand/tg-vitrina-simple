import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import type { Product } from '@entities/product/types'
import { useAuthStore } from '@entities/user/store'
import { addFavorite, getFavorites, mergeFavorites, removeFavorite } from './api'

const STORAGE_KEY = 'vitrina:favorites:v1'
const MAX_ANONYMOUS_FAVORITES = 100

function readLocalIds(): Set<number> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return new Set()
    const parsed: unknown = JSON.parse(raw)
    if (!Array.isArray(parsed)) return new Set()
    return new Set(parsed.filter((value): value is number => typeof value === 'number'))
  } catch {
    return new Set()
  }
}

function writeLocalIds(ids: Set<number>): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(Array.from(ids)))
}

function clearLocalIds(): void {
  localStorage.removeItem(STORAGE_KEY)
}

export const useFavoriteStore = defineStore('favorite', () => {
  const ids = ref<Set<number>>(new Set())
  const products = ref<Product[]>([])

  const count = computed(() => ids.value.size)

  function isFavorite(productId: number): boolean {
    return ids.value.has(productId)
  }

  /**
   * Loads the current favorite ids: the server list when authenticated,
   * otherwise the locally persisted anonymous ids (no product data fetched
   * for the anonymous case).
   */
  async function fetchFavorites(): Promise<void> {
    const authStore = useAuthStore()
    if (authStore.token) {
      products.value = await getFavorites()
      ids.value = new Set(products.value.map((product) => product.id))
    } else {
      products.value = []
      ids.value = readLocalIds()
    }
  }

  async function toggleFavorite(productId: number): Promise<void> {
    const authStore = useAuthStore()
    const previousIds = ids.value
    const wasFavorite = previousIds.has(productId)

    let nextIds = new Set(previousIds)
    if (wasFavorite) {
      nextIds.delete(productId)
    } else {
      nextIds.add(productId)
    }

    if (!authStore.token && !wasFavorite && nextIds.size > MAX_ANONYMOUS_FAVORITES) {
      nextIds = new Set(Array.from(nextIds).slice(-MAX_ANONYMOUS_FAVORITES))
    }

    ids.value = nextIds

    if (authStore.token) {
      try {
        if (wasFavorite) {
          await removeFavorite(productId)
        } else {
          await addFavorite(productId)
        }
      } catch (error) {
        ids.value = previousIds
        throw error
      }
    } else {
      writeLocalIds(nextIds)
    }
  }

  /**
   * Merges anonymous (localStorage) favorites into the server-backed list
   * right after login, then clears local storage and reloads from the
   * server. Safe to call even when there were no local favorites.
   */
  async function mergeOnLogin(): Promise<void> {
    const localIds = readLocalIds()
    if (localIds.size > 0) {
      await mergeFavorites({ product_ids: Array.from(localIds) })
      clearLocalIds()
    }
    await fetchFavorites()
  }

  return { ids, products, count, isFavorite, fetchFavorites, toggleFavorite, mergeOnLogin }
})
