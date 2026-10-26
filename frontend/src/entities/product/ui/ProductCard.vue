<script setup lang="ts">
import type { Product } from '@entities/product/types'
import { availabilityChipClasses, availabilityLabels, formatPrice } from '@entities/product/labels'
import { isOutOfStock, maxCartQuantity, shouldShowQuantity } from '@entities/product/stock'
import { useFavoriteStore } from '@entities/favorite/store'
import { useCartStore } from '@entities/cart/store'

// Tint placeholders: colour is pinned to the product id, so the same
// product always looks the same and an image-less grid doesn't read as
// grey/broken. Cool blue-grey tones, matching the rest of the storefront.
const TINTS = ['bg-[#eff4ff]', 'bg-[#f1f5f9]', 'bg-[#f5f8ff]', 'bg-[#eef2f7]', 'bg-[#e8eef7]']

const props = defineProps<{ product: Product }>()

const favoriteStore = useFavoriteStore()
const cartStore = useCartStore()

const isFavorite = computed(() => favoriteStore.isFavorite(props.product.id))
const thumbnail = computed(() => props.product.photo_paths[0] ?? null)
const tint = computed(() => TINTS[props.product.id % TINTS.length])
const initial = computed(() => props.product.name[0]?.toUpperCase() ?? '')

const showAvailability = computed(() => props.product.availability !== 'unknown')

const availabilityLabel = computed(() => {
  const label = availabilityLabels[props.product.availability]
  return shouldShowQuantity(props.product) ? `${label} · ${props.product.quantity} шт.` : label
})

const outOfStock = computed(() => isOutOfStock(props.product))
const cartQuantity = computed(() => cartStore.quantityOf(props.product.id))

async function onToggleFavorite(event: Event): Promise<void> {
  event.preventDefault()
  event.stopPropagation()
  await favoriteStore.toggleFavorite(props.product.id)
}

function onAddToCart(event: Event): void {
  event.preventDefault()
  event.stopPropagation()
  const max = maxCartQuantity(props.product)
  if (max !== null && cartQuantity.value >= max) return
  cartStore.addItem(props.product.id)
}
</script>

<template>
  <RouterLink
    :to="`/product/${product.id}`"
    class="flex flex-col rounded-3xl border border-sf-line bg-sf-card p-2"
  >
    <div class="relative aspect-square overflow-hidden rounded-[1.15rem]" :class="tint">
      <img
        v-if="thumbnail"
        :src="thumbnail"
        :alt="product.name"
        class="size-full object-cover"
        loading="lazy"
      />
      <div
        v-else
        class="flex size-full items-center justify-center text-3xl font-semibold text-sf-disabled"
      >
        {{ initial }}
      </div>

      <button
        type="button"
        class="absolute right-2 top-2 flex size-8 items-center justify-center rounded-full bg-white/85 backdrop-blur"
        :aria-label="isFavorite ? 'Убрать из избранного' : 'В избранное'"
        @click="onToggleFavorite"
      >
        <i
          class="pi text-sm"
          :class="isFavorite ? 'pi-heart-fill text-sf-danger' : 'pi-heart text-sf-muted'"
        />
      </button>

      <button
        v-if="!outOfStock"
        type="button"
        class="absolute bottom-2 right-2 flex size-8 items-center justify-center rounded-full bg-white/85 backdrop-blur"
        aria-label="В корзину"
        @click="onAddToCart"
      >
        <i
          class="pi pi-shopping-cart text-sm"
          :class="cartQuantity > 0 ? 'text-sf-accent' : 'text-sf-muted'"
        />
        <span
          v-if="cartQuantity > 0"
          class="absolute -right-1 -top-1 flex min-w-4 items-center justify-center rounded-full bg-sf-danger px-1 text-[0.6rem] font-semibold leading-4 text-white"
        >
          {{ cartQuantity }}
        </span>
      </button>
    </div>

    <div class="flex flex-1 flex-col gap-1 px-1.5 pb-1 pt-2">
      <p class="line-clamp-2 text-sm leading-tight text-sf-ink">{{ product.name }}</p>
      <p class="mt-auto pt-1 font-semibold text-sf-ink">
        {{ formatPrice(product.price, product.currency) }}
      </p>
      <span
        v-if="showAvailability"
        class="w-fit rounded-full px-2 py-0.5 text-[0.65rem]"
        :class="availabilityChipClasses[product.availability]"
      >
        {{ availabilityLabel }}
      </span>
    </div>
  </RouterLink>
</template>
