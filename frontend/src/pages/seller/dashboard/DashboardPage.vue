<script setup lang="ts">
import { useAuthStore } from '@entities/user/store'
import { getSellerOrders } from '@entities/cart/api'

interface Tile {
  to: string
  label: string
  icon: string
  badge?: number
}

const authStore = useAuthStore()

// Orders are the one tile with something waiting on the seller, so it
// leads the grid and carries a count of still-unhandled ("Новый") ones —
// the Telegram chat notification is easy to scroll past.
const newOrdersCount = ref(0)

onMounted(async () => {
  try {
    newOrdersCount.value = (await getSellerOrders(['new'], 1)).total
  } catch {
    // Just no badge — the tile itself still works.
  }
})

// tg-vitrina's "Главное" is a pure launcher — a grid of tiles, not an
// at-a-glance stats screen (that's «Статистика», a tab of its own there).
// Daily sections (Товары/Посты/Категории/Настройки) already live in the
// bottom nav; this grid covers those plus the ones that don't — Заказы,
// Статистика, Синхронизация, Баннеры — mirroring how tg-vitrina's dashboard surfaces
// banners/team/contacts/sync only through its own tile grid.
const tiles = computed<Tile[]>(() => {
  const base: Tile[] = [
    { to: '/seller/orders', label: 'Заказы', icon: 'receipt', badge: newOrdersCount.value },
    { to: '/seller/products', label: 'Товары', icon: 'box' },
    { to: '/seller/raw-posts', label: 'Посты', icon: 'inbox' },
    { to: '/seller/categories', label: 'Категории', icon: 'sitemap' },
    { to: '/seller/banners', label: 'Баннеры', icon: 'images' },
    { to: '/seller/statistics', label: 'Статистика', icon: 'chart-bar' },
    { to: '/seller/sync', label: 'Синхронизация', icon: 'sync' },
  ]
  // Settings (incl. moderator management) is owner-only.
  if (authStore.role === 'seller' || authStore.role === 'admin') {
    base.push({ to: '/seller/settings', label: 'Настройки', icon: 'cog' })
  }
  return base
})
</script>

<template>
  <div class="flex flex-col gap-4 px-4 sm:px-6 md:px-8 lg:px-10">
    <!-- tg-vitrina's "Главное" is a pure launcher grid — the shop name in
         the header above already says where you are, so no repeat heading
         here, same as there. -->
    <div class="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
      <RouterLink
        v-for="tile in tiles"
        :key="tile.to"
        :to="tile.to"
        class="flex flex-col items-center justify-center gap-2 rounded-2xl bg-white p-6 text-center shadow-sm transition-transform active:scale-95"
      >
        <span class="relative">
          <i :class="`pi pi-${tile.icon}`" class="text-2xl text-sf-accent" />
          <span
            v-if="tile.badge"
            class="absolute -right-3 -top-2 flex min-w-5 items-center justify-center rounded-full bg-sf-danger px-1 text-xs font-semibold leading-5 text-white"
          >
            {{ tile.badge }}
          </span>
        </span>
        <span class="text-sm font-medium text-sf-ink">{{ tile.label }}</span>
      </RouterLink>
    </div>
  </div>
</template>
