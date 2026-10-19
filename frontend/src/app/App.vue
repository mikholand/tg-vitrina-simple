<script setup lang="ts">
import BottomNav from '@widgets/nav/BottomNav.vue'
import { useAuthStore } from '@entities/user/store'
import { useStoreInfoStore } from '@entities/store-info/store'
import { showBackButton, onBackButtonClick } from '@shared/telegram/sdk'

const route = useRoute()
const router = useRouter()
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

// Native Telegram Back Button, wired centrally here instead of per-page —
// shown on every screen, including the BottomNav tabs themselves, so it's
// always available to retrace whatever path got the user here.
showBackButton()

// Logical parent for each route — used only as a fallback when there's no
// in-app history to pop (e.g. the page was opened directly, or reloaded, so
// `history.state.back` below is empty). Tab roots fall back to their own
// "home" (BottomNav's first tab for that role); drill-in pages fall back to
// wherever they're actually linked from — dashboard tiles / the settings
// page's links, see DashboardPage.vue and SellerSettingsPage.vue.
const BACK_BUTTON_FALLBACK_PARENT: Partial<Record<string, string>> = {
  catalog: 'home',
  favorites: 'home',
  'seller-dashboard': 'home',
  'seller-products': 'seller-dashboard',
  'seller-categories': 'seller-dashboard',
  'seller-statistics': 'seller-dashboard',
  'seller-settings': 'seller-dashboard',
  'product-detail': 'catalog',
  'seller-raw-posts': 'seller-dashboard',
  'seller-sync': 'seller-dashboard',
  'seller-banners': 'seller-dashboard',
  'seller-contacts': 'seller-settings',
  'seller-team': 'seller-settings',
}

function onBackButtonPressed(): void {
  // vue-router's html5 history stores `back` (the path of the previous
  // in-app entry, or null if there isn't one) on `history.state` — more
  // reliable than a module-level counter since it survives page reloads.
  if (window.history.state?.back) {
    router.back()
    return
  }
  const name = typeof route.name === 'string' ? route.name : undefined
  const fallback = (name && BACK_BUTTON_FALLBACK_PARENT[name]) || 'home'
  if (fallback === name) return // already at the true root — nothing to do
  void router.replace({ name: fallback })
}

onBackButtonClick(onBackButtonPressed)

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
    class="min-h-screen text-sf-ink"
    :class="isSeller ? 'bg-sf-surface' : 'bg-sf-bg'"
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
