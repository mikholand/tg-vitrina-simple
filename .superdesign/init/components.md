# Shared UI Components

Framework: Vue 3 (`<script setup lang="ts">`, Composition API) + Vite 6. Component
library: PrimeVue 4 (Aura preset, recolored once centrally in `frontend/src/main.ts`)
used directly in templates via auto-import (`unplugin-vue-components` +
`@primevue/auto-import-resolver`) — so PrimeVue components (`Button`, `InputText`,
`Textarea`, `Select`, `InputNumber`, `ToggleSwitch`, `Avatar`, `Tag`, `Message`) appear
in templates below with **no import statement**, that is expected, not an omission.
Styling: Tailwind CSS 3 + custom `--sf-*` tokens (see `theme.md`).

This project has a very small shared/ui primitive set (`frontend/src/shared/ui/`) —
just a bottom-sheet modal and a spinner. Most "reusable" visual components actually
live as `ui/*.vue` inside entity folders (`entities/<domain>/ui/`), since the project
follows Feature-Sliced-Design: a domain's reusable display component belongs with its
domain, not in a generic basket. Both are included below since the design tool needs
all reusable (non-page-specific) primitives regardless of which folder they live in.

No separate Button/Card/Badge/Input atoms exist — plain `<button>`/`<input>` elements
styled inline with Tailwind + `--sf-*` classes are used ad hoc everywhere (see
`pages.md` / `extractable-components.md` for where these inline patterns repeat enough
to be worth extracting as design-tool components even though they are not literally
components in the source).

---

## `frontend/src/shared/ui/AppModal.vue`
**AppModal** — bottom-sheet modal (slides up from the bottom, capped at `max-w-web-app`
width), used for every modal/dialog in the app except the Telegram login prompt.

Props: `visible: boolean`, `title: string`. Emits: `update:visible`. Slot: default
(body content).

```vue
<script setup lang="ts">
defineProps<{
  visible: boolean
  title: string
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
}>()

function close(): void {
  emit('update:visible', false)
}
</script>

<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div
        v-if="visible"
        class="fixed inset-0 z-50 flex items-end justify-center bg-black/40"
        @click.self="close"
      >
        <div class="max-h-[90vh] w-full max-w-web-app overflow-y-auto rounded-t-2xl bg-white pb-safe-bottom">
          <header class="sticky top-0 flex items-center justify-between border-b border-sf-line bg-white px-4 py-3">
            <h2 class="text-base font-semibold text-sf-ink">{{ title }}</h2>
            <button type="button" class="text-sf-muted" aria-label="Закрыть" @click="close">
              <i class="pi pi-times text-lg" />
            </button>
          </header>
          <div class="px-4 py-4">
            <slot />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}
.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
</style>
```

---

## `frontend/src/shared/ui/AppSpinner.vue`
**AppSpinner** — the single loading-state spinner used across every page (replaced a
dozen copy-pasted `Загрузка…` texts). Border-spin circle; `compact` prop shrinks it for
inline/sub-section loading states instead of full-page ones.

Props: `compact?: boolean` (default `false`).

```vue
<script setup lang="ts">
withDefaults(
  defineProps<{
    compact?: boolean
  }>(),
  { compact: false },
)
</script>

<template>
  <div class="flex items-center justify-center" :class="compact ? 'py-4' : 'py-16'">
    <div
      class="animate-spin rounded-full border-sf-line border-t-sf-accent duration-[0.8s]"
      :class="compact ? 'h-5 w-5 border-2' : 'h-10 w-10 border-[3px]'"
      role="status"
      aria-label="Загрузка"
    />
  </div>
</template>
```

---

## `frontend/src/entities/product/ui/ProductCard.vue`
**ProductCard** — the storefront product tile (used on home, catalog, favorites,
customer dashboards). Shows image/initial placeholder, favorite toggle, add-to-cart
button with cart-count badge, name, price, availability chip.

