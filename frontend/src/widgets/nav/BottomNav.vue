<script setup lang="ts">
import { useAuthStore } from '@entities/user/store'

interface NavItem {
  to: string
  label: string
  icon: string
}

const authStore = useAuthStore()

// Labels match tg-vitrina's storefront nav verbatim ("Витрина" names the
// landing/feed screen as a curated pick, distinct from "Каталог" which is
// the full by-section browse — the two words read as the same thing
// otherwise).
const customerItems: NavItem[] = [
  { to: '/', label: 'Витрина', icon: 'pi pi-home' },
  { to: '/catalog', label: 'Каталог', icon: 'pi pi-th-large' },
  { to: '/favorites', label: 'Избранное', icon: 'pi pi-heart' },
]

const sellerItems: NavItem[] = [
  { to: '/seller', label: 'Главное', icon: 'pi pi-chart-bar' },
  { to: '/seller/products', label: 'Товары', icon: 'pi pi-box' },
  { to: '/seller/raw-posts', label: 'Посты', icon: 'pi pi-inbox' },
  { to: '/seller/categories', label: 'Разделы', icon: 'pi pi-sitemap' },
  { to: '/seller/settings', label: 'Настройки', icon: 'pi pi-cog' },
]

// Moderators get the same cabinet as the owner, minus shop settings —
// "модератор без доступа к настройкам магазина".
const moderatorItems: NavItem[] = sellerItems.filter((item) => item.to !== '/seller/settings')

const isSeller = computed(
  () => authStore.role === 'seller' || authStore.role === 'admin' || authStore.role === 'moderator',
)
const items = computed<NavItem[]>(() => {
  if (authStore.role === 'moderator') return moderatorItems
  if (isSeller.value) return sellerItems
  return customerItems
})
</script>

<template>
  <!-- Customer nav: tg-vitrina's StorefrontNav — a floating rounded pill,
       bordered/shadowed so it reads on a plain white background. -->
  <nav
    v-if="!isSeller"
    class="fixed bottom-0 left-1/2 z-40 w-full max-w-web-app -translate-x-1/2 px-4 pb-safe-bottom"
  >
    <ul class="mb-3 flex items-stretch gap-1 rounded-full border border-sf-line bg-sf-bg p-1.5 shadow-lg shadow-black/5">
      <li v-for="item in items" :key="item.to" class="flex-1">
        <RouterLink
          :to="item.to"
          class="flex items-center justify-center gap-2 rounded-full py-2.5 text-sm transition-colors"
          active-class="bg-sf-soft font-medium text-sf-accent"
          exact-active-class="bg-sf-soft font-medium text-sf-accent"
        >
          <i :class="item.icon" class="text-sm" />
          <span class="leading-none">{{ item.label }}</span>
        </RouterLink>
      </li>
    </ul>
  </nav>

  <!-- Seller nav: tg-vitrina's SellerNav — a flat, bordered-top tab bar. -->
  <nav
    v-else
    class="fixed bottom-0 left-1/2 z-40 w-full max-w-web-app -translate-x-1/2 border-t border-sf-line bg-sf-bg pb-safe-bottom"
  >
    <ul class="flex items-stretch justify-around">
      <li v-for="item in items" :key="item.to" class="flex-1">
        <RouterLink
          :to="item.to"
          class="flex flex-col items-center gap-1 py-2 text-sf-muted transition-colors"
          active-class="text-sf-accent"
          exact-active-class="text-sf-accent"
        >
          <i :class="item.icon" class="text-lg" />
          <span class="text-[0.65rem] leading-none">{{ item.label }}</span>
        </RouterLink>
      </li>
    </ul>
  </nav>
</template>
