import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import type { Product } from '@entities/product/types'
import { getCatalogProduct } from '@entities/product/api'
import { checkout as checkoutRequest } from './api'
import type { Order } from './types'

const STORAGE_KEY = 'vitrina:cart:v1'

function readLines(): Map<number, number> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return new Map()
    const parsed: unknown = JSON.parse(raw)
    if (!Array.isArray(parsed)) return new Map()
    const entries = parsed.filter(
      (entry): entry is [number, number] =>
        Array.isArray(entry) &&
        entry.length === 2 &&
        typeof entry[0] === 'number' &&
        typeof entry[1] === 'number' &&
        entry[1] > 0,
    )
    return new Map(entries)
  } catch {
    return new Map()
  }
}

function writeLines(lines: Map<number, number>): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(Array.from(lines.entries())))
}

/**
 * Unlike `favorite/store.ts`, the cart never syncs to the backend per-action
 * — it's a purely local draft (localStorage, same as an anonymous visitor's
 * favorites) until the single `checkout()` call at the very end that posts
 * the whole thing to `POST /catalog/orders` and, on success, clears it.
 * There is no per-user server-side cart to merge on login.
 */
export const useCartStore = defineStore('cart', () => {
  const lines = ref<Map<number, number>>(readLines())
  // Full product details for whatever's currently in `lines` — loaded on
  // demand via `fetchCartProducts()` (the cart page, mainly), since only
  // ids+quantities are persisted locally.
  const products = ref<Product[]>([])

  const itemsCount = computed(() =>
    Array.from(lines.value.values()).reduce((sum, quantity) => sum + quantity, 0),
  )

  function quantityOf(productId: number): number {
    return lines.value.get(productId) ?? 0
  }

  function setQuantity(productId: number, quantity: number): void {
    const next = new Map(lines.value)
    if (quantity <= 0) {
      next.delete(productId)
      // Drops the now-stale product from the resolved-details list too —
      // without this, a line removed down to 0 on the cart page (where
      // `products` drives the rendered rows) would keep showing a ghost
      // row stuck at quantity 0 until the next `fetchCartProducts()` call.
      products.value = products.value.filter((product) => product.id !== productId)
    } else {
      next.set(productId, quantity)
    }
    lines.value = next
    writeLines(next)
  }

  function addItem(productId: number, quantity = 1): void {
    setQuantity(productId, quantityOf(productId) + quantity)
  }

  function removeItem(productId: number): void {
    setQuantity(productId, 0)
  }

  function clear(): void {
    lines.value = new Map()
    products.value = []
    localStorage.removeItem(STORAGE_KEY)
  }

  /**
   * Resolves product details for every line in the cart. Any id that no
   * longer resolves (product deleted/unpublished since it was added) is
   * silently dropped from the cart too — there's nothing to show or price
   * for it, and checkout would just reject it as `product_unavailable`
   * anyway.
   */
  async function fetchCartProducts(): Promise<void> {
    const ids = Array.from(lines.value.keys())
    const resolved = await Promise.all(ids.map((id) => getCatalogProduct(id).catch(() => null)))
    products.value = resolved.filter((product): product is Product => product !== null)

    const resolvedIds = new Set(products.value.map((product) => product.id))
    if (resolvedIds.size !== lines.value.size) {
      const pruned = new Map(
        Array.from(lines.value.entries()).filter(([productId]) => resolvedIds.has(productId)),
      )
      lines.value = pruned
      writeLines(pruned)
    }
  }

  const total = computed(() => {
    let sum = 0
    for (const product of products.value) {
      const price = product.price ? Number(product.price) : 0
      sum += price * quantityOf(product.id)
    }
    return sum
  })

  /** Posts the cart as an order, then clears it on success. Throws (and
   * leaves the cart untouched) on any failure — insufficient stock,
   * unavailable product, or not being logged in. */
  async function submitOrder(comment: string | null): Promise<Order> {
    const items = Array.from(lines.value.entries()).map(([product_id, quantity]) => ({
      product_id,
      quantity,
    }))
    const order = await checkoutRequest({ items, comment })
    clear()
    return order
  }

  return {
    lines,
    products,
    itemsCount,
    total,
    quantityOf,
    addItem,
    setQuantity,
    removeItem,
    clear,
    fetchCartProducts,
    submitOrder,
  }
})
