<script setup lang="ts">
import BottomNav from '@widgets/nav/BottomNav.vue'
import { useAuthStore } from '@entities/user/store'
import { useStoreInfoStore } from '@entities/store-info/store'

const route = useRoute()
const authStore = useAuthStore()
const storeInfoStore = useStoreInfoStore()

const isSeller = computed(
  () => authStore.role === 'seller' || authStore.role === 'admin' || authStore.role === 'moderator',
)
const isOwner = computed(() => authStore.role === 'seller' || authStore.role === 'admin')

// Карточка товара рисует фото во всю ширину и свою нижнюю панель с ценой —
// общие вкладки и верхний отступ под чёлку на ней только мешали бы, как и
// в исходном tg-vitrina (там этот маршрут тоже помечен как "bare").
const bare = computed(() => route.name === 'product-detail')

const storeInitial = computed(() => storeInfoStore.storeInfo?.name?.[0]?.toUpperCase() ?? '')

onMounted(() => {
  // /catalog/store не требует авторизации, так что одного и того же
  // fetchStoreInfo хватает и покупательской шапке, и шапке продавца ниже.
  void storeInfoStore.fetchStoreInfo()
})

// Заголовок вкладки/PWA по умолчанию — "Store" (см. index.html, он нужен
// как статичный фолбэк до того, как JS успеет загрузить данные магазина).
// Как только название магазина подгрузилось — подставляем его.
watch(
  () => storeInfoStore.storeInfo?.name,
  (name) => {
    if (name) document.title = name
  },
  { immediate: true },
)
</script>

<template>
  <div
    class="min-h-screen bg-sf-bg text-sf-ink"
    style="
      padding-left: var(--tg-safe-area-inset-left, 0px);
      padding-right: var(--tg-safe-area-inset-right, 0px);
    "
    :style="{
      // Outside Telegram this var is never set, so the fallback (0px) left
      // the header flush against the browser's top edge — max() keeps a
      // comfortable floor in the browser while still growing to the real
      // notch inset inside Telegram.
      paddingTop: bare ? '0px' : 'max(1rem, var(--tg-safe-area-inset-top, 0px))',
    }"
  >
    <div
      class="relative mx-auto max-w-web-app sm:max-w-2xl md:max-w-4xl lg:max-w-6xl xl:max-w-7xl"
      :class="bare ? '' : 'pb-20'"
    >
      <header
        v-if="!isSeller && !bare && storeInfoStore.storeInfo"
        class="mb-1 flex items-center gap-2.5 px-4 pb-2 pt-safe-top sm:px-6 md:px-8 lg:px-10"
      >
        <img
          v-if="storeInfoStore.storeInfo.logo"
          :src="storeInfoStore.storeInfo.logo"
          :alt="storeInfoStore.storeInfo.name"
          class="size-9 shrink-0 rounded-full object-cover"
        />
        <div
          v-else
          class="flex size-9 shrink-0 items-center justify-center rounded-full bg-sf-accent text-sm font-semibold text-white"
        >
          {{ storeInitial }}
        </div>
        <h1 class="min-w-0 truncate font-semibold leading-tight text-sf-ink">
          {{ storeInfoStore.storeInfo.name }}
        </h1>
      </header>

      <!-- Seller cabinet: tg-vitrina's SellerLayout header — flat row with
           the shop name (back to the dashboard) and a gear to Settings,
           no card/logo like the customer header above. -->
      <header
        v-if="isSeller && storeInfoStore.storeInfo"
        class="flex items-center justify-between gap-2 px-4 pb-2 pt-safe-top sm:px-6 md:px-8 lg:px-10"
      >
        <RouterLink to="/seller" class="truncate text-lg font-semibold leading-tight text-sf-ink">
          {{ storeInfoStore.storeInfo.name }}
        </RouterLink>
        <RouterLink
          v-if="isOwner"
          to="/seller/settings"
          class="shrink-0 text-sf-muted"
          aria-label="Настройки"
        >
          <i class="pi pi-cog text-xl" />
        </RouterLink>
      </header>

      <router-view />
    </div>
    <BottomNav v-if="!bare" />
  </div>
</template>
