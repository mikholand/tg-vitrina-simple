<script setup lang="ts">
import { useRoute } from 'vue-router'
import { useAuthStore } from '@entities/user/store'

interface NavItem {
  to: string
  label: string
  icon: string
}

const authStore = useAuthStore()
const route = useRoute()

// Why not RouterLink's `active-class`/`exact-active-class`: those props
// APPEND a class string alongside whatever static `class` is already on the
// element — they don't replace it. That silently broke every previous
// attempt at coloring the active tab here: with a base `text-sf-placeholder`
// class always present, the active tab ended up with *both*
// `text-sf-placeholder` and `text-sf-ink` (or `text-sf-accent` before it) on
// the same element at once. Same specificity (single class selector each) →
// the cascade falls back to source order in the compiled stylesheet, and
// `.text-sf-placeholder` happens to be emitted after `.text-sf-ink`, so it
// silently won every time regardless of which color we picked for "active".
// Computing a single class ourselves (mirrors tg-vitrina's own
// `isActive(section) ? 'text-primary' : 'text-gray-400'` pattern) guarantees
// only one color class is ever on the element, so there's nothing left to
// collide.
function isActive(item: NavItem): boolean {
  return route.path === item.to
}

// Labels match tg-vitrina's storefront nav verbatim ("Витрина" names the
// landing/feed screen as a curated pick, distinct from "Каталог" which is
// the full by-section browse — the two words read as the same thing
// otherwise).
const customerItems: NavItem[] = [
  { to: '/', label: 'Витрина', icon: 'pi pi-home' },
  { to: '/catalog', label: 'Каталог', icon: 'pi pi-th-large' },
  { to: '/favorites', label: 'Избранное', icon: 'pi pi-heart' },
]

// Icon/label match tg-vitrina's tabBarSections verbatim where the same
// route exists there: 'th-large' (a tile grid) for "Главное" — it opens a
// grid of tiles, a bar chart icon described a page this isn't — and
// "Категории" instead of "Разделы", so the bottom-nav label agrees with the
// tile on the dashboard that links to the same /seller/categories route.
const sellerItems: NavItem[] = [
  { to: '/seller', label: 'Главное', icon: 'pi pi-th-large' },
  { to: '/seller/products', label: 'Товары', icon: 'pi pi-box' },
  { to: '/seller/raw-posts', label: 'Посты', icon: 'pi pi-inbox' },
  { to: '/seller/categories', label: 'Категории', icon: 'pi pi-sitemap' },
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
          :class="isActive(item) ? 'bg-sf-soft font-medium text-sf-accent' : ''"
        >
          <i :class="item.icon" class="text-sm" />
          <span class="leading-none">{{ item.label }}</span>
        </RouterLink>
      </li>
    </ul>
  </nav>

  <!-- Seller nav: tg-vitrina's SellerNav — a flat, bordered-top tab bar.
       tg-vitrina itself contrasts a light gray-400 inactive color against a
       strong dark-blue primary for the active tab, so the active one clearly
       pops instead of blending in with a merely-slightly-darker shade. -->
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
