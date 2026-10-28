# Routes

Router: `vue-router` 4, `createWebHistory()`. Defined in
`frontend/src/app/router/index.ts`. Every route component is lazy-loaded
(`() => import(...)`). Layout is always the single root shell `App.vue` (see
`layouts.md`) — there is no per-route layout component; `App.vue` itself switches
header/footer/nav visuals based on `route.name`.

Two custom route-meta flags are declared via `declare module 'vue-router'`:
- `requiresSeller?: boolean` — staff access: seller, admin, or moderator.
- `requiresOwner?: boolean` — owner-only: seller or admin — **moderators excluded**.
  Used by `seller-settings`, `seller-contacts`, `seller-team`. This is the flag
  CLAUDE.md references for `/seller/contacts` (`requiresOwner: true`) — note in the
  router file all three owner-only pages share it, not just contacts.

`router.beforeEach` also: runs `ensureAuthInitialized()` (silent Telegram login or
session restore) and `redeemPendingInvite()` on first navigation; resolves a
base64url-encoded Mini App deep link (`decodeStartPath`) to redirect straight to a
shared product/page; auto-redirects staff from `home` to `seller-dashboard` on first
load; enforces `requiresOwner`/`requiresSeller` by redirecting non-privileged users to
`home`.

## Full source — `frontend/src/app/router/index.ts`

```ts
import { createRouter, createWebHistory, type RouteLocationRaw, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@entities/user/store'
import { redeemInvite } from '@entities/invite/api'
import { getStartParam } from '@shared/telegram/sdk'

declare module 'vue-router' {
  interface RouteMeta {
    // Staff access: seller, admin, or moderator.
    requiresSeller?: boolean
    // Owner-only: seller or admin — moderators are explicitly excluded.
    // Used only by the shop settings page (store identity + moderator
    // management itself), per "модератор без доступа к настройкам магазина".
    requiresOwner?: boolean
  }
}

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: () => import('@pages/home/HomePage.vue'),
  },
  {
    path: '/catalog',
    name: 'catalog',
    component: () => import('@pages/catalog/CatalogPage.vue'),
  },
  {
    path: '/product/:id',
    name: 'product-detail',
    component: () => import('@pages/product/ProductDetailPage.vue'),
    props: true,
  },
  {
    path: '/favorites',
    name: 'favorites',
    component: () => import('@pages/favorites/FavoritesPage.vue'),
  },
  {
    path: '/cart',
    name: 'cart',
    component: () => import('@pages/cart/CartPage.vue'),
  },
  {
    path: '/orders',
    name: 'orders',
    component: () => import('@pages/orders/OrdersPage.vue'),
  },
  {
    path: '/seller',
    name: 'seller-dashboard',
    component: () => import('@pages/seller/dashboard/DashboardPage.vue'),
    meta: { requiresSeller: true },
  },
  {
    path: '/seller/products',
    name: 'seller-products',
    component: () => import('@pages/seller/products/SellerProductsPage.vue'),
    meta: { requiresSeller: true },
  },
  {
    path: '/seller/raw-posts',
    name: 'seller-raw-posts',
    component: () => import('@pages/seller/raw-posts/RawPostsPage.vue'),
    meta: { requiresSeller: true },
  },
  {
    path: '/seller/categories',
    name: 'seller-categories',
    component: () => import('@pages/seller/categories/SellerCategoriesPage.vue'),
    meta: { requiresSeller: true },
  },
  {
    path: '/seller/statistics',
    name: 'seller-statistics',
    component: () => import('@pages/seller/statistics/StatisticsPage.vue'),
    meta: { requiresSeller: true },
  },
  {
    path: '/seller/sync',
    name: 'seller-sync',
    component: () => import('@pages/seller/sync/SyncPage.vue'),
    meta: { requiresSeller: true },
  },
  {
    path: '/seller/banners',
    name: 'seller-banners',
    component: () => import('@pages/seller/banners/SellerBannersPage.vue'),
    meta: { requiresSeller: true },
  },
  {
    path: '/seller/settings',
    name: 'seller-settings',
    component: () => import('@pages/seller/settings/SellerSettingsPage.vue'),
    meta: { requiresOwner: true },
  },
  {
    path: '/seller/contacts',
    name: 'seller-contacts',
    component: () => import('@pages/seller/contacts/SellerContactsPage.vue'),
    meta: { requiresOwner: true },
  },
  {
    path: '/seller/team',
    name: 'seller-team',
    component: () => import('@pages/seller/team/SellerTeamPage.vue'),
    meta: { requiresOwner: true },
  },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})

let authInitPromise: Promise<void> | null = null

/**
 * Runs once per page load, before the first navigation(s) resolve:
 *  - no token yet (fresh tab, never logged in this browser) → silent
 *    Telegram login via initData.
 *  - token already in sessionStorage (e.g. a page *reload*, not a fresh
 *    tab — the token survives that) → re-fetch the profile instead of
 *    logging in again. Without this, `currentUser`/`role` would start out
 *    `null` on every reload (fresh Pinia store, nothing restores it from
 *    the token alone), so an owner/moderator would silently lose access to
 *    `/seller/*` until the page was reopened fresh from Telegram.
 * Memoized in a module-level promise (not just a boolean flag) so every
 * navigation that fires before the first one resolves awaits the same
 * in-flight attempt instead of racing a second one.
 */
