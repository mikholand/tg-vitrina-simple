# Shared Layout Components

The app has no dedicated `layouts/` folder — there is exactly one root shell
(`App.vue`) that every route renders inside via `<router-view />`, plus one bottom
navigation widget (`BottomNav.vue`) that swaps its tab set depending on whether the
current route is in the customer storefront or the seller cabinet. There is no
separate header component file — the header markup lives inline inside `App.vue`
(two variants: customer header, seller/admin header) rather than being split out.

## Route layout modes
`App.vue` computes a single boolean, `bare`, true only for `product-detail`
(`route.name === 'product-detail'`): that route renders full-bleed with no shared
header/footer/BottomNav padding, since `ProductDetailPage.vue` draws its own photo
hero and its own fixed bottom action bar. Every other route gets:
- the customer header (logo + shop name + login/profile) **or** the seller header
  (shop name + store/admin switcher + settings gear), chosen by
  `isInAdminSection` (`route.name` starts with `"seller"`),
- `<router-view />`,
- the "Разработано Polki Tech" footer (customers only, hidden for staff),
- `BottomNav` (hidden only when `bare`).

---

## `frontend/src/app/App.vue`
**App** — root shell: safe-area padding (Telegram Mini App insets), the
customer/seller header switch, Telegram back-button wiring, SEO `<meta>`/favicon
sync from `StoreInfo`, outside-tap keyboard dismissal, and the page footer. Mounts
`BottomNav` and `TelegramLoginButton`.

