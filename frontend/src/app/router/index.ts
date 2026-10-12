import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@entities/user/store'

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
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})

let attemptedSilentLogin = false

/**
 * Attempts a single silent Telegram login per session before the first
 * navigation(s) resolve. Non-blocking by design: failures are swallowed so
 * public routes still render. Seller-only routes are gated once the silent
 * login attempt has resolved (success or failure).
 */
router.beforeEach(async (to) => {
  const authStore = useAuthStore()

  if (!authStore.token && !attemptedSilentLogin) {
    attemptedSilentLogin = true
    try {
      await authStore.loginWithTelegram()
    } catch {
      // Ignored — see comment above.
    }
  }

  if (to.meta.requiresOwner && authStore.role !== 'seller' && authStore.role !== 'admin') {
    return { name: 'home' }
  }

  if (
    to.meta.requiresSeller &&
    authStore.role !== 'seller' &&
    authStore.role !== 'admin' &&
    authStore.role !== 'moderator'
  ) {
    return { name: 'home' }
  }

  return true
})

export default router
