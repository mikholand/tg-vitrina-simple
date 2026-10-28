<script setup lang="ts">
import type { Product } from '@entities/product/types'
import { formatPrice } from '@entities/product/labels'
import { maxCartQuantity } from '@entities/product/stock'
import { useCartStore } from '@entities/cart/store'
import { useAuthStore } from '@entities/user/store'
import type { Order } from '@entities/cart/types'
import AppSpinner from '@shared/ui/AppSpinner.vue'

const cartStore = useCartStore()
const authStore = useAuthStore()

const loading = ref(true)
const submitting = ref(false)
const comment = ref('')
const contactName = ref('')
const contactPhone = ref('')
const error = ref<string | null>(null)
const placedOrder = ref<Order | null>(null)

const isEmpty = computed(() => cartStore.lines.size === 0)

// No Telegram session (the storefront opened as a plain website) means
// there's no identity to attach to the order — the backend requires a name
// + phone instead (see OrderService.checkout's `contact_required`).
const needsContact = computed(() => !authStore.token)
const contactValid = computed(
  () => !needsContact.value || (contactName.value.trim() !== '' && contactPhone.value.trim() !== ''),
)
const canSubmit = computed(() => !isEmpty.value && contactValid.value)

const totalLabel = computed(() => {
  const currency = cartStore.products[0]?.currency ?? 'RUB'
  return formatPrice(cartStore.total.toFixed(2), currency)
})

function thumbnail(product: Product): string | null {
  return product.photo_paths[0] ?? null
}

// Same cap ProductCard.vue/ProductDetailPage.vue use for "add to cart" —
// ties the "+" stepper to both tracked quantity AND an explicit "нет в
// наличии", so a customer can't build a cart line the backend will reject
// at checkout anyway.
function maxQuantity(product: Product): number | null {
  return maxCartQuantity(product)
}

function increment(product: Product): void {
  const current = cartStore.quantityOf(product.id)
  const max = maxQuantity(product)
  if (max !== null && current >= max) return
  cartStore.addItem(product.id, 1)
}

function decrement(product: Product): void {
  cartStore.setQuantity(product.id, cartStore.quantityOf(product.id) - 1)
}

function removeLine(product: Product): void {
  cartStore.removeItem(product.id)
}

/** Maps the backend's short machine-readable checkout error codes (see
 * `OrderService.checkout`) to a Russian message. Falls back to a generic
 * one for anything unrecognized. */
function describeError(detail: string): string {
  if (detail.startsWith('insufficient_stock')) {
    return 'Кого-то из товаров уже разобрали — остатки обновлены, проверьте количество.'
  }
  if (detail.startsWith('product_unavailable')) {
    return 'Один из товаров уже недоступен и был убран из корзины.'
  }
  if (detail === 'empty_cart') {
    return 'Корзина пуста.'
  }
  if (detail === 'contact_required') {
    return 'Укажите имя и телефон, чтобы продавец мог с вами связаться.'
  }
  return 'Не удалось оформить заказ. Попробуйте ещё раз.'
}

async function load(): Promise<void> {
  loading.value = true
  try {
    await cartStore.fetchCartProducts()
  } finally {
    loading.value = false
  }
}

