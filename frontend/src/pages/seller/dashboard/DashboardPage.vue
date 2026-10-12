<script setup lang="ts">
interface Tile {
  to: string
  label: string
  icon: string
}

// tg-vitrina's "Главное" is a pure launcher — a grid of tiles, not an
// at-a-glance stats screen (that's «Статистика», a tab of its own there).
// Daily sections (Товары/Посты/Категории/Настройки) already live in the
// bottom nav; this grid covers those plus the two that don't — Статистика
// and Синхронизация — mirroring how tg-vitrina's dashboard surfaces
// banners/team/contacts/sync only through its own tile grid.
const tiles: Tile[] = [
  { to: '/seller/products', label: 'Товары', icon: 'box' },
  { to: '/seller/raw-posts', label: 'Посты', icon: 'inbox' },
  { to: '/seller/categories', label: 'Категории', icon: 'sitemap' },
  { to: '/seller/statistics', label: 'Статистика', icon: 'chart-bar' },
  { to: '/seller/sync', label: 'Синхронизация', icon: 'sync' },
  { to: '/seller/settings', label: 'Настройки', icon: 'cog' },
]
</script>

<template>
  <div class="flex flex-col gap-4 px-4">
    <h1 class="text-xl font-semibold leading-tight text-sf-ink">Главное</h1>

    <div class="grid grid-cols-2 gap-3">
      <RouterLink
        v-for="tile in tiles"
        :key="tile.to"
        :to="tile.to"
        class="flex flex-col items-center justify-center gap-2 rounded-2xl border border-sf-line bg-sf-card p-6 text-center transition-transform active:scale-95"
      >
        <i :class="`pi pi-${tile.icon}`" class="text-2xl text-sf-accent" />
        <span class="text-sm font-medium text-sf-ink">{{ tile.label }}</span>
      </RouterLink>
    </div>
  </div>
</template>
