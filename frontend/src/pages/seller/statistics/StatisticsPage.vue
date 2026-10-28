<script setup lang="ts">
import type { SellerStats, StatsPeriod } from '@entities/seller-settings/types'
import AppSpinner from '@shared/ui/AppSpinner.vue'
import { getSellerStats } from '@entities/seller-settings/api'

// Labels/values match tg-vitrina's statistics screen verbatim.
const periods: { value: StatsPeriod; label: string }[] = [
  { value: 'all', label: 'Всё время' },
  { value: '7d', label: '7 дней' },
  { value: '30d', label: '30 дней' },
]

const period = ref<StatsPeriod>('all')
const stats = ref<SellerStats | null>(null)
const loading = ref(true)

async function load(): Promise<void> {
  loading.value = true
  try {
    stats.value = await getSellerStats(period.value, 10)
  } finally {
    loading.value = false
  }
}

function setPeriod(value: StatsPeriod): void {
  if (period.value === value) return
  period.value = value
  void load()
}

onMounted(load)
</script>

<template>
  <div class="mx-auto flex w-full max-w-2xl flex-col gap-4 px-4">
    <h1 class="text-xl font-semibold leading-tight text-sf-ink">Статистика</h1>

    <div class="flex gap-2">
      <button
        v-for="option in periods"
        :key="option.value"
        type="button"
        class="flex-1 rounded-full py-1.5 text-sm transition-colors"
        :class="
          period === option.value
            ? 'bg-sf-accent font-medium text-sf-accent-ink'
            : 'bg-sf-card text-sf-muted shadow-sm'
        "
        @click="setPeriod(option.value)"
      >
        {{ option.label }}
      </button>
    </div>

    <AppSpinner v-if="loading" />

    <template v-else-if="stats">
      <!-- bg-sf-card + shadow-sm — this page sits on the seller cabinet's
           --sf-surface; the shadow is what reads as "raised" (see App.vue
           for the surface/card relationship). Same pattern as
           DashboardPage/SellerSettingsPage/SellerContactsPage/SellerTeamPage. -->
      <div class="grid grid-cols-2 gap-2.5">
        <div class="rounded-2xl bg-sf-card p-3.5 shadow-sm">
          <p class="text-2xl font-semibold text-sf-accent">{{ stats.store_views_total }}</p>
          <p class="text-xs text-sf-muted">Просмотры магазина</p>
        </div>
        <div class="rounded-2xl bg-sf-card p-3.5 shadow-sm">
          <p class="text-2xl font-semibold text-sf-accent">{{ stats.product_views_total }}</p>
          <p class="text-xs text-sf-muted">Просмотры товаров</p>
        </div>
      </div>

      <h2 class="text-sm font-medium text-sf-muted">Топ товаров</h2>
      <p v-if="stats.top_products.length === 0" class="py-8 text-center text-sm text-sf-muted">
        Пока нет данных
      </p>
      <ol v-else class="flex flex-col gap-2">
        <li
          v-for="(product, index) in stats.top_products"
          :key="product.id"
          class="flex items-center gap-3 rounded-xl bg-sf-card px-3 py-2 shadow-sm"
        >
          <span class="w-5 shrink-0 text-center text-sm text-sf-muted">{{ index + 1 }}</span>
          <span class="min-w-0 flex-1 truncate text-sm text-sf-ink">{{ product.name }}</span>
          <span class="shrink-0 text-sm font-medium text-sf-ink">{{ product.views_total }}</span>
        </li>
      </ol>
    </template>
  </div>
</template>
