<script setup lang="ts">
import { addToHomeScreen, checkHomeScreenStatus } from '@telegram-apps/sdk'
import type { Product } from '@entities/product/types'
import { getCatalogProducts } from '@entities/product/api'
import ProductCard from '@entities/product/ui/ProductCard.vue'
import { useStoreInfoStore } from '@entities/store-info/store'
import { useFavoriteStore } from '@entities/favorite/store'
import { useBannerStore } from '@entities/banner/store'
import BannerCarousel from '@entities/banner/ui/BannerCarousel.vue'

// Сколько товаров грузит подборка на главной — хватает и на «Товары», и на
// первые карточки шелфа «Новинки» (см. newItems ниже).
const FEED_SIZE = 24

// Длина полки «Новинки»: один горизонтальный проход, не второй каталог.
const NEW_SIZE = 10

const router = useRouter()
const storeInfoStore = useStoreInfoStore()
const favoriteStore = useFavoriteStore()
const bannerStore = useBannerStore()

const search = ref('')
const loading = ref(true)
const items = ref<Product[]>([])
const canAddToHome = ref(false)

// Новая подборка уже приходит отсортированной по дате — «Новинки» просто
// берёт первые карточки той же выдачи, второй запрос тут не нужен.
const newItems = computed(() => items.value.slice(0, NEW_SIZE))

function goToCatalog(): void {
  const query: Record<string, string> = {}
  const value = search.value.trim()
  if (value) query.search = value
  router.push({ path: '/catalog', query })
}

/**
 * Ярлык мини-аппа на главный экран — нативный диалог Telegram (Mini Apps
 * v8.0+), без PWA-манифеста и обходных путей через «Поделиться» в браузере:
 * в отличие от веб-версии tg-vitrina, здесь витрина открывается только
 * внутри Telegram, так что нативный способ — единственный и самый простой.
 */
async function promptAddToHome(): Promise<void> {
  if (!addToHomeScreen.isAvailable()) return
  try {
    addToHomeScreen()
  } catch {
    // Пользователь мог отказаться или диалог недоступен прямо сейчас —
    // кнопка просто останется на месте для повторной попытки.
  }
}

onMounted(async () => {
  storeInfoStore.recordVisit()

  if (addToHomeScreen.isAvailable()) {
    try {
      const status = checkHomeScreenStatus.isAvailable() ? await checkHomeScreenStatus() : 'unknown'
      canAddToHome.value = status !== 'added'
    } catch {
      canAddToHome.value = true
    }
  }

  loading.value = true
  try {
    const [, , result] = await Promise.all([
      favoriteStore.fetchFavorites(),
      bannerStore.fetchBanners(),
      getCatalogProducts({ limit: FEED_SIZE }),
    ])
    items.value = result.items
  } catch {
    items.value = []
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="flex flex-col gap-4 px-4 sm:px-6 md:px-8 lg:px-10">
    <div class="flex items-center gap-2">
      <input
        v-model="search"
        type="search"
        placeholder="Поиск по названию или артикулу"
        class="w-full rounded-full border border-sf-line bg-sf-card px-4 py-2.5 text-sm text-sf-ink outline-none placeholder:text-sf-muted focus:border-sf-accent"
        @keyup.enter="goToCatalog()"
      />
    </div>

    <BannerCarousel v-if="bannerStore.banners.length > 0" :banners="bannerStore.banners" />

    <!-- Только на главной: ярлык ведёт именно сюда, и предлагать его на
         каждом экране витрины значило бы мозолить глаза одной и той же
         кнопкой. -->
    <button
      v-if="canAddToHome"
      type="button"
      class="flex items-center gap-3 rounded-2xl border border-sf-line bg-sf-card p-3 text-left"
      @click="promptAddToHome"
    >
      <span class="flex size-9 shrink-0 items-center justify-center rounded-full bg-sf-soft text-sf-accent">
        <i class="pi pi-mobile" />
      </span>
      <span class="min-w-0 flex-1">
        <span class="block truncate text-sm font-medium leading-tight text-sf-ink"> Магазин на экран телефона </span>
        <span class="block truncate text-xs text-sf-muted"> Значок рядом с приложениями — открывается в одно касание </span>
      </span>
      <i class="pi pi-chevron-right shrink-0 text-xs text-sf-muted" />
    </button>

    <!-- Раздела нет вовсе, когда новинок нет: пустая полка на главной хуже,
         чем её отсутствие — она сообщает покупателю, что магазин стоит. -->
    <div v-if="newItems.length > 0" class="flex flex-col gap-3">
      <div>
        <h2 class="text-xl font-semibold leading-tight text-sf-ink">Новинки</h2>
        <p class="text-sm text-sf-muted">Появилось недавно</p>
      </div>
      <div
        class="no-scrollbar -mx-4 flex snap-x snap-mandatory gap-3 overflow-x-auto px-4 pb-1 sm:-mx-6 sm:px-6 md:-mx-8 md:px-8 lg:-mx-10 lg:px-10"
      >
        <div v-for="product in newItems" :key="product.id" class="w-36 shrink-0 snap-start">
          <ProductCard :product="product" />
        </div>
      </div>
    </div>

    <div class="flex items-end justify-between gap-3">
      <div>
        <h2 class="text-xl font-semibold leading-tight text-sf-ink">Товары</h2>
        <p class="text-sm text-sf-muted">Каждый раз новая подборка</p>
      </div>
      <RouterLink to="/catalog" class="shrink-0 text-sm text-sf-accent"> Весь каталог </RouterLink>
    </div>

    <p v-if="loading" class="py-16 text-center text-sf-muted">Загрузка…</p>

    <div v-else-if="items.length === 0" class="flex flex-col items-center gap-2 py-16 text-center text-sf-muted">
      <i class="pi pi-box text-4xl" />
      <span>В магазине пока нет товаров</span>
    </div>

    <div v-else class="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6">
      <ProductCard v-for="product in items" :key="product.id" :product="product" />
    </div>
  </div>
</template>