Props: `product: Product`. No emits — acts directly on `useFavoriteStore` /
`useCartStore`. Links to `/product/:id`.

```vue
<script setup lang="ts">
import type { Product } from '@entities/product/types'
import { availabilityChipClasses, availabilityLabels, formatPrice } from '@entities/product/labels'
import { isOutOfStock, maxCartQuantity, shouldShowQuantity } from '@entities/product/stock'
import { useFavoriteStore } from '@entities/favorite/store'
import { useCartStore } from '@entities/cart/store'

// Tint placeholders: colour is pinned to the product id, so the same
// product always looks the same and an image-less grid doesn't read as
// grey/broken. Cool blue-grey tones, matching the rest of the storefront.
const TINTS = ['bg-[#eff4ff]', 'bg-[#f1f5f9]', 'bg-[#f5f8ff]', 'bg-[#eef2f7]', 'bg-[#e8eef7]']

const props = defineProps<{ product: Product }>()

const favoriteStore = useFavoriteStore()
const cartStore = useCartStore()

const isFavorite = computed(() => favoriteStore.isFavorite(props.product.id))
const thumbnail = computed(() => props.product.photo_paths[0] ?? null)
const tint = computed(() => TINTS[props.product.id % TINTS.length])
const initial = computed(() => props.product.name[0]?.toUpperCase() ?? '')

const showAvailability = computed(() => props.product.availability !== 'unknown')

const availabilityLabel = computed(() => {
  const label = availabilityLabels[props.product.availability]
  return shouldShowQuantity(props.product) ? `${label} · ${props.product.quantity} шт.` : label
})

const outOfStock = computed(() => isOutOfStock(props.product))
const cartQuantity = computed(() => cartStore.quantityOf(props.product.id))

async function onToggleFavorite(event: Event): Promise<void> {
  event.preventDefault()
  event.stopPropagation()
  await favoriteStore.toggleFavorite(props.product.id)
}

function onAddToCart(event: Event): void {
  event.preventDefault()
  event.stopPropagation()
  const max = maxCartQuantity(props.product)
  if (max !== null && cartQuantity.value >= max) return
  cartStore.addItem(props.product.id)
}
</script>

<template>
  <RouterLink
    :to="`/product/${product.id}`"
    class="flex flex-col rounded-3xl border border-sf-line bg-sf-card p-2"
  >
    <div class="relative aspect-square overflow-hidden rounded-[1.15rem]" :class="tint">
      <img
        v-if="thumbnail"
        :src="thumbnail"
        :alt="product.name"
        class="size-full object-cover"
        loading="lazy"
      />
      <div
        v-else
        class="flex size-full items-center justify-center text-3xl font-semibold text-sf-disabled"
      >
        {{ initial }}
      </div>

      <button
        type="button"
        class="absolute right-2 top-2 flex size-8 items-center justify-center rounded-full bg-white/85 backdrop-blur"
        :aria-label="isFavorite ? 'Убрать из избранного' : 'В избранное'"
        @click="onToggleFavorite"
      >
        <i
          class="pi text-sm"
          :class="isFavorite ? 'pi-heart-fill text-sf-danger' : 'pi-heart text-sf-muted'"
        />
      </button>

      <button
        v-if="!outOfStock"
        type="button"
        class="absolute bottom-2 right-2 flex size-8 items-center justify-center rounded-full bg-white/85 backdrop-blur"
        aria-label="В корзину"
        @click="onAddToCart"
      >
        <i
          class="pi pi-shopping-cart text-sm"
          :class="cartQuantity > 0 ? 'text-sf-accent' : 'text-sf-muted'"
        />
        <span
          v-if="cartQuantity > 0"
          class="absolute -right-1 -top-1 flex min-w-4 items-center justify-center rounded-full bg-sf-danger px-1 text-[0.6rem] font-semibold leading-4 text-white"
        >
          {{ cartQuantity }}
        </span>
      </button>
    </div>

    <div class="flex flex-1 flex-col gap-1 px-1.5 pb-1 pt-2">
      <p class="line-clamp-2 text-sm leading-tight text-sf-ink">{{ product.name }}</p>
      <p class="mt-auto pt-1 font-semibold text-sf-ink">
        {{ formatPrice(product.price, product.currency) }}
      </p>
      <span
        v-if="showAvailability"
        class="w-fit rounded-full px-2 py-0.5 text-[0.65rem]"
        :class="availabilityChipClasses[product.availability]"
      >
        {{ availabilityLabel }}
      </span>
    </div>
  </RouterLink>
</template>
```

