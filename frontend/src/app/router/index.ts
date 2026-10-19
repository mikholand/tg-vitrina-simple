import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
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

const INVITE_START_PARAM_PREFIX = 'invite_'

/**
 * A `startapp=invite_<token>` deep link (see `SellerTeamPage.vue`, which
 * generates these) promotes whoever opens it to moderator — no separate
 * "accept invite" screen, since the `isStaff` redirect below already sends
 * a freshly-promoted moderator straight into the seller cabinet, which is
 * confirmation enough. Runs at most once per page load, after
 * `ensureAuthInitialized()` has settled, so there's a real logged-in user to
 * redeem it for; invalid/expired/already-used tokens are silently ignored
 * and just leave the visitor's role unchanged.
 */
function redeemPendingInvite(): Promise<void> {
  if (!inviteRedeemPromise) {
    inviteRedeemPromise = (async () => {
      const startParam = getStartParam()
      if (!startParam?.startsWith(INVITE_START_PARAM_PREFIX)) return

      const token = startParam.slice(INVITE_START_PARAM_PREFIX.length)
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

router.beforeEach(async (to) => {
  const authStore = useAuthStore()

  await ensureAuthInitialized()
  await redeemPendingInvite()

  const isStaff =
    authStore.role === 'seller' || authStore.role === 'admin' || authStore.role === 'moderator'

  // tg-vitrina sends sellers/admins/moderators straight to their own
  // dashboard instead of the public storefront — the customer "Витрина" has
  // no real use for staff, who don't even have a nav item back to it once
  // inside the seller cabinet. Mirrored here so opening the mini app lands
  // staff on "Главное" immediately rather than the generic home page.
  if (to.name === 'home' && isStaff) {
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