function ensureAuthInitialized(): Promise<void> {
  if (!authInitPromise) {
    const authStore = useAuthStore()
    authInitPromise = (async () => {
      if (authStore.token) {
        try {
          await authStore.fetchMe()
        } catch {
          // Stale/invalid token — http.ts already tried a silent relogin
          // via Telegram initData on the 401 and failed, so this really is
          // a dead token. Drop it and fall back to anonymous access.
          authStore.logout()
        }
      } else {
        try {
          await authStore.loginWithTelegram()
        } catch {
          // Ignored — public routes still render outside Telegram.
        }
      }
    })()
  }
  return authInitPromise
}

let inviteRedeemPromise: Promise<void> | null = null

// Not a page route — recognized specially below instead of being navigated
// to literally. See `decodeStartPath()`'s doc comment for the overall
// scheme.
const INVITE_PATH_PREFIX = '/invite/'

/**
 * Decodes the Mini App `startapp` deep-link value into the app-relative
 * path it encodes (e.g. `/product/5`, `/invite/<token>`). The backend is the
 * sole producer of this value — `BotClient.product_mini_app_url()` /
 * `invite_mini_app_url()`, via `app/core/start_param.py`'s
 * `encode_start_param()` — which base64url-encodes the path so it survives
 * as Telegram's `startapp`/`start_param` (`^[A-Za-z0-9_-]{1,64}$`, no
 * slashes allowed there otherwise).
 *
 * This replaced the old `product_<id>`/`invite_<token>` prefix scheme: that
 * required this file to hard-code a route (`name: 'product-detail'`) per
 * prefix, which is exactly the kind of place a mismatch between what the
 * backend stamps and what the frontend expects can silently break deep
 * links. Encoding the destination path itself means the guard below just
 * navigates there directly — no per-destination logic to keep in sync.
 */
function decodeStartPath(startParam: string): string | null {
  try {
    const base64 = startParam.replace(/-/g, '+').replace(/_/g, '/')
    const padded = base64 + '='.repeat((4 - (base64.length % 4)) % 4)
    const binary = atob(padded)
    const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0))
    const path = new TextDecoder().decode(bytes)
    return path.startsWith('/') ? path : null
  } catch {
    return null
  }
}

// Set the instant a redirect is actually issued — NOT just "whether we've
// looked", see `pendingStartRedirect()`'s doc comment for why that
// distinction is the whole fix for a real infinite-loop bug found live
// (reproduced in a plain browser tab: `?tgWebAppStartParam=...` froze the
// page solid, CDP `Runtime.evaluate` timing out after 45s — not a "blank
// page", a genuinely hung main thread).
let startRedirectIssued = false

/**
 * A shared product/page deep link — returns the route to redirect to on the
 * very first navigation, or null when there's no start param / it decodes to
 * something that isn't a plain page path (e.g. an invite link — handled
 * separately, below) / it's already been issued once this page load.
 *
 * That last case is load-bearing, not a nicety: `router.beforeEach` below
 * only calls this while `from.matched.length === 0`, meant as a "just the
 * once, on first navigation" guard — but `from` is vue-router's *last
 * confirmed* route, and a navigation a guard redirects away from never
 * confirms. So for the whole chain of redirects `beforeEach` triggers during
 * the very first navigation (`/` → `/product/5`, then whatever the next
 * guard call decides), `from` stays `START_LOCATION` throughout — meaning
 * `from.matched.length === 0` is true on *every single one* of those calls,
 * not just the first. A non-memoized version of this function (what both
 * this file's previous `pendingProductRedirect()` and this function's own
 * first draft this session did) recomputes and returns the *same* redirect
 * every time it's asked — so the guard redirects to `/product/5`, is asked
 * again (`from` still empty), redirects to `/product/5` again, forever.
 * Confirmed live: loading a deep link in a plain browser tab hangs it solid,
 * matching the "blank page that never finishes loading" symptom in
 * Telegram. One `return null` after the first successful redirect is the
 * entire fix.
 */