---

## `frontend/src/entities/product/ui/ProductGallery.vue`
**ProductGallery** — full-width swipeable photo/video gallery used on the product
detail page. Scroll-snap track + position dots; exposes an `overlay` slot for
back/share/favorite buttons layered on top of the media.

Props: `photos: string[]`, `video?: string | null`, `alt: string`. Slot: `overlay`.

```vue
<script setup lang="ts">
const props = defineProps<{
  /** Photo URLs (first is the cover, unless `video` is set — then the
   *  video leads and photos follow). */
  photos: string[]
  /** Optional product video URL. Rendered as the first slide when present. */
  video?: string | null
  /** Alt-text base (product name). */
  alt: string
}>()

const track = ref<HTMLElement | null>(null)
const activeIndex = ref(0)

const slideCount = computed(() => (props.video ? 1 : 0) + props.photos.length)

function onScroll(): void {
  const element = track.value
  if (!element) return
  activeIndex.value = Math.round(element.scrollLeft / element.clientWidth)
}

watch(
  () => [props.video, props.photos],
  () => {
    activeIndex.value = 0
    track.value?.scrollTo({ left: 0 })
  },
)

const initial = computed(() => props.alt[0]?.toUpperCase() ?? '')
</script>

<template>
  <div class="relative aspect-[4/5] overflow-hidden rounded-b-[2rem] bg-sf-soft">
    <div
      v-if="slideCount"
      ref="track"
      class="no-scrollbar flex size-full snap-x snap-mandatory overflow-x-auto"
      @scroll.passive="onScroll"
    >
      <video
        v-if="video"
        :src="video"
        controls
        playsinline
        class="size-full shrink-0 snap-center object-contain"
      />
      <img
        v-for="(photo, index) in photos"
        :key="photo"
        :src="photo"
        :alt="!video && index === 0 ? alt : `${alt} — фото ${index + 1}`"
        class="size-full shrink-0 snap-center object-contain"
        :loading="!video && index === 0 ? 'eager' : 'lazy'"
      />
    </div>
    <div v-else class="flex size-full items-center justify-center text-5xl font-semibold text-sf-disabled">
      {{ initial }}
    </div>

    <div v-if="slideCount > 1" class="absolute inset-x-0 bottom-5 flex justify-center gap-1.5">
      <span
        v-for="n in slideCount"
        :key="n"
        class="size-1.5 rounded-full transition-all"
        :class="n - 1 === activeIndex ? 'w-4 bg-white' : 'bg-white/60'"
      />
    </div>

    <slot name="overlay" />
  </div>
</template>
```

---

## `frontend/src/entities/category/ui/CategoryNode.vue`
**CategoryNode** — recursive tree row for the seller's category-management screen
(`SellerCategoriesPage.vue`): expand/collapse, visibility toggle, delete button.
Recurses into itself for children (`<category-node>` self-reference, kebab-case tag).

Props: `category: CategoryTreeNode`, `togglingId: number | null`, `deletingId: number |
null`. Emits: `toggle-visibility(category)`, `delete(category)`.

