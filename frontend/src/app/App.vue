<script setup lang="ts">
import BottomNav from '@widgets/nav/BottomNav.vue'
import TelegramLoginButton from '@features/telegram-login/TelegramLoginButton.vue'
import { useAuthStore } from '@entities/user/store'
import { useStoreInfoStore } from '@entities/store-info/store'
import { showBackButton, hideBackButton, onBackButtonClick } from '@shared/telegram/sdk'
import { currentTheme, toggleTheme } from '@shared/theme/theme'

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

// Header avatar for a logged-in website visitor — just the initial, not
// the full name: name + logout used to sit here and squeezed the shop's own
// name down to "Лавка Тёплый …" on a phone. Name and logout now live on
// the profile page this avatar links to.
const customerInitial = computed(
  () => (authStore.currentUser?.tg_first_name || authStore.currentUser?.tg_username || '?')[0]?.toUpperCase() ?? '?',
)

// Store↔admin switcher next to the settings gear in the seller/moderator
// header. Every /seller/* route name is prefixed "seller-" (dashboard
// included), so that's enough to tell which side we're on without a
// separate route-meta flag: from admin it jumps to "Витрина" — the
// storefront home, same as BottomNav's first customer tab — for a quick
// "view as customer", from anywhere else it jumps back into the cabinet.
const isInAdminSection = computed(
  () => typeof route.name === 'string' && route.name.startsWith('seller'),
)

// Native Telegram Back Button, wired centrally here instead of per-page —
// shown on every screen except each role's true home ('home' for
// customers, 'seller-dashboard' — labelled "Главное" in BottomNav — for
// staff), which has nothing above it to go back to.
const HOME_ROUTE_NAMES = new Set(['home', 'seller-dashboard'])

watch(
  () => route.name,
  (name) => {
    if (typeof name === 'string' && HOME_ROUTE_NAMES.has(name)) {
      hideBackButton()
    } else {
      showBackButton()
    }
  },
  { immediate: true },
)

