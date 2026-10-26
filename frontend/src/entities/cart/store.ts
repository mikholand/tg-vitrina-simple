import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import type { Product } from '@entities/product/types'
import { getCatalogProduct } from '@entities/product/api'
import { maxCartQuantity } from '@entities/product/stock'
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
   * Resolves product details for every line in the cart, then reconciles
   * against live stock/availability: a line whose product no longer
   * resolves (deleted/unpublished since it was added) is dropped — nothing
   * to show or price for it — and a line that now exceeds what can
   * actually be ordered (sold out, or the seller flipped it to "нет в
   * наличии" since it was added) is clamped down to `maxCartQuantity`
   * rather than left to just error at checkout. Mirrors the same cap
   * ProductCard.vue/ProductDetailPage.vue enforce when adding.
   */
  async function fetchCartProducts(): Promise<void> {
    const ids = Array.from(lines.value.keys())
    const resolved = await Promise.all(ids.map((id) => getCatalogProduct(id).catch(() => null)))
    const byId = new Map(
      resolved.filter((product): product is Product => product !== null).map((p) => [p.id, p]),
    )

    let changed = byId.size !== lines.value.size
    const next = new Map<number, number>()
    for (const [productId, quantity] of lines.value) {
      const product = byId.get(productId)
      if (!product) continue
      const max = maxCartQuantity(product)
      const clamped = max === null ? quantity : Math.min(quantity, max)
      if (clamped <= 0) {
        changed = true
        continue
      }
      if (clamped !== quantity) changed = true
      next.set(productId, clamped)
    }

    products.value = Array.from(byId.values()).filter((product) => next.has(product.id))
    if (changed) {
      lines.value = next
      writeLines(next)
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
   * unavailable product, or (checkout outside Telegram, with no
   * contactName/contactPhone) a missing contact. */
  async function submitOrder(
    comment: string | null,
    contactName?: string | null,
    contactPhone?: string | null,
  ): Promise<Order> {
    const items = Array.from(lines.value.entries()).map(([product_id, quantity]) => ({
      product_id,
      quantity,
    }))
    const order = await checkoutRequest({
      items,
      comment,
      contact_name: contactName,
      contact_phone: contactPhone,
    })
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