```vue
<script setup lang="ts">
import type { Category, CategoryTreeNode } from '../types'

defineProps<{
  category: CategoryTreeNode
  /** Visibility toggle in flight for this id — a second click would just confuse. */
  togglingId: number | null
  /** Delete in flight for this id. */
  deletingId: number | null
}>()

const emit = defineEmits<{
  'toggle-visibility': [category: Category]
  delete: [category: Category]
}>()

const open = ref(true)
</script>

<template>
  <li>
    <div
      class="flex items-center gap-2 rounded-xl border border-sf-line bg-white px-3 py-2"
      :class="category.is_hidden ? 'opacity-60' : ''"
    >
      <button
        v-if="category.children.length"
        type="button"
        class="w-5 shrink-0 text-sf-muted"
        :aria-label="open ? 'Свернуть' : 'Развернуть'"
        @click="open = !open"
      >
        <i class="pi text-xs" :class="open ? 'pi-chevron-down' : 'pi-chevron-right'" />
      </button>
      <span v-else class="w-5 shrink-0" />

      <div class="min-w-0 flex-1">
        <span class="block truncate text-sm text-sf-ink">{{ category.name }}</span>
        <span v-if="category.is_fallback" class="text-xs text-sf-muted">Категория по умолчанию</span>
      </div>

      <span v-if="category.children.length" class="shrink-0 text-xs text-sf-placeholder">
        {{ category.children.length }}
      </span>

      <button
        type="button"
        class="shrink-0 text-sf-muted disabled:opacity-50"
        :aria-label="category.is_hidden ? 'Показывать' : 'Скрыть'"
        :disabled="togglingId === category.id"
        @click="emit('toggle-visibility', category)"
      >
        <i
          v-if="togglingId !== category.id"
          class="pi text-sm"
          :class="category.is_hidden ? 'pi-eye-slash text-sf-placeholder' : 'pi-eye text-sf-accent'"
        />
        <i v-else class="pi pi-spin pi-spinner text-sm" />
      </button>

      <button
        v-if="!category.is_fallback"
        type="button"
        class="shrink-0 text-sf-muted disabled:opacity-50"
        aria-label="Удалить"
        :disabled="deletingId === category.id"
        @click="emit('delete', category)"
      >
        <i v-if="deletingId !== category.id" class="pi pi-trash text-sm" />
        <i v-else class="pi pi-spin pi-spinner text-sm" />
      </button>
    </div>

    <ul v-if="open && category.children.length" class="ml-4 mt-2 flex flex-col gap-2 border-l border-sf-line pl-2">
      <category-node
        v-for="child in category.children"
        :key="child.id"
        :category="child"
        :toggling-id="togglingId"
        :deleting-id="deletingId"
        @toggle-visibility="(c) => emit('toggle-visibility', c)"
        @delete="(c) => emit('delete', c)"
      />
    </ul>
  </li>
</template>
```

---

## `frontend/src/entities/category/ui/CategoryPickNode.vue`
**CategoryPickNode** — recursive checkbox tree for picking categories inside the
product editor (`ProductEditor.vue`). Shows a per-branch "N selected" count while
collapsed.

Props: `category: CategoryTreeNode`, `modelValue: number[]`. Emits: `update:modelValue`
(v-model compatible).

