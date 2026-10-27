<script setup lang="ts">
import { getMyOrders } from '@entities/cart/api'
import { formatPrice } from '@entities/product/labels'
import type { Order } from '@entities/cart/types'
import { useAuthStore } from '@entities/user/store'
import { isInsideTelegram } from '@shared/telegram/sdk'
import AppSpinner from '@shared/ui/AppSpinner.vue'
import TelegramLoginButton from '@features/telegram-login/TelegramLoginButton.vue'

const authStore = useAuthStore()
// See App.vue's own `outsideTelegram` — same reasoning: the Login Widget
// only makes sense outside the Mini App, where ensureAuthInitialized
// hasn't already silently signed the visitor in via init_data.
const outsideTelegram = !isInsideTelegram()

const orders = ref<Order[]>([])
const loading = ref(true)

// Only "new" exists today (see the backend's OrderStatus docstring — more
// statuses can be added later without a migration), but falling back to
// the raw value keeps this page from going blank on an unrecognized one
// rather than erroring.
const statusLabels: Record<string, string> = {
  new: 'Новый',
}

function statusLabel(status: string): string {
  return statusLabels[status] ?? status
}

function formatDate(value: string): string {
  return new Date(value).toLocaleString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

onMounted(async () => {
  // No session yet — most likely a website visitor who hasn't logged in
  // via the Telegram Login Widget (inside the Mini App, ensureAuthInitialized
  // already signs everyone in before any page renders). Nothing to fetch;
  // show a prompt instead of letting the request 401.
  if (!authStore.token) {
    loading.value = false
    return
  }
  try {
    const page = await getMyOrders()
    orders.value = page.items
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="flex flex-col gap-4 px-4 sm:px-6 md:px-8 lg:px-10">
    <div>
      <h1 class="text-2xl font-semibold leading-tight text-sf-ink">Мои заказы</h1>
      <p class="text-sm text-sf-muted">История ваших заказов в этом магазине</p>
    </div>

    <AppSpinner v-if="loading" />

    <div
      v-else-if="!authStore.token"
      class="flex flex-col items-center gap-3 py-16 text-center text-sf-muted"
    >
      <i class="pi pi-receipt text-4xl" />
      <span>Войдите, чтобы видеть историю своих заказов</span>
      <TelegramLoginButton v-if="outsideTelegram" />
    </div>

    <template v-else>
      <div
        v-if="orders.length === 0"
        class="flex flex-col items-center gap-2 py-16 text-center text-sf-muted"
      >
        <i class="pi pi-receipt text-4xl" />
        <span>Заказов пока нет</span>
      </div>

      <ul v-else class="flex flex-col gap-3">
        <li
          v-for="order in orders"
          :key="order.id"
          class="rounded-2xl border border-sf-line bg-sf-card p-4"
        >
          <div class="flex items-start justify-between gap-2">
            <div>
              <p class="font-medium text-sf-ink">Заказ №{{ order.id }}</p>
              <p class="text-xs text-sf-muted">{{ formatDate(order.created_at) }}</p>
            </div>
            <span class="shrink-0 rounded-full bg-sf-soft px-2.5 py-1 text-xs font-medium text-sf-accent">
              {{ statusLabel(order.status) }}
            </span>
          </div>

          <ul class="mt-3 flex flex-col gap-1.5 border-t border-sf-line pt-3">
            <li
              v-for="item in order.items"
              :key="item.id"
              class="flex items-center justify-between gap-2 text-sm"
            >
              <span class="min-w-0 truncate text-sf-ink">{{ item.product_name }} × {{ item.quantity }}</span>
              <span class="shrink-0 text-sf-muted">
                {{ formatPrice((Number(item.price) * item.quantity).toFixed(2), item.currency) }}
              </span>
            </li>
          </ul>

          <div class="mt-3 flex items-center justify-between border-t border-sf-line pt-3">
            <span class="text-sm text-sf-muted">Итого</span>
            <span class="font-semibold text-sf-ink">{{ formatPrice(order.total, order.currency) }}</span>
          </div>
        </li>
      </ul>
    </template>
  </div>
</template>