```vue
<script setup lang="ts">
import BottomNav from '@widgets/nav/BottomNav.vue'
import TelegramLoginButton from '@features/telegram-login/TelegramLoginButton.vue'
import { useAuthStore } from '@entities/user/store'
import { useStoreInfoStore } from '@entities/store-info/store'
import { showBackButton, hideBackButton, onBackButtonClick, isInsideTelegram } from '@shared/telegram/sdk'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const storeInfoStore = useStoreInfoStore()

const isSeller = computed(
  () => authStore.role === 'seller' || authStore.role === 'admin' || authStore.role === 'moderator',
)
const isOwner = computed(() => authStore.role === 'seller' || authStore.role === 'admin')

// The Telegram Login Widget only makes sense outside the Mini App — inside
// it, `ensureAuthInitialized()` (router/index.ts) already logs every
// visitor in silently via init_data before the first page even renders.
// This doesn't need to be reactive: whether we're inside Telegram is
// decided once, at launch, by the environment the page loaded into.
const outsideTelegram = !isInsideTelegram()

// Карточка товара рисует фото во всю ширину и свою нижнюю панель с ценой —
// общие вкладки и верхний отступ под чёлку на ней только мешали бы, как и
// в исходном tg-vitrina (там этот маршрут тоже помечен как "bare").
const bare = computed(() => route.name === 'product-detail')

const storeInitial = computed(() => storeInfoStore.storeInfo?.name?.[0]?.toUpperCase() ?? '')

// A logged-in website visitor's display name in the header — first+last
// name when Telegram gave us both, falling back to just the username (no
// name claim at all isn't actually possible for a real Telegram account,
// but the OIDC token's given_name could still come back empty for one) and
// finally a generic label so the header never renders blank where the name
// should be.
const customerDisplayName = computed(() => {
  const user = authStore.currentUser
  if (!user) return ''
  const fullName = [user.tg_first_name, user.tg_last_name].filter(Boolean).join(' ')
  return fullName || (user.tg_username ? `@${user.tg_username}` : 'Профиль')
})
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
  orders: 'home',
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
    :class="isInAdminSection ? 'bg-sf-surface' : 'bg-sf-bg'"
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
      <!-- Shown for customers always, and for staff while they're
           previewing the storefront via the store<->admin switcher below
           (hence `!isInAdminSection`, not role-based `!isSeller` — a staff
           member on /catalog must see exactly what a customer sees). -->
      <header
        v-if="!isInAdminSection && !bare && storeInfoStore.storeInfo"
        class="mb-1 flex items-center justify-between gap-2.5 px-4 pb-2 pt-safe-top sm:px-6 md:px-8 lg:px-10"
      >
        <div class="flex min-w-0 items-center gap-2.5">
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
        </div>
        <div class="flex shrink-0 items-center gap-3">
          <!-- Inside Telegram there's never a website login block to share
               this row with (see `outsideTelegram` below) — staff just
               gets the briefcase link on its own, as before. -->
          <RouterLink
            v-if="isSeller && !outsideTelegram"
            :to="{ name: 'seller-dashboard' }"
            class="text-sf-muted"
            aria-label="Админка"
          >
            <i class="pi pi-briefcase text-xl" />
          </RouterLink>
          <!-- Website visitors only (see `outsideTelegram` above) — inside
               Telegram there's always already a signed-in Mini App user by
               the time this renders, staff included. -->
          <template v-if="outsideTelegram">
            <div v-if="authStore.currentUser" class="flex items-center gap-2">
              <img
                v-if="authStore.currentUser.tg_photo_url"
                :src="authStore.currentUser.tg_photo_url"
                alt=""
                class="size-7 shrink-0 rounded-full object-cover"
              />
              <div
                v-else
                class="flex size-7 shrink-0 items-center justify-center rounded-full bg-sf-accent text-xs font-semibold text-white"
              >
                {{ customerInitial }}
              </div>
              <span class="max-w-40 truncate text-sm text-sf-ink">{{ customerDisplayName }}</span>
              <!-- A staff member logged in via the website widget still
                   needs a way into the cabinet — placed right before
                   logout, not at the start of the row (see the standalone
                   one above for the Mini App case). -->
              <RouterLink
                v-if="isSeller"
                :to="{ name: 'seller-dashboard' }"
                class="flex shrink-0 items-center text-sf-muted"
                aria-label="Админка"
              >
                <i class="pi pi-briefcase text-lg" />
              </RouterLink>
              <button
                type="button"
                class="flex shrink-0 items-center text-sf-muted"
                aria-label="Выйти"
                @click="authStore.logout()"
              >
                <i class="pi pi-sign-out text-lg" />
              </button>
            </div>
            <TelegramLoginButton v-else />
          </template>
        </div>
      </header>

      <!-- Seller cabinet: tg-vitrina's SellerLayout header — flat row with
           the shop name (back to the dashboard) and a gear to Settings,
           no card/logo like the customer header above. -->
      <header
        v-if="isInAdminSection && storeInfoStore.storeInfo"
        class="flex items-center justify-between gap-2 px-4 pb-2 pt-safe-top sm:px-6 md:px-8 lg:px-10"
      >
        <RouterLink to="/seller" class="truncate text-lg font-semibold leading-tight text-sf-ink">
          {{ storeInfoStore.storeInfo.name }}
        </RouterLink>
        <div class="flex shrink-0 items-center gap-3">
          <RouterLink
            :to="isInAdminSection ? { name: 'home' } : { name: 'seller-dashboard' }"
            class="text-sf-muted"
            :aria-label="isInAdminSection ? 'Магазин' : 'Админка'"
          >
            <i :class="isInAdminSection ? 'pi pi-shop' : 'pi pi-briefcase'" class="text-xl" />
          </RouterLink>
          <RouterLink v-if="isOwner" to="/seller/settings" class="text-sf-muted" aria-label="Настройки">
            <i class="pi pi-cog text-xl" />
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
```

---

## `frontend/src/widgets/nav/BottomNav.vue`
**BottomNav** — bottom navigation, present on every route except `bare` ones
(product detail). Renders one of two completely different visual styles depending on
section:
- **Customer** (`!isInAdminSection`): floating rounded pill nav, 5 tabs (Витрина,
  Каталог, Избранное, Корзина, Заказы), cart badge with live count.
- **Seller/admin/moderator** (`isInAdminSection`): flat bordered-top tab bar, 5 tabs
  for owner/admin (Главное, Товары, Категории, Статистика, Настройки) or 4 for
  moderator (same minus Настройки).

Active-tab detection is done via a manually computed class (not `RouterLink`'s
`active-class`) to avoid a specificity collision between two same-specificity
Tailwind color classes — see the code comment.