```vue
<script setup lang="ts">
import type { CategoryTreeNode } from '@entities/category/types'

const props = defineProps<{
  category: CategoryTreeNode
  modelValue: number[]
}>()

const emit = defineEmits<{
  'update:modelValue': [value: number[]]
}>()

const open = ref(false)

const picked = computed(() => {
  if (open.value) return 0
  const count = (nodes: CategoryTreeNode[]): number =>
    nodes.reduce(
      (sum, node) => sum + (props.modelValue.includes(node.id) ? 1 : 0) + count(node.children),
      0,
    )
  return count(props.category.children)
})

function toggle(): void {
  const next = props.modelValue.includes(props.category.id)
    ? props.modelValue.filter((id) => id !== props.category.id)
    : [...props.modelValue, props.category.id]
  emit('update:modelValue', next)
}
</script>

<template>
  <li>
    <div class="flex items-center gap-2 py-1">
      <button
        v-if="category.children.length"
        type="button"
        class="w-5 text-sf-muted"
        :aria-label="open ? 'Свернуть' : 'Развернуть'"
        @click="open = !open"
      >
        <i class="pi text-xs" :class="open ? 'pi-chevron-down' : 'pi-chevron-right'" />
      </button>
      <span v-else class="w-5" />

      <label class="flex flex-1 items-center gap-2 text-sm text-sf-ink">
        <input type="checkbox" class="size-4" :checked="modelValue.includes(category.id)" @change="toggle" />
        <span class="truncate">{{ category.name }}</span>
      </label>

      <span v-if="picked" class="text-xs text-sf-accent">{{ picked }}</span>
    </div>

    <ul v-if="open && category.children.length" class="ml-4 border-l border-sf-line pl-2">
      <CategoryPickNode
        v-for="child in category.children"
        :key="child.id"
        :category="child"
        :model-value="modelValue"
        @update:model-value="emit('update:modelValue', $event)"
      />
    </ul>
  </li>
</template>
```

---

## `frontend/src/entities/banner/ui/BannerCarousel.vue`
**BannerCarousel** — full-bleed home-page promo banner carousel. Native scroll-snap
with mobile (16:9) / desktop (3:1) crops, blurred-background + sharp-foreground image
pairing, step arrows shown only when there's more than one banner.

Props: `banners: Banner[]`. No emits — clicking a banner with a `link_url` opens it in
a new tab.

```vue
<script setup lang="ts">
import type { Banner } from '@entities/banner/types'

defineProps<{ banners: Banner[] }>()

function onBannerClick(banner: Banner): void {
  if (!banner.link_url) return
  window.open(banner.link_url, '_blank', 'noopener,noreferrer')
}

function desktopSrc(banner: Banner): string {
  return banner.image_path_desktop ?? banner.image_path_mobile
}

const scrollEl = ref<HTMLDivElement | null>(null)
const atStart = ref(true)
const atEnd = ref(true)

function updateEdges(): void {
  const el = scrollEl.value
  if (!el) return
  atStart.value = el.scrollLeft <= 1
  atEnd.value = el.scrollLeft >= el.scrollWidth - el.clientWidth - 1
}

function scrollByOne(direction: -1 | 1): void {
  const el = scrollEl.value
  if (!el) return
  el.scrollBy({ left: direction * el.clientWidth, behavior: 'smooth' })
}

onMounted(() => {
  updateEdges()
})
</script>

<template>
  <div class="relative">
    <div
      ref="scrollEl"
      class="no-scrollbar flex snap-x snap-mandatory overflow-x-auto"
      @scroll="updateEdges"
    >
      <button
        v-for="banner in banners"
        :key="banner.id"
        type="button"
        class="relative aspect-[16/9] w-full shrink-0 snap-start overflow-hidden rounded-3xl bg-sf-soft md:aspect-[3/1]"
        :class="banner.link_url ? 'cursor-pointer' : 'cursor-default'"
        @click="onBannerClick(banner)"
      >
        <img
          :src="banner.image_path_mobile"
          alt=""
          aria-hidden="true"
          class="absolute inset-0 size-full scale-110 object-cover blur-xl md:hidden"
          loading="lazy"
        />
        <img
          :src="banner.image_path_mobile"
          alt=""
          class="relative size-full object-contain md:hidden"
          loading="lazy"
        />

        <img
          :src="desktopSrc(banner)"
          alt=""
          aria-hidden="true"
          class="absolute inset-0 hidden size-full scale-110 object-cover blur-xl md:block"
          loading="lazy"
        />
        <img
          :src="desktopSrc(banner)"
          alt=""
          class="relative hidden size-full object-contain md:block"
          loading="lazy"
        />
      </button>
    </div>

    <template v-if="banners.length > 1">
      <button
        type="button"
        aria-label="Предыдущий баннер"
        class="absolute left-2 top-1/2 flex size-8 -translate-y-1/2 items-center justify-center rounded-full bg-black/40 text-white backdrop-blur-sm transition-opacity"
        :class="atStart ? 'pointer-events-none opacity-0' : 'opacity-100'"
        @click="scrollByOne(-1)"
      >
        <i class="pi pi-chevron-left text-sm" />
      </button>
      <button
        type="button"
        aria-label="Следующий баннер"
        class="absolute right-2 top-1/2 flex size-8 -translate-y-1/2 items-center justify-center rounded-full bg-black/40 text-white backdrop-blur-sm transition-opacity"
        :class="atEnd ? 'pointer-events-none opacity-0' : 'opacity-100'"
        @click="scrollByOne(1)"
      >
        <i class="pi pi-chevron-right text-sm" />
      </button>
    </template>
  </div>
</template>
```

