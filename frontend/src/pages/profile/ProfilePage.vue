<script setup lang="ts">
import { getMyOrders } from '@entities/cart/api'
import type { Order } from '@entities/cart/types'
import OrderCard from '@entities/cart/ui/OrderCard.vue'
import { getCatalogContacts } from '@entities/contact/api'
import { contactTypeIcons } from '@entities/contact/labels'
import type { PublicContact } from '@entities/contact/types'
import { useAuthStore } from '@entities/user/store'
import { isInsideTelegram } from '@shared/telegram/sdk'
import AppSpinner from '@shared/ui/AppSpinner.vue'
import TelegramLoginButton from '@features/telegram-login/TelegramLoginButton.vue'

const PAGE_SIZE = 20

const authStore = useAuthStore()
// See App.vue's own `outsideTelegram` — same reasoning: the Login Widget
// and logout only make sense outside the Mini App, where
// ensureAuthInitialized hasn't already silently signed the visitor in via
// init_data (and would just sign them straight back in on the next load).
const outsideTelegram = !isInsideTelegram()

const isStaff = computed(
  () => authStore.role === 'seller' || authStore.role === 'admin' || authStore.role === 'moderator',
)

const displayName = computed(() => {
  const user = authStore.currentUser
  if (!user) return 'Профиль'
  const fullName = [user.tg_first_name, user.tg_last_name].filter(Boolean).join(' ')
  return fullName || (user.tg_username ? `@${user.tg_username}` : 'Профиль')
})
const initial = computed(
  () => (authStore.currentUser?.tg_first_name || authStore.currentUser?.tg_username || '?')[0]?.toUpperCase() ?? '?',
)

const orders = ref<Order[]>([])
const ordersTotal = ref(0)
const ordersLoading = ref(false)
const loadingMore = ref(false)
const hasMore = computed(() => orders.value.length < ordersTotal.value)

// Публичные контакты магазина — тот же список, что у кнопки «Написать
// продавцу» на карточке товара. Статуса кроме «Новый» у заказа пока нет, так
// что «где мой заказ» решается только перепиской — даём её прямо здесь.
const contacts = ref<PublicContact[]>([])

async function loadOrders(): Promise<void> {
  ordersLoading.value = true
  try {
    const page = await getMyOrders(PAGE_SIZE, 0)
    orders.value = page.items
    ordersTotal.value = page.total
  } finally {
    ordersLoading.value = false
  }
}

async function loadMore(): Promise<void> {
  if (loadingMore.value) return
  loadingMore.value = true
  try {
    const page = await getMyOrders(PAGE_SIZE, orders.value.length)
    orders.value = [...orders.value, ...page.items]
    ordersTotal.value = page.total
  } finally {
    loadingMore.value = false
  }
}

// Логин через виджет происходит прямо на этой странице (кнопка в блоке
// «Войдите…») — без watch список так и остался бы пустым до перезагрузки, а
// после выхода продолжал бы показывать чужие заказы.
watch(
  () => authStore.token,
  (token) => {
    if (token) {
      void loadOrders()
    } else {
      orders.value = []
      ordersTotal.value = 0
    }
  },
  { immediate: true },
)

onMounted(async () => {
  contacts.value = await getCatalogContacts().catch(() => [])
})
</script>

