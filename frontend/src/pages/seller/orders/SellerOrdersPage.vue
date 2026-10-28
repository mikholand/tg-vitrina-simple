<script setup lang="ts">
import { changeOrderStatus, getSellerOrders } from '@entities/cart/api'
import { orderStatusClass, orderStatusLabel, orderStatusLabels } from '@entities/cart/labels'
import type { OrderStatus, SellerOrder } from '@entities/cart/types'
import OrderItemThumb from '@entities/cart/ui/OrderItemThumb.vue'
import { formatPrice } from '@entities/product/labels'
import AppSpinner from '@shared/ui/AppSpinner.vue'

const PAGE_SIZE = 20

type Tab = 'active' | 'done' | 'all'

// "Активные" first and default: that's the seller's to-do list. Finished
// orders stay one tap away rather than mixed in, so a busy week's completed
// orders don't push today's new one below the fold.
const tabs: { value: Tab; label: string; statuses: OrderStatus[] }[] = [
  { value: 'active', label: 'Активные', statuses: ['new', 'accepted', 'shipped'] },
  { value: 'done', label: 'Завершённые', statuses: ['completed', 'cancelled'] },
  { value: 'all', label: 'Все', statuses: [] },
]

// The usual next step for each status — one obvious button instead of
// making the seller open a dropdown for the common path. Anything else
// (going back a step, cancelling) goes through the status select. Labels
// are verbs, not the target status name: right next to a select already
// showing a status, a button reading "Отправлен" looked like a second
// status badge rather than something to press.
const nextStep: Partial<Record<OrderStatus, { status: OrderStatus; label: string }>> = {
  new: { status: 'accepted', label: 'Принять' },
  accepted: { status: 'shipped', label: 'Отправить' },
  shipped: { status: 'completed', label: 'Завершить' },
}

const statusOptions = (Object.keys(orderStatusLabels) as OrderStatus[]).map((value) => ({
  value,
  label: orderStatusLabels[value],
}))

const activeTab = ref<Tab>('active')
const orders = ref<SellerOrder[]>([])
const total = ref(0)
const loading = ref(true)
const loadingMore = ref(false)
const loadError = ref(false)
const savingId = ref<number | null>(null)
// Per-order inline feedback under the card's actions — the cabinet has no
// toast host, and a message next to the order it's about reads better
// than one floating somewhere else anyway.
const notices = ref<Record<number, { severity: 'error' | 'info'; text: string }>>({})

const hasMore = computed(() => orders.value.length < total.value)

function currentStatuses(): OrderStatus[] {
  return tabs.find((tab) => tab.value === activeTab.value)?.statuses ?? []
}

async function load(): Promise<void> {
  loading.value = true
  loadError.value = false
  notices.value = {}
  try {
    const page = await getSellerOrders(currentStatuses(), PAGE_SIZE, 0)
    orders.value = page.items
    total.value = page.total
  } catch {
    loadError.value = true
  } finally {
    loading.value = false
  }
}

async function loadMore(): Promise<void> {
  if (loadingMore.value) return
  loadingMore.value = true
  try {
    const page = await getSellerOrders(currentStatuses(), PAGE_SIZE, orders.value.length)
    orders.value = [...orders.value, ...page.items]
    total.value = page.total
  } finally {
    loadingMore.value = false
  }
}

async function setStatus(order: SellerOrder, status: OrderStatus): Promise<void> {
  if (order.status === status || savingId.value !== null) return
  savingId.value = order.id
  delete notices.value[order.id]
  try {
    const updated = await changeOrderStatus(order.id, status)
    // Updated in place, not dropped from the list even if it no longer
    // matches the tab: an order vanishing the moment you tap "Выполнен"
    // reads as "it got lost", and there'd be nothing left to undo from.
    orders.value = orders.value.map((item) => (item.id === updated.id ? updated : item))
    if (status === 'cancelled') {
      // See OrderService.change_status — reserved stock isn't returned.
      notices.value[order.id] = {
        severity: 'info',
        text: 'Заказ отменён. Остатки товаров не вернулись автоматически — при необходимости поправьте количество в карточке товара.',
      }
    }
  } catch {
    notices.value[order.id] = { severity: 'error', text: 'Не удалось сменить статус. Попробуйте ещё раз.' }
  } finally {
    savingId.value = null
  }
}