---

## `frontend/src/features/contact-picker/ContactPicker.vue`
**ContactPicker** — bottom-sheet (built on `AppModal`) listing a shop's public contacts
so a customer can pick which one to message. Skipped entirely when there's only one
contact (caller opens it directly instead).

Props: `visible: boolean`, `contacts: PublicContact[]`. Emits: `update:visible`.

```vue
<script setup lang="ts">
import type { PublicContact } from '@entities/contact/types'
import { contactTypeIcons } from '@entities/contact/labels'
import AppModal from '@shared/ui/AppModal.vue'

defineProps<{
  visible: boolean
  contacts: PublicContact[]
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
}>()

function close(): void {
  emit('update:visible', false)
}

function pick(contact: PublicContact): void {
  close()
  window.open(contact.url, '_blank', 'noopener,noreferrer')
}
</script>

<template>
  <AppModal :visible="visible" title="Написать продавцу" @update:visible="(value: boolean) => emit('update:visible', value)">
    <ul class="flex flex-col gap-2">
      <li v-for="contact in contacts" :key="contact.id">
        <button
          type="button"
          class="flex w-full items-center gap-3 rounded-2xl border border-sf-line bg-sf-card p-3 text-left active:bg-sf-soft"
          @click="pick(contact)"
        >
          <span class="flex size-10 shrink-0 items-center justify-center rounded-full bg-sf-soft text-sf-accent">
            <i class="pi" :class="contactTypeIcons[contact.type]" />
          </span>
          <span class="min-w-0 flex-1">
            <span class="block truncate text-sm font-medium leading-tight text-sf-ink">{{ contact.label }}</span>
            <span class="block truncate text-sm text-sf-muted">{{ contact.value }}</span>
          </span>
          <i class="pi pi-chevron-right shrink-0 text-xs text-sf-disabled" />
        </button>
      </li>
    </ul>
  </AppModal>
</template>
```

---

## `frontend/src/features/product-delete/DeleteConfirm.vue`
**DeleteConfirm** — irreversible-delete confirmation sheet (built on `AppModal`) for
the seller's product list.

Props: `visible: boolean`, `product: Product | null`, `busy?: boolean`. Emits:
`update:visible`, `confirm`.

```vue
<script setup lang="ts">
import type { Product } from '@entities/product/types'
import AppModal from '@shared/ui/AppModal.vue'

defineProps<{
  visible: boolean
  product: Product | null
  busy?: boolean
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  confirm: []
}>()

function close(): void {
  emit('update:visible', false)
}
</script>

<template>
  <AppModal :visible="visible" title="Удалить товар" @update:visible="(value: boolean) => emit('update:visible', value)">
    <div class="flex flex-col gap-4">
      <p class="text-sm text-sf-ink">
        Товар «{{ product?.name }}» будет удалён навсегда — вместе с фото, видео и статистикой просмотров.
      </p>

      <p class="rounded-xl bg-sf-danger-soft px-3 py-2 text-sm text-sf-danger" role="alert">
        Восстановить его будет нельзя. Если товар нужен позже — скройте его вместо удаления.
      </p>

      <div class="flex gap-2">
        <button
          type="button"
          class="flex-1 rounded-xl border border-sf-line py-2.5 text-sf-muted"
          @click="close"
        >
          Отмена
        </button>
        <button
          type="button"
          :disabled="busy"
          class="flex-1 rounded-xl bg-sf-danger py-2.5 font-semibold text-white disabled:opacity-50"
          @click="emit('confirm')"
        >
          Удалить навсегда
        </button>
      </div>
    </div>
  </AppModal>
</template>
```

