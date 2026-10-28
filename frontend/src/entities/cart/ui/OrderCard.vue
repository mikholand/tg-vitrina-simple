<script setup lang="ts">
import { formatPrice } from '@entities/product/labels'
import { orderStatusClass, orderStatusLabel } from '../labels'
import type { Order } from '../types'
import OrderItemThumb from './OrderItemThumb.vue'

const props = defineProps<{ order: Order }>()

// Свёрнут по умолчанию: в профиле заказы — одна из нескольких секций, и
// полный состав каждого заказа превращал список в простыню. Свёрнутая
// строка отвечает на «что это было и сколько стоило» (номер, дата, первый
// товар, сумма), а состав и комментарий — по нажатию.
const expanded = ref(false)

// Год показываем только для прошлогодних заказов — у свежих он лишь
// удлиняет строку, которая на узком экране делит место с суммой.
const dateLabel = computed(() => {
  const date = new Date(props.order.created_at)
  const sameYear = date.getFullYear() === new Date().getFullYear()
  return date.toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    ...(sameYear ? {} : { year: 'numeric' }),
  })
})

// Сколько ещё позиций скрыто за миниатюрой первой — бейдж «+N» на ней.
const moreCount = computed(() => Math.max(props.order.items.length - 1, 0))

const summary = computed(() => {
  const [first, ...rest] = props.order.items
  if (!first) return ''
  return rest.length ? `${first.product_name} и ещё ${rest.length}` : first.product_name
})

const panelId = computed(() => `order-${props.order.id}-items`)
</script>

<template>
  <article class="rounded-2xl border border-sf-line bg-sf-card">
    <button
      type="button"
      class="flex w-full items-start gap-3 rounded-2xl p-4 text-left focus-visible:outline focus-visible:outline-2 focus-visible:outline-sf-accent"
      :aria-expanded="expanded"
      :aria-controls="panelId"
      @click="expanded = !expanded"
    >
      <span class="relative shrink-0">
        <OrderItemThumb :src="order.items[0]?.photo_path ?? null" class="size-11 rounded-xl" />
        <span
          v-if="moreCount"
          class="absolute -bottom-1 -right-1 rounded-full border-2 border-sf-card bg-sf-ink px-1.5 text-[0.65rem] font-semibold leading-4 text-white"
        >
          +{{ moreCount }}
        </span>
      </span>
      <span class="min-w-0 flex-1">
        <span class="flex items-center gap-2">
          <span class="font-medium text-sf-ink">№{{ order.id }}</span>
          <span class="text-sm text-sf-muted">{{ dateLabel }}</span>
        </span>
        <span class="mt-0.5 block truncate text-sm text-sf-muted">{{ summary }}</span>
      </span>
      <span class="flex shrink-0 flex-col items-end gap-1">
        <span class="font-semibold text-sf-ink">{{ formatPrice(order.total, order.currency) }}</span>
        <span class="rounded-full px-2 py-0.5 text-xs font-medium" :class="orderStatusClass(order.status)">
          {{ orderStatusLabel(order.status) }}
        </span>
      </span>
      <i
        class="pi pi-chevron-down mt-1.5 shrink-0 text-xs text-sf-placeholder transition-transform motion-reduce:transition-none"
        :class="expanded ? 'rotate-180' : ''"
      />
    </button>

    <div v-if="expanded" :id="panelId" class="mx-4 border-t border-sf-line pb-4 pt-3">
      <ul class="flex flex-col gap-2">
        <li v-for="item in order.items" :key="item.id" class="flex items-center gap-3 text-sm">
          <OrderItemThumb :src="item.photo_path" class="size-8 shrink-0 rounded-lg" />
          <span class="min-w-0 flex-1 text-sf-ink">
            {{ item.product_name }}
            <span class="whitespace-nowrap text-sf-muted">× {{ item.quantity }}</span>
          </span>
          <span class="shrink-0 text-sf-muted">
            {{ formatPrice((Number(item.price) * item.quantity).toFixed(2), item.currency) }}
          </span>
        </li>
      </ul>
      <p v-if="order.comment" class="mt-3 text-sm text-sf-muted">
        Комментарий: <span class="text-sf-ink">{{ order.comment }}</span>
      </p>
    </div>
  </article>
</template>