```vue
<script setup lang="ts">
import { useRoute } from 'vue-router'
import { useAuthStore } from '@entities/user/store'
import { useCartStore } from '@entities/cart/store'

interface NavItem {
  to: string
  label: string
  icon: string
}

const authStore = useAuthStore()
const cartStore = useCartStore()
const route = useRoute()

function isActive(item: NavItem): boolean {
  return route.path === item.to
}

const customerItems: NavItem[] = [
  { to: '/', label: 'Витрина', icon: 'pi pi-home' },
  { to: '/catalog', label: 'Каталог', icon: 'pi pi-th-large' },
  { to: '/favorites', label: 'Избранное', icon: 'pi pi-heart' },
  { to: '/cart', label: 'Корзина', icon: 'pi pi-shopping-cart' },
  { to: '/orders', label: 'Заказы', icon: 'pi pi-receipt' },
]

const sellerItems: NavItem[] = [
  { to: '/seller', label: 'Главное', icon: 'pi pi-th-large' },
  { to: '/seller/products', label: 'Товары', icon: 'pi pi-box' },
  { to: '/seller/categories', label: 'Категории', icon: 'pi pi-sitemap' },
  { to: '/seller/statistics', label: 'Статистика', icon: 'pi pi-chart-bar' },
  { to: '/seller/settings', label: 'Настройки', icon: 'pi pi-cog' },
]

// Moderators get the same cabinet as the owner, minus shop settings —
// "модератор без доступа к настройкам магазина".
const moderatorItems: NavItem[] = sellerItems.filter((item) => item.to !== '/seller/settings')

const isInAdminSection = computed(
  () => typeof route.name === 'string' && route.name.startsWith('seller'),
)
const items = computed<NavItem[]>(() => {
  if (!isInAdminSection.value) return customerItems
  if (authStore.role === 'moderator') return moderatorItems
  return sellerItems
})
</script>

<template>
  <!-- Customer nav: a floating rounded pill, bordered/shadowed so it reads
       on a plain white background. -->
  <nav
    v-if="!isInAdminSection"
    class="fixed bottom-0 left-1/2 z-40 w-full max-w-web-app -translate-x-1/2 px-4 pb-safe-bottom"
  >
    <ul class="mb-3 flex items-stretch gap-1 rounded-full border border-sf-line bg-sf-bg p-1.5 shadow-lg shadow-black/5">
      <li v-for="item in items" :key="item.to" class="flex-1">
        <RouterLink
          :to="item.to"
          class="relative flex items-center justify-center gap-2 rounded-full py-2.5 text-sm transition-colors"
          :class="isActive(item) ? 'bg-sf-soft font-medium text-sf-accent' : ''"
        >
          <i :class="item.icon" class="text-base sm:text-sm" />
          <!-- Mobile: icons only, labels hidden; from sm and up the label
               returns. -->
          <span class="hidden leading-none sm:inline">{{ item.label }}</span>
          <span
            v-if="item.to === '/cart' && cartStore.itemsCount > 0"
            class="absolute right-3 top-0.5 flex min-w-4 items-center justify-center rounded-full bg-sf-danger px-1 text-[0.6rem] font-semibold leading-4 text-white"
          >
            {{ cartStore.itemsCount }}
          </span>
        </RouterLink>
      </li>
    </ul>
  </nav>

  <!-- Seller nav: a flat, bordered-top tab bar. -->
  <nav
    v-else
    class="fixed bottom-0 left-1/2 z-40 w-full max-w-web-app -translate-x-1/2 border-t border-sf-line bg-sf-bg pb-safe-bottom"
  >
    <ul class="flex items-stretch justify-around">
      <li v-for="item in items" :key="item.to" class="flex-1">
        <RouterLink
          :to="item.to"
          class="flex flex-col items-center gap-1 py-2 transition-colors"
          :class="isActive(item) ? 'text-sf-ink font-medium' : 'text-sf-placeholder'"
        >
          <i :class="item.icon" class="text-lg" />
          <span class="text-[0.65rem] leading-none">{{ item.label }}</span>
        </RouterLink>
      </li>
    </ul>
  </nav>
</template>
```
