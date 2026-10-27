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

// First four labels match tg-vitrina's storefront nav verbatim ("Витрина"
// names the landing/feed screen as a curated pick, distinct from "Каталог"
// which is the full by-section browse — the two words read as the same
// thing otherwise). "Заказы" has no tg-vitrina equivalent — added once the
// website login made a customer's own order history (OrdersPage.vue)
// something to actually navigate to.
const customerItems: NavItem[] = [
  { to: '/', label: 'Витрина', icon: 'pi pi-home' },
  { to: '/catalog', label: 'Каталог', icon: 'pi pi-th-large' },
  { to: '/favorites', label: 'Избранное', icon: 'pi pi-heart' },
  { to: '/cart', label: 'Корзина', icon: 'pi pi-shopping-cart' },
  { to: '/orders', label: 'Заказы', icon: 'pi pi-receipt' },
]

// Exactly tg-vitrina's tabBarSections, five items, same order: Главное,
// Товары, Категории, Статистика, Настройки. "Посты" isn't one of the five
// daily tabs there either (its nearest equivalent, moderation, lives inside
// Товары) — it stays reachable as a tile on the Главное grid instead, same
// as Баннеры/Синхронизация.
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

// Which tab set to show follows the current *section*, not the raw role —
// staff previewing the storefront via the store<->admin switcher in
// App.vue (route name not prefixed "seller-") must see the same customer
// tabs a real customer would, not get stuck in the cabinet's nav.
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
  <!-- Customer nav: tg-vitrina's StorefrontNav — a floating rounded pill,
       bordered/shadowed so it reads on a plain white background. -->
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
          <!-- Мобильный экран: только иконки, подписи скрыты — четыре
               полноразмерных лейбла в пилюле на узком экране смотрелись
               тесно. От sm и шире (десктоп/широкий Telegram Desktop) подпись
               возвращается. -->
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