async function submit(): Promise<void> {
  if (!canSubmit.value || submitting.value) return
  if (needsContact.value && !contactValid.value) {
    error.value = 'Укажите имя и телефон, чтобы продавец мог с вами связаться.'
    return
  }
  submitting.value = true
  error.value = null
  try {
    placedOrder.value = await cartStore.submitOrder(
      comment.value.trim() || null,
      needsContact.value ? contactName.value.trim() : null,
      needsContact.value ? contactPhone.value.trim() : null,
    )
    comment.value = ''
    contactName.value = ''
    contactPhone.value = ''
  } catch (err) {
    const detail =
      (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? ''
    error.value = describeError(detail)
    // Stock/availability may have changed since the cart was last loaded —
    // refresh it so the customer sees up-to-date quantities before retrying.
    await load()
  } finally {
    submitting.value = false
  }
}

function startNewOrder(): void {
  placedOrder.value = null
}

onMounted(load)
</script>

<template>
  <div class="flex flex-col gap-4 px-4 pb-10 sm:px-6 md:px-8 lg:px-10">
    <div>
      <h1 class="text-2xl font-semibold leading-tight text-sf-ink">Корзина</h1>
    </div>

    <AppSpinner v-if="loading" />

    <div v-else-if="placedOrder" class="flex flex-col items-center gap-3 rounded-2xl bg-sf-card p-6 text-center shadow-sm">
      <i class="pi pi-check-circle text-4xl text-sf-success" />
      <p class="text-lg font-semibold text-sf-ink">Заказ №{{ placedOrder.id }} оформлен</p>
      <p class="text-sm text-sf-muted">
        {{
          placedOrder.notified
            ? 'Продавец уже получил уведомление о заказе.'
            : 'Заказ сохранён — продавец свяжется с вами.'
        }}
      </p>
      <button
        type="button"
        class="mt-2 rounded-full bg-sf-accent px-6 py-2.5 text-sm font-medium text-sf-bg"
        @click="startNewOrder"
      >
        Продолжить покупки
      </button>
      <!-- Guest checkouts never show up in the profile's history (no
           customer_id to match them by), so only signed-in customers get
           the link — it would lead a guest to an empty list. -->
      <RouterLink v-if="authStore.token" :to="{ name: 'profile' }" class="text-sm font-medium text-sf-accent">
        Мои заказы
      </RouterLink>
    </div>

    <template v-else>
      <div v-if="isEmpty" class="flex flex-col items-center gap-2 py-16 text-center text-sf-muted">
        <i class="pi pi-shopping-cart text-4xl" />
        <span>Корзина пуста</span>
      </div>

      <template v-else>
        <div class="flex flex-col gap-2">
          <div
            v-for="product in cartStore.products"
            :key="product.id"
            class="flex items-center gap-3 rounded-2xl bg-sf-card p-3 shadow-sm"
          >
            <div class="flex size-14 shrink-0 items-center justify-center overflow-hidden rounded-xl bg-sf-soft">
              <img
                v-if="thumbnail(product)"
                :src="thumbnail(product) ?? undefined"
                :alt="product.name"
                class="size-full object-cover"
              />
              <i v-else class="pi pi-box text-sf-disabled" />
            </div>

            <div class="min-w-0 flex-1">
              <p class="line-clamp-2 text-sm leading-tight text-sf-ink">{{ product.name }}</p>
              <p class="mt-0.5 text-sm font-medium text-sf-ink">
                {{ formatPrice(product.price, product.currency) }}
              </p>
            </div>

            <div class="flex shrink-0 items-center gap-2">
              <button
                type="button"
                class="flex size-8 items-center justify-center rounded-full border border-sf-line text-sf-ink"
                aria-label="Убрать один"
                @click="decrement(product)"
              >
                <i class="pi pi-minus text-xs" />
              </button>
              <span class="w-5 text-center text-sm font-medium text-sf-ink">
                {{ cartStore.quantityOf(product.id) }}
              </span>
              <button
                type="button"
                class="flex size-8 items-center justify-center rounded-full border border-sf-line text-sf-ink disabled:opacity-40"
                aria-label="Добавить один"
                :disabled="maxQuantity(product) !== null && cartStore.quantityOf(product.id) >= (maxQuantity(product) ?? 0)"
                @click="increment(product)"
              >
                <i class="pi pi-plus text-xs" />
              </button>
            </div>

            <button
              type="button"
              class="shrink-0 text-sf-muted"
              aria-label="Удалить из корзины"
              @click="removeLine(product)"
            >
              <i class="pi pi-trash" />
            </button>
          </div>
        </div>

        <template v-if="needsContact">
          <p class="text-xs text-sf-muted">
            Вы оформляете заказ не из Telegram — укажите имя и телефон, чтобы продавец мог с вами связаться.
          </p>
          <label class="flex flex-col gap-1 text-sm">
            <span class="text-sf-muted">Имя *</span>
            <InputText v-model="contactName" placeholder="Как к вам обращаться" fluid />
          </label>
          <label class="flex flex-col gap-1 text-sm">
            <span class="text-sf-muted">Телефон *</span>
            <InputText v-model="contactPhone" type="tel" placeholder="+7 ..." fluid />
          </label>
        </template>

        <label class="flex flex-col gap-1 text-sm">
          <span class="text-sf-muted">Комментарий к заказу (необязательно)</span>
          <Textarea v-model="comment" auto-resize rows="2" fluid placeholder="Например, время доставки" />
        </label>

        <Message v-if="error" severity="error" :closable="false">{{ error }}</Message>

        <div class="flex items-center justify-between rounded-2xl bg-sf-card p-4 shadow-sm">
          <span class="text-sf-muted">Итого</span>
          <span class="text-lg font-semibold text-sf-ink">{{ totalLabel }}</span>
        </div>

        <Button
          label="Отправить заказ"
          :loading="submitting"
          :disabled="!canSubmit"
          fluid
          @click="submit"
        />
      </template>
    </template>
  </div>
</template>
