<script setup lang="ts">
import type { Product } from '@entities/product/types'
import { getCatalogProduct } from '@entities/product/api'
import ProductCard from '@entities/product/ui/ProductCard.vue'
import { useFavoriteStore } from '@entities/favorite/store'
import { useAuthStore } from '@entities/user/store'

const favoriteStore = useFavoriteStore()
const authStore = useAuthStore()

const products = ref<Product[]>([])
const loading = ref(true)

function plural(count: number): string {
  const tens = count % 100
  const ones = count % 10
  if (ones === 1 && tens !== 11) return 'товар'
  if (ones >= 2 && ones <= 4 && (tens < 12 || tens > 14)) return 'товара'
  return 'товаров'
}

const subtitle = computed(() => {
  const count = products.value.length
  if (loading.value) return 'Собираем список'
  if (!count) return 'Отмечайте сердечком то, к чему хотите вернуться'
  return `${count} ${plural(count)} в вашем списке`
})

onMounted(async () => {
  try {
    await favoriteStore.fetchFavorites()

    if (authStore.token) {
      products.value = favoriteStore.products
    } else {
      const ids = Array.from(favoriteStore.ids)
      const resolved = await Promise.all(ids.map((id) => getCatalogProduct(id).catch(() => null)))
      products.value = resolved.filter((product): product is Product => product !== null)
    }
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="flex flex-col gap-4 px-4">
    <div>
      <h1 class="text-2xl font-semibold leading-tight text-sf-ink">Избранное</h1>
      <p class="text-sm text-sf-muted">{{ subtitle }}</p>
    </div>

    <p v-if="loading" class="py-16 text-center text-sf-muted">Загрузка…</p>

    <template v-else>
      <div v-if="products.length === 0" class="flex flex-col items-center gap-2 py-16 text-center text-sf-muted">
        <i class="pi pi-heart text-4xl" />
        <span>В избранном пока пусто</span>
      </div>

      <div v-else class="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6">
        <ProductCard v-for="product in products" :key="product.id" :product="product" />
      </div>
    </template>
  </div>
</template>