<template>
  <div class="flex flex-col gap-6 px-4 sm:px-6 md:px-8 lg:px-10">
    <!-- Signed in: the person themselves is the page heading. Soft-blue
         initial, not solid accent — the solid circle is the shop's own logo
         fallback in the header, and two identical circles read as one
         identity. -->
    <section v-if="authStore.token" class="flex items-center gap-3">
      <img
        v-if="authStore.currentUser?.tg_photo_url"
        :src="authStore.currentUser.tg_photo_url"
        alt=""
        class="size-14 shrink-0 rounded-full object-cover"
      />
      <div
        v-else
        class="flex size-14 shrink-0 items-center justify-center rounded-full bg-sf-soft text-xl font-semibold text-sf-accent"
      >
        {{ initial }}
      </div>
      <div class="min-w-0 flex-1">
        <h1 class="truncate text-xl font-semibold leading-tight text-sf-ink">{{ displayName }}</h1>
        <p v-if="authStore.currentUser?.tg_username" class="truncate text-sm text-sf-muted">
          @{{ authStore.currentUser.tg_username }}
        </p>
      </div>
      <button
        v-if="outsideTelegram"
        type="button"
        class="flex shrink-0 items-center gap-1.5 rounded-full px-2 py-1 text-sm text-sf-muted focus-visible:outline focus-visible:outline-2 focus-visible:outline-sf-accent"
        @click="authStore.logout()"
      >
        <i class="pi pi-sign-out" />
        Выйти
      </button>
    </section>

    <!-- Not signed in. Practically only a website visitor: inside the Mini
         App ensureAuthInitialized has already logged everyone in. -->
    <section v-else class="flex flex-col gap-3">
      <h1 class="text-2xl font-semibold leading-tight text-sf-ink">Профиль</h1>
      <div class="flex flex-col items-start gap-3 rounded-2xl bg-sf-soft p-4">
        <p class="text-sm text-sf-ink">
          Войдите через Telegram, чтобы видеть свои заказы и сохранять избранное на всех устройствах.
        </p>
        <TelegramLoginButton v-if="outsideTelegram" />
        <!-- Guest checkout stores only a name + phone, nothing that ties the
             order to a Telegram account later (see OrderRepository.
             list_for_customer) — say so up front instead of letting someone
             log in and wonder where yesterday's order went. -->
        <p class="text-xs text-sf-muted">
          Заказы, оформленные без входа, здесь не появятся — продавец свяжется с вами по указанному телефону.
        </p>
      </div>
    </section>

    <RouterLink
      v-if="isStaff"
      :to="{ name: 'seller-dashboard' }"
      class="flex items-center gap-3 rounded-2xl border border-sf-line p-4 focus-visible:outline focus-visible:outline-2 focus-visible:outline-sf-accent"
    >
      <i class="pi pi-briefcase text-sf-muted" />
      <span class="flex-1 text-sf-ink">Кабинет продавца</span>
      <i class="pi pi-chevron-right text-xs text-sf-disabled" />
    </RouterLink>

    <section v-if="authStore.token" class="flex flex-col gap-3" aria-labelledby="profile-orders">
      <h2 id="profile-orders" class="text-lg font-semibold leading-tight text-sf-ink">
        Мои заказы
        <span v-if="ordersTotal" class="font-normal text-sf-muted">{{ ordersTotal }}</span>
      </h2>

      <AppSpinner v-if="ordersLoading" compact />

      <div
        v-else-if="orders.length === 0"
        class="flex flex-col items-start gap-3 rounded-2xl border border-dashed border-sf-line p-4"
      >
        <p class="text-sm text-sf-muted">Здесь появятся заказы, которые вы оформите в корзине.</p>
        <RouterLink :to="{ name: 'catalog' }" class="text-sm font-medium text-sf-accent">
          Перейти в каталог
        </RouterLink>
      </div>

      <template v-else>
        <OrderCard v-for="order in orders" :key="order.id" :order="order" />
        <Button
          v-if="hasMore"
          label="Показать ещё"
          severity="secondary"
          :loading="loadingMore"
          fluid
          @click="loadMore"
        />
      </template>
    </section>

    <section v-if="contacts.length" class="flex flex-col gap-3" aria-labelledby="profile-contacts">
      <div>
        <h2 id="profile-contacts" class="text-lg font-semibold leading-tight text-sf-ink">Связаться с продавцом</h2>
        <p class="text-sm text-sf-muted">Уточнить заказ, доставку или наличие</p>
      </div>
      <ul class="flex flex-col gap-2">
        <li v-for="contact in contacts" :key="contact.id">
          <a
            :href="contact.url"
            target="_blank"
            rel="noopener noreferrer"
            class="flex items-center gap-3 rounded-2xl border border-sf-line bg-sf-card p-3 active:bg-sf-soft focus-visible:outline focus-visible:outline-2 focus-visible:outline-sf-accent"
          >
            <span class="flex size-10 shrink-0 items-center justify-center rounded-full bg-sf-soft text-sf-accent">
              <i class="pi" :class="contactTypeIcons[contact.type]" />
            </span>
            <span class="min-w-0 flex-1">
              <span class="block truncate text-sm font-medium leading-tight text-sf-ink">{{ contact.label }}</span>
              <span class="block truncate text-sm text-sf-muted">{{ contact.value }}</span>
            </span>
            <i class="pi pi-chevron-right shrink-0 text-xs text-sf-disabled" />
          </a>
        </li>
      </ul>
    </section>
  </div>
</template>