---

## `frontend/src/features/telegram-login/TelegramLoginButton.vue`
**TelegramLoginButton** — "Войти" link + centered modal embedding Telegram's own
official Login Widget `<script>`, for website visitors outside the Mini App (inside
Telegram, login is silent via `init_data`).

No props. No emits (self-contained; drives `useAuthStore`/`useStoreInfoStore`
internally).

```vue
<script setup lang="ts">
import { useAuthStore } from '@entities/user/store'
import { useStoreInfoStore } from '@entities/store-info/store'
import { mountTelegramLoginWidget, type TelegramWidgetAuthResult } from '@shared/telegram/widget'

const authStore = useAuthStore()
const storeInfoStore = useStoreInfoStore()

const visible = ref(false)
const container = ref<HTMLElement | null>(null)
const error = ref<string | null>(null)

async function handleAuth(result: TelegramWidgetAuthResult): Promise<void> {
  error.value = null
  if (!result.id_token) {
    error.value = 'Не удалось войти через Telegram. Попробуйте ещё раз.'
    return
  }
  try {
    await authStore.loginWithTelegramWidget(result.id_token)
    visible.value = false
  } catch {
    error.value = 'Не удалось войти через Telegram. Попробуйте ещё раз.'
  }
}

watch(
  () => [visible.value, storeInfoStore.storeInfo?.bot_client_id] as const,
  ([isVisible, botClientId]) => {
    if (isVisible && botClientId && container.value) {
      mountTelegramLoginWidget(container.value, botClientId, handleAuth)
    }
  },
  { flush: 'post' },
)
</script>

<template>
  <button
    type="button"
    class="flex shrink-0 items-center gap-1.5 text-sm font-medium text-sf-accent"
    @click="visible = true"
  >
    <i class="pi pi-user text-base" />
    Войти
  </button>

  <Teleport to="body">
    <Transition name="tg-login-modal-fade">
      <div
        v-if="visible"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
        @click.self="visible = false"
      >
        <div class="w-full max-w-sm rounded-2xl bg-white p-5">
          <header class="mb-4 flex items-center justify-between">
            <h2 class="text-base font-semibold text-sf-ink">Вход через Telegram</h2>
            <button type="button" class="text-sf-muted" aria-label="Закрыть" @click="visible = false">
              <i class="pi pi-times text-lg" />
            </button>
          </header>
          <div class="flex flex-col items-center gap-4 pb-1">
            <p class="text-center text-sm text-sf-muted">Войдите через свой аккаунт Telegram.</p>
            <div ref="container" class="min-h-11" />
            <p v-if="error" class="text-center text-sm text-sf-danger">{{ error }}</p>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.tg-login-modal-fade-enter-active,
.tg-login-modal-fade-leave-active {
  transition: opacity 0.2s ease;
}
.tg-login-modal-fade-enter-from,
.tg-login-modal-fade-leave-to {
  opacity: 0;
}
</style>
```

---

Note: `frontend/src/features/product-editor/ProductEditor.vue` (the full product
create/edit form — large, modal-based, built on `AppModal` + `CategoryPickNode`) is a
**feature**, not a shared primitive, and is page-specific enough (one consumer:
`SellerProductsPage.vue`) that its full source is omitted here to keep this file to
true reusable primitives — see `pages.md` (Seller Products dependency tree) and
`extractable-components.md` for its shape and extractable props.