function pendingStartRedirect(): RouteLocationRaw | null {
  if (startRedirectIssued) return null

  const startParam = getStartParam()
  if (!startParam) return null
  const path = decodeStartPath(startParam)
  if (!path || path.startsWith(INVITE_PATH_PREFIX)) return null

  // Guards against a blank screen: an unmatched `path` would otherwise make
  // `router.beforeEach` redirect straight into a dead end (no route, so
  // `<RouterView>` renders nothing) instead of just falling through to the
  // normal home page below — malformed/stale/unknown encoded paths should
  // degrade to "ignore it", not "break the app".
  if (router.resolve(path).matched.length === 0) return null

  startRedirectIssued = true
  return { path }
}

/**
 * A `startapp`-encoded `/invite/<token>` deep link (see `SellerTeamPage.vue`,
 * which generates these) promotes whoever opens it to moderator — no
 * separate "accept invite" screen, since the `isStaff` redirect below
 * already sends a freshly-promoted moderator straight into the seller
 * cabinet, which is confirmation enough. Runs at most once per page load,
 * after `ensureAuthInitialized()` has settled, so there's a real logged-in
 * user to redeem it for; invalid/expired/already-used tokens are silently
 * ignored and just leave the visitor's role unchanged.
 */
function redeemPendingInvite(): Promise<void> {
  if (!inviteRedeemPromise) {
    inviteRedeemPromise = (async () => {
      const startParam = getStartParam()
      if (!startParam) return
      const path = decodeStartPath(startParam)
      if (!path?.startsWith(INVITE_PATH_PREFIX)) return

      const token = path.slice(INVITE_PATH_PREFIX.length)
      if (!token) return
      try {
        await redeemInvite(token)
        await useAuthStore().fetchMe()
      } catch {
        // Invalid / expired / already redeemed — ignored.
      }
    })()
  }
  return inviteRedeemPromise
}

router.beforeEach(async (to, from) => {
  const authStore = useAuthStore()

  await ensureAuthInitialized()
  await redeemPendingInvite()

  // A shared deep link takes priority over the staff auto-redirect right
  // below — a seller/moderator opening a link a customer sent them should
  // land on that page, not get bounced to their own dashboard. Only on the
  // very first navigation, same `from.matched.length === 0` guard as
  // `redeemPendingInvite()`'s caller.
  if (from.matched.length === 0) {
    const startRedirect = pendingStartRedirect()
    if (startRedirect) return startRedirect
  }

  const isStaff =
    authStore.role === 'seller' || authStore.role === 'admin' || authStore.role === 'moderator'

  // tg-vitrina sends sellers/admins/moderators straight to their own
  // dashboard instead of the public storefront, so opening the mini app
  // lands staff on "Главное" immediately rather than the generic home page.
  // Only on that very first navigation though (`from.matched` is empty only
  // for vue-router's START_LOCATION) — staff can deliberately come back to
  // "Витрина" afterwards (the store<->admin switcher in App.vue, the
  // BottomNav "Витрина" tab while previewing) and this must not bounce them
  // straight back to the dashboard every time.
  if (to.name === 'home' && isStaff && from.matched.length === 0) {
    return { name: 'seller-dashboard' }
  }

  if (to.meta.requiresOwner && authStore.role !== 'seller' && authStore.role !== 'admin') {
    return { name: 'home' }
  }

  if (to.meta.requiresSeller && !isStaff) {
    return { name: 'home' }
  }

  return true
})