function formatDateTime(value: string): string {
  return new Date(value).toLocaleString('ru-RU', {
    day: 'numeric',
    month: 'long',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function customerName(order: SellerOrder): string {
  const customer = order.customer
  if (!customer) return order.contact_name ?? 'Гость'
  const fullName = [customer.tg_first_name, customer.tg_last_name].filter(Boolean).join(' ')
  return fullName || (customer.tg_username ? `@${customer.tg_username}` : `ID ${customer.id}`)
}

// users.id is the Telegram user id, so a buyer without a public username
// is still reachable via tg://user — it opens their chat inside Telegram
// apps (not in a plain browser, but that's where the cabinet runs).
function customerLink(order: SellerOrder): { href: string; label: string } | null {
  if (order.customer) {
    return order.customer.tg_username
      ? { href: `https://t.me/${order.customer.tg_username}`, label: 'Написать' }
      : { href: `tg://user?id=${order.customer.id}`, label: 'Написать' }
  }
  if (order.contact_phone) {
    return { href: `tel:${order.contact_phone.replace(/[^\d+]/g, '')}`, label: 'Позвонить' }
  }
  return null
}

watch(activeTab, load)
onMounted(load)
</script>

<template>
  <div class="mx-auto flex w-full max-w-2xl flex-col gap-4 px-4">
    <h1 class="text-xl font-semibold leading-tight text-sf-ink">Заказы</h1>

    <div class="no-scrollbar -mx-4 flex gap-2 overflow-x-auto px-4">
      <button
        v-for="tab in tabs"
        :key="tab.value"
        type="button"
        class="shrink-0 rounded-full border px-3.5 py-1 text-sm"
        :class="
          activeTab === tab.value ? 'border-sf-accent bg-sf-accent text-sf-bg' : 'border-sf-line bg-sf-card text-sf-ink'
        "
        :aria-pressed="activeTab === tab.value"
        @click="activeTab = tab.value"
      >
        {{ tab.label }}
      </button>
    </div>

    <AppSpinner v-if="loading" />

    <Message v-else-if="loadError" severity="error" :closable="false">
      Не удалось загрузить заказы. Обновите страницу.
    </Message>

    <template v-else>
      <div v-if="orders.length === 0" class="flex flex-col items-center gap-2 py-16 text-center text-sf-muted">
        <i class="pi pi-receipt text-4xl" />
        <span>{{ activeTab === 'active' ? 'Новых заказов нет — всё обработано' : 'Здесь пока пусто' }}</span>
      </div>

      <div v-else class="flex flex-col gap-3">
        <article v-for="order in orders" :key="order.id" class="flex flex-col gap-3 rounded-2xl bg-sf-card p-4 shadow-sm">
          <header class="flex items-start justify-between gap-2">
            <div>
              <h2 class="font-semibold leading-tight text-sf-ink">№{{ order.id }}</h2>
              <p class="text-xs text-sf-muted">{{ formatDateTime(order.created_at) }}</p>
            </div>
            <span
              class="shrink-0 rounded-full px-2.5 py-1 text-xs font-medium"
              :class="orderStatusClass(order.status)"
            >
              {{ orderStatusLabel(order.status) }}
            </span>
          </header>

          <div class="flex items-center gap-3 rounded-xl bg-sf-surface px-3 py-2">
            <i class="pi text-sf-muted" :class="order.customer ? 'pi-telegram' : 'pi-user'" />
            <div class="min-w-0 flex-1">
              <p class="truncate text-sm font-medium text-sf-ink">{{ customerName(order) }}</p>
              <p class="truncate text-xs text-sf-muted">
                <template v-if="order.customer">
                  {{ order.customer.tg_username ? `@${order.customer.tg_username}` : 'Telegram' }}
                </template>
                <template v-else>Гость с сайта, {{ order.contact_phone }}</template>
              </p>
            </div>
            <a
              v-if="customerLink(order)"
              :href="customerLink(order)?.href"
              target="_blank"
              rel="noopener noreferrer"
              class="shrink-0 text-sm font-medium text-sf-accent"
            >
              {{ customerLink(order)?.label }}
            </a>
          </div>

          <ul class="flex flex-col gap-2">
            <li v-for="item in order.items" :key="item.id" class="flex items-center gap-3 text-sm">
              <OrderItemThumb :src="item.photo_path" class="size-10 shrink-0 rounded-lg" />
              <span class="min-w-0 flex-1 text-sf-ink">
                {{ item.product_name }}
                <!-- Explicit spaces: Vue's whitespace condensing drops the
                     newline between two adjacent spans entirely. -->
                <span v-if="item.sku" class="text-sf-muted">({{ item.sku }})</span>{{ ' ' }}
                <span class="whitespace-nowrap text-sf-muted">× {{ item.quantity }}</span>
              </span>
              <span class="shrink-0 text-sf-muted">
                {{ formatPrice((Number(item.price) * item.quantity).toFixed(2), item.currency) }}
              </span>
            </li>
          </ul>

          <p v-if="order.comment" class="rounded-xl bg-sf-warning-soft px-3 py-2 text-sm text-sf-ink">
            {{ order.comment }}
          </p>

          <div class="flex items-center justify-between border-t border-sf-line pt-3">
            <span class="text-sm text-sf-muted">Итого</span>
            <span class="font-semibold text-sf-ink">{{ formatPrice(order.total, order.currency) }}</span>
          </div>

          <!-- Notified=false covers both "no chat set via /setorderchat" and
               "Telegram rejected the send" — either way this list is the
               only place the seller learns about the order. -->
          <p v-if="!order.notified" class="flex items-center gap-1.5 text-xs text-sf-muted">
            <i class="pi pi-exclamation-circle text-xs" />
            Уведомление в Telegram-чат магазина не отправлялось
          </p>

          <div class="flex items-center gap-2">
            <Button
              v-if="nextStep[order.status as OrderStatus]"
              :label="nextStep[order.status as OrderStatus]?.label"
              size="small"
              :loading="savingId === order.id"
              :disabled="savingId !== null && savingId !== order.id"
              @click="setStatus(order, nextStep[order.status as OrderStatus]!.status)"
            />
            <Select
              :model-value="order.status"
              :options="statusOptions"
              option-label="label"
              option-value="value"
              size="small"
              aria-label="Статус заказа"
              :disabled="savingId !== null"
              class="min-w-0 flex-1"
              @update:model-value="(value: OrderStatus) => setStatus(order, value)"
            />
          </div>

          <Message v-if="notices[order.id]" :severity="notices[order.id].severity" :closable="false">
            {{ notices[order.id].text }}
          </Message>
        </article>

        <Button
          v-if="hasMore"
          label="Показать ещё"
          severity="secondary"
          :loading="loadingMore"
          fluid
          @click="loadMore"
        />
      </div>
    </template>
  </div>
</template>