// Logical parent for each route — used only as a fallback when there's no
// in-app history to pop (e.g. the page was opened directly, or reloaded, so
// `history.state.back` below is empty). Tab roots fall back to their own
// role's home; drill-in pages fall back to wherever they're actually linked
// from — dashboard tiles / the settings page's links, see
// DashboardPage.vue and SellerSettingsPage.vue.
const BACK_BUTTON_FALLBACK_PARENT: Partial<Record<string, string>> = {
  catalog: 'home',
  favorites: 'home',
  cart: 'home',
  profile: 'home',
  'seller-products': 'seller-dashboard',
  'seller-orders': 'seller-dashboard',
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

// Telegram's in-app WebView doesn't reliably close the on-screen keyboard
// just because the focused input scrolled out of view or lost visual focus
// ring — tapping anywhere else on the page should explicitly blur() the
// field to dismiss it, same as native apps. Capture phase so this fires
// before any component's own click handler can stopPropagation() it away;
// pointerdown (not click) so the keyboard starts closing immediately on
// touch-down rather than waiting for the tap to fully resolve.
function dismissKeyboardOnOutsideTap(event: PointerEvent): void {
  const active = document.activeElement as HTMLElement | null
  if (!active) return
  const isEditableField =
    active.tagName === 'INPUT' || active.tagName === 'TEXTAREA' || active.isContentEditable
  if (!isEditableField) return
  // Tapping inside the focused field itself (its own clear/eye icon etc.)
  // shouldn't blur it — only taps genuinely outside should.
  if (event.target instanceof Node && active.contains(event.target)) return
  active.blur()
}

onMounted(() => {
  // /catalog/store не требует авторизации, так что одного и того же
  // fetchStoreInfo хватает и покупательской шапке, и шапке продавца ниже.
  void storeInfoStore.fetchStoreInfo()

  document.addEventListener('pointerdown', dismissKeyboardOnOutsideTap, { capture: true })
})

onUnmounted(() => {
  document.removeEventListener('pointerdown', dismissKeyboardOnOutsideTap, { capture: true })
})

// Создаёт/находит <meta name="..."> или <meta property="..."> и задаёт её
// content — upsert, а не просто querySelector, потому что og:image в
// index.html изначально отсутствует (нет статичного лого на этапе сборки,
// оно приходит только из API конкретного магазина).
function upsertMeta(attr: 'name' | 'property', key: string, content: string): void {
  let el = document.querySelector<HTMLMetaElement>(`meta[${attr}="${key}"]`)
  if (!el) {
    el = document.createElement('meta')
    el.setAttribute(attr, key)
    document.head.appendChild(el)
  }
  el.setAttribute('content', content)
}

// Заголовок вкладки/PWA и SEO-теги по умолчанию — статичный фолбэк в
// index.html, нужен до того, как JS успеет загрузить данные магазина. Как
// только они подгрузились — подставляем реальные название/описание/лого
// (title, meta description, Open Graph, favicon).
watch(
  () => storeInfoStore.storeInfo,
  (info) => {
    if (!info) return
    document.title = info.name
    const description = info.description || `${info.name} — каталог товаров в Telegram.`
    upsertMeta('name', 'description', description)
    upsertMeta('property', 'og:title', info.name)
    upsertMeta('property', 'og:description', description)
    if (info.logo) {
      upsertMeta('property', 'og:image', info.logo)
      let icon = document.querySelector<HTMLLinkElement>('link[rel="icon"]')
      if (!icon) {
        icon = document.createElement('link')
        icon.rel = 'icon'
        document.head.appendChild(icon)
      }
      icon.href = info.logo
    }
  },
  { immediate: true },
)
</script>

<template>
  <div
    class="min-h-screen text-sf-ink"
    :class="isInAdminSection ? 'bg-sf-surface admin-scheme' : 'bg-sf-bg'"
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
      <!-- One shared header for both customer and seller/moderator sections
           (merged from two near-duplicate <header>s that only agreed on
           most of their markup) — switching between them via the
           store<->admin icon below now toggles a handful of v-if branches
           inside the SAME element instead of swapping two differently-
           sized headers in and out, which used to make the page visibly
           jump a few pixels on every switch (direct follow-up request).
           Left: shop logo/initial + name, identical in both sections,
           except the admin side links it back to the dashboard. Right: the
           one slot that actually differs — avatar/login for customers, the
           settings gear for admin owners — then the theme toggle (always),
           then the store<->admin switch icon (staff only, either
           direction). -->
      <header
        v-if="!bare && storeInfoStore.storeInfo"
        class="mb-1 flex items-center justify-between gap-2.5 px-4 pb-2 pt-safe-top sm:px-6 md:px-8 lg:px-10"
      >
        <RouterLink v-if="isInAdminSection" to="/seller" class="flex min-w-0 items-center gap-2.5">
          <img
            v-if="storeInfoStore.storeInfo.logo"
            :src="storeInfoStore.storeInfo.logo"
            :alt="storeInfoStore.storeInfo.name"
            class="size-9 shrink-0 rounded-full object-cover"
          />
          <div
            v-else
            class="flex size-9 shrink-0 items-center justify-center rounded-full bg-sf-accent text-sm font-semibold text-sf-accent-ink"
          >
            {{ storeInitial }}
          </div>
          <h1 class="min-w-0 truncate font-semibold leading-tight text-sf-ink">
            {{ storeInfoStore.storeInfo.name }}
          </h1>
        </RouterLink>
        <div v-else class="flex min-w-0 items-center gap-2.5">
          <img
            v-if="storeInfoStore.storeInfo.logo"
            :src="storeInfoStore.storeInfo.logo"
            :alt="storeInfoStore.storeInfo.name"
            class="size-9 shrink-0 rounded-full object-cover"
          />
          <div
            v-else
            class="flex size-9 shrink-0 items-center justify-center rounded-full bg-sf-accent text-sm font-semibold text-sf-accent-ink"
          >
            {{ storeInitial }}
          </div>
          <h1 class="min-w-0 truncate font-semibold leading-tight text-sf-ink">
            {{ storeInfoStore.storeInfo.name }}
          </h1>
        </div>

        <div class="flex shrink-0 items-center gap-3">
          <!-- Admin side: settings gear, owners only (moderators don't
               manage shop settings — see CLAUDE.md §8). -->
          <RouterLink
            v-if="isInAdminSection && isOwner"
            to="/seller/settings"
            class="flex items-center text-sf-muted"
            aria-label="Настройки"
          >
            <i class="pi pi-cog text-xl" />
          </RouterLink>

          <!-- Customer side: avatar/login, the only way to reach "Профиль"
               now that the bottom nav no longer has its own tab for it (see
               BottomNav.vue) — shown everywhere, Telegram included, not
               just to website visitors. Inside Telegram
               `authStore.currentUser` is always already set by the time
               this renders (silent init_data login, see
               `ensureAuthInitialized()` in router/index.ts), so the
               `TelegramLoginButton` fallback only ever actually shows to a
               logged-out website visitor. Hidden on the profile page
               itself, which already shows the same avatar (or login
               prompt) as its own heading. Placed first in this row (direct
               follow-up request), ahead of the theme toggle. -->
          <template v-if="!isInAdminSection && route.name !== 'profile'">
            <RouterLink
              v-if="authStore.currentUser"
              :to="{ name: 'profile' }"
              class="flex shrink-0 rounded-full focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sf-accent"
              aria-label="Профиль"
            >
              <img
                v-if="authStore.currentUser.tg_photo_url"
                :src="authStore.currentUser.tg_photo_url"
                alt=""
                class="size-8 rounded-full object-cover"
              />
              <span
                v-else
                class="flex size-8 items-center justify-center rounded-full bg-sf-soft text-sm font-semibold text-sf-accent"
              >
                {{ customerInitial }}
              </span>
            </RouterLink>
            <TelegramLoginButton v-else />
          </template>

          <button
            type="button"
            class="flex items-center text-sf-muted"
            :aria-label="currentTheme === 'dark' ? 'Светлая тема' : 'Тёмная тема'"
            @click="toggleTheme"
          >
            <i :class="currentTheme === 'dark' ? 'pi pi-sun' : 'pi pi-moon'" class="text-xl" />
          </button>
          <RouterLink
            v-if="isSeller"
            :to="isInAdminSection ? { name: 'home' } : { name: 'seller-dashboard' }"
            class="flex items-center text-sf-muted"
            :aria-label="isInAdminSection ? 'Магазин' : 'Админка'"
          >
            <i :class="isInAdminSection ? 'pi pi-shop' : 'pi pi-briefcase'" class="text-xl" />
          </RouterLink>
        </div>
      </header>

      <router-view />

      <!-- Agency credit — customers only, never staff: gated on `!isSeller`
           rather than `!isInAdminSection` so it also stays hidden while a
           seller/moderator is previewing the storefront via the
           store<->admin switcher above, not just inside the cabinet
           itself — a pitch to "order your own store" makes no sense aimed
           at the person who already runs this one. -->
      <footer
        v-if="!isSeller && !bare"
        class="px-4 pb-4 pt-6 text-center text-xs text-sf-muted sm:px-6 md:px-8 lg:px-10"
      >
        Разработано Polki Tech · Хотите такой же магазин?
        <!-- `sm:hidden` break + `whitespace-nowrap` on the link: at
             mobile/web-app widths this phrase is the one most likely to
             spill onto a third line, so it gets dropped to its own line
             instead of wrapping into a single orphaned word ("нам" alone
             below "Напишите"); wide screens have room, so the <br> is
             suppressed and it just flows inline there. -->
        <br class="sm:hidden" />
        <a
          href="https://t.me/polki_tech"
          target="_blank"
          rel="noopener noreferrer"
          class="whitespace-nowrap text-sf-accent"
        >
          Напишите нам
        </a>
      </footer>
    </div>
    <BottomNav v-if="!bare" />
  </div>
</template>