export default router
```

## Route map

| Path | Name | Component | Meta | Layout |
|---|---|---|---|---|
| `/` | `home` | `pages/home/HomePage.vue` | — | App shell + customer header + BottomNav |
| `/catalog` | `catalog` | `pages/catalog/CatalogPage.vue` | — | App shell + customer header + BottomNav |
| `/product/:id` | `product-detail` | `pages/product/ProductDetailPage.vue` (`props: true`) | — | App shell, **bare** (no header/footer/BottomNav padding) |
| `/favorites` | `favorites` | `pages/favorites/FavoritesPage.vue` | — | App shell + customer header + BottomNav |
| `/cart` | `cart` | `pages/cart/CartPage.vue` | — | App shell + customer header + BottomNav |
| `/orders` | `orders` | `pages/orders/OrdersPage.vue` | — | App shell + customer header + BottomNav |
| `/seller` | `seller-dashboard` | `pages/seller/dashboard/DashboardPage.vue` | `requiresSeller` | App shell + seller header + seller BottomNav |
| `/seller/products` | `seller-products` | `pages/seller/products/SellerProductsPage.vue` | `requiresSeller` | App shell + seller header + seller BottomNav |
| `/seller/raw-posts` | `seller-raw-posts` | `pages/seller/raw-posts/RawPostsPage.vue` | `requiresSeller` | App shell + seller header + seller BottomNav |
| `/seller/categories` | `seller-categories` | `pages/seller/categories/SellerCategoriesPage.vue` | `requiresSeller` | App shell + seller header + seller BottomNav |
| `/seller/statistics` | `seller-statistics` | `pages/seller/statistics/StatisticsPage.vue` | `requiresSeller` | App shell + seller header + seller BottomNav |
| `/seller/sync` | `seller-sync` | `pages/seller/sync/SyncPage.vue` | `requiresSeller` | App shell + seller header + seller BottomNav |
| `/seller/banners` | `seller-banners` | `pages/seller/banners/SellerBannersPage.vue` | `requiresSeller` | App shell + seller header + seller BottomNav |
| `/seller/settings` | `seller-settings` | `pages/seller/settings/SellerSettingsPage.vue` | `requiresOwner` | App shell + seller header + seller BottomNav |
| `/seller/contacts` | `seller-contacts` | `pages/seller/contacts/SellerContactsPage.vue` | `requiresOwner` | App shell + seller header + seller BottomNav (no BottomNav entry — reached via Settings link) |
| `/seller/team` | `seller-team` | `pages/seller/team/SellerTeamPage.vue` | `requiresOwner` | App shell + seller header + seller BottomNav (no BottomNav entry — reached via Settings link) |

Not a route: `/invite/<token>` — a virtual path only ever produced by
`decodeStartPath()` from a Mini App `startapp` deep link; it is intercepted and
redeemed in `router.beforeEach` (`redeemPendingInvite`), never actually navigated to.

## Page summaries

- **`/` Home** — search bar linking to `/catalog`, optional `BannerCarousel`, optional
  "add Mini App to home screen" prompt, a horizontal "Новинки" (new arrivals) shelf,
  then a full `ProductCard` grid of the latest catalog feed.
- **`/catalog` Catalog** — search bar, a grid of root-category tiles ("Все" + each
  root category) and a row of child-category chips under the selected root, then a
  paginated (`Показать ещё`) `ProductCard` grid filtered by search/category.
- **`/product/:id` Product detail** — `bare` route: full-bleed `ProductGallery` with
  an overlay (back/share/favorite buttons), spec list (availability/quantity/sku),
  description, and a fixed bottom bar with price + add-to-cart + "Написать продавцу"
  (opens `ContactPicker` when there's more than one contact).
- **`/cart` Cart** — list of cart lines with quantity steppers, guest contact
  name/phone fields (shown only without a Telegram session), order comment, total,
  and a submit button; shows an order-confirmation state after checkout.
- **`/favorites` Favorites** — plain `ProductCard` grid of favorited products (and a
  pluralized Russian count subtitle).
- **`/orders` Orders ("Мои заказы")** — customer's own order history; prompts
  `TelegramLoginButton` when there's no session (website visitor).
- **`/seller` Dashboard ("Главное")** — a pure launcher grid of tiles to every other
  cabinet section (Товары, Посты, Категории, Баннеры, Статистика, Синхронизация, and
  Настройки for owners only).
- **`/seller/products` Products** — status-tab filter (Все/Черновики/
  Опубликованные/Скрытые), search, paginated list with publish/hide/edit/delete
  actions; edit/create opens `ProductEditor`, delete opens `DeleteConfirm`.
- **`/seller/settings` Settings** — store name/description form + logo upload, links
  to `seller-contacts` and `seller-team`, and read-only server-configured fields
  (Telegram channel id, extractor/order-chat status).

(Seller categories/raw-posts/statistics/sync/banners/contacts/team pages exist but are
not expanded above — see `pages.md` for component trees of the ones traced in detail.)
