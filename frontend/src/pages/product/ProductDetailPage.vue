<script setup lang="ts">
import type { Product } from '@entities/product/types'
import type { CategoryTreeNode } from '@entities/category/types'
import AppSpinner from '@shared/ui/AppSpinner.vue'
import { getCatalogProduct } from '@entities/product/api'
import { availabilityLabels, formatPrice } from '@entities/product/labels'
import ProductGallery from '@entities/product/ui/ProductGallery.vue'
import { useFavoriteStore } from '@entities/favorite/store'
import { useCartStore } from '@entities/cart/store'
import { useStoreInfoStore } from '@entities/store-info/store'
import { useCategoryStore } from '@entities/category/store'
import type { PublicContact } from '@entities/contact/types'
import { getCatalogContacts } from '@entities/contact/api'
import ContactPicker from '@features/contact-picker/ContactPicker.vue'
import { shareLink, isInsideTelegram, isMobileTelegramPlatform } from '@shared/telegram/sdk'
import { toAbsoluteUrl, useJsonLd, useSeoMeta } from '@shared/seo/useSeoMeta'

const props = defineProps<{ id: string }>()

// Внутри Telegram нативная кнопка "Назад" уже есть в шапке (см. App.vue,
// showBackButton()) — своя поверх галереи там лишняя и только путается под
// нативной. Показываем её только вне Telegram (обычный браузер), где
// нативной кнопки нет. Launch-параметры не меняются за время жизни
// страницы, так что достаточно посчитать один раз.
//
// Даже вне Telegram кнопка нужна только на мобильном: у десктопного браузера
// уже есть своя стрелка "назад" в хроме окна, и дублировать её прямо под ней
// нашей — лишнее. Это чисто про ширину окна, а не про платформу, так что
// решается CSS-брейкпоинтом (`md:hidden` на самой кнопке в шаблоне), а не ещё
// одной веткой здесь.
const showOwnBackButton = !isInsideTelegram()

// Та же причина, по которой sdk.ts запрашивает fullscreen только на мобильных
// клиентах: именно fullscreen даёт плавающую нативную шапку (Back/"..."),
// перекрывающую верх галереи, — десктопный/веб-клиент Telegram в fullscreen
// не уходит и такой проблемы не имеет. Единый отступ под оба случая либо
// не спасал от перекрытия на мобильном, либо зря утапливал кнопки на
// десктопе — считаем один раз, как и showOwnBackButton выше.
const overlayTopPaddingClass = isMobileTelegramPlatform()
  ? 'pt-[max(6rem,var(--tg-content-safe-area-inset-top,0px))]'
  : 'pt-[max(1rem,var(--tg-content-safe-area-inset-top,0px))]'

const router = useRouter()
const favoriteStore = useFavoriteStore()
const cartStore = useCartStore()
const storeInfoStore = useStoreInfoStore()
const categoryStore = useCategoryStore()

const contacts = ref<PublicContact[]>([])
const contactPickerVisible = ref(false)

const product = ref<Product | null>(null)
const loading = ref(true)

const isFavorite = computed(() => (product.value ? favoriteStore.isFavorite(product.value.id) : false))

const price = computed(() => (product.value ? formatPrice(product.value.price, product.value.currency) : ''))

const specs = computed<{ label: string; value: string }[]>(() => {
  const item = product.value
  if (!item) return []
  const rows: { label: string; value: string }[] = []
  // availability=unknown несёт никакого сигнала о складе — строку не показываем.
  if (item.availability !== 'unknown') {
    rows.push({ label: 'Наличие', value: availabilityLabels[item.availability] })
  }
  // Только положительный остаток стоит показывать: 0 уже читается строкой выше.
  if (item.quantity) rows.push({ label: 'Осталось', value: `${item.quantity} шт.` })
  if (item.sku) rows.push({ label: 'Артикул', value: item.sku })
  return rows
})

const updatedAt = computed(() =>
  product.value
    ? new Date(product.value.updated_at).toLocaleDateString('ru-RU', {
        day: 'numeric',
        month: 'long',
        year: 'numeric',
      })
    : '',
)

// Сопоставляем id разделов товара с их названиями через дерево категорий.
const categoryNames = computed<string[]>(() => {
  if (!product.value) return []
  const names = new Map<number, string>()
  const walk = (nodes: CategoryTreeNode[]) => {
    for (const node of nodes) {
      names.set(node.id, node.name)
      walk(node.children)
    }
  }
  walk(categoryStore.tree)
  return product.value.category_ids.map((id) => names.get(id)).filter((name): name is string => !!name)
})

const AVAILABILITY_TO_SCHEMA: Record<string, string> = {
  in_stock: 'https://schema.org/InStock',
  on_order: 'https://schema.org/PreOrder',
  out_of_stock: 'https://schema.org/OutOfStock',
}

// Загрузка ещё не завершилась → `storeInfoStore.storeInfo` или `product` —
// null, и обе функции ниже отдают разумный фоллбек-заголовок вместо пустого;
// `watchEffect` внутри `useSeoMeta`/`useJsonLd` сам перезапустится, когда
// `load()` дозаполнит оба.
useSeoMeta(() => {
  const item = product.value
  const storeName = storeInfoStore.storeInfo?.name ?? 'Магазин'
  return {
    title: item ? `${item.name} — ${storeName}` : storeName,
    description: (item?.description || item?.name || '').slice(0, 160) || undefined,
    image: item?.photo_paths[0] ? toAbsoluteUrl(item.photo_paths[0]) : null,
  }
})

useJsonLd('product', () => {
  const item = product.value
  if (!item) return null
  return {
    '@context': 'https://schema.org',
    '@type': 'Product',
    name: item.name,
    description: item.description || undefined,
    image: item.photo_paths.map(toAbsoluteUrl),
    sku: item.sku || undefined,
    offers: item.price
      ? {
          '@type': 'Offer',
          priceCurrency: item.currency,
          price: item.price,
          availability: AVAILABILITY_TO_SCHEMA[item.availability],
        }
      : undefined,
  }
})

// Шторка выбора нужна только когда менеджеров несколько — с единственным её
// показ был бы лишним экраном между «хочу спросить» и чатом, и кнопка ведёт
// к нему напрямую.
function contactSeller(): void {
  if (contacts.value.length === 0) return
  if (contacts.value.length === 1) {
    window.open(contacts.value[0].url, '_blank', 'noopener,noreferrer')
    return
  }
  contactPickerVisible.value = true
}

// По deep-link карточка может открыться первой страницей — истории нет, и
// router.back() увёл бы покупателя из мини-аппа. Ведём его на главную.
function goBack(): void {
  if (window.history.state?.back) router.back()
  else router.push('/')
}

async function toggleFavorite(): Promise<void> {
  if (!product.value) return
  await favoriteStore.toggleFavorite(product.value.id)
}

// Same tracked-vs-untracked-stock convention as ProductCard.vue/the
// backend's checkout validation: only a positive tracked quantity blocks
// adding more.
const outOfStock = computed(() => product.value?.quantity !== null && (product.value?.quantity ?? 0) <= 0)
const cartQuantity = computed(() => (product.value ? cartStore.quantityOf(product.value.id) : 0))

const addedToCartAt = ref<number | null>(null)

function addToCart(): void {
  if (!product.value || outOfStock.value) return
  cartStore.addItem(product.value.id)
  const addedAt = Date.now()
  addedToCartAt.value = addedAt
  window.setTimeout(() => {
    if (addedToCartAt.value === addedAt) addedToCartAt.value = null
  }, 1500)
}

const shareCopiedAt = ref<number | null>(null)

// На телефоне внутри Telegram открываем системную шторку «Поделиться» —
// как и в SellerTeamPage.vue. Если недоступно (десктоп/обычный браузер),
// откатываемся на буфер обмена, но здесь — в отличие от шторки с
// приглашением — подсказка об этом скрывается сама через пару секунд:
// страница товара во весь экран, постоянно висящее сообщение было бы негде
// красиво разместить.
async function onShare(): Promise<void> {
  if (!product.value?.share_url) return
  const shared = shareLink(product.value.share_url, product.value.name)
  if (!shared) await onCopyShareLink()
}

async function onCopyShareLink(): Promise<void> {
  if (!product.value?.share_url) return
  try {
    await navigator.clipboard.writeText(product.value.share_url)
    const copiedAt = Date.now()
    shareCopiedAt.value = copiedAt
    window.setTimeout(() => {
      if (shareCopiedAt.value === copiedAt) shareCopiedAt.value = null
    }, 2000)
  } catch {
    // Буфер обмена недоступен — молча ничего не показываем, как и
    // toggleFavorite выше при сбое сети.
  }
}

async function load(): Promise<void> {
  loading.value = true
  try {
    const [loadedProduct, loadedContacts] = await Promise.all([
      getCatalogProduct(Number(props.id)),
      getCatalogContacts(),
      favoriteStore.fetchFavorites(),
      storeInfoStore.fetchStoreInfo(),
      categoryStore.fetchCategories(),
    ])
    product.value = loadedProduct
    contacts.value = loadedContacts
  } catch {
    product.value = null
  } finally {
    loading.value = false
  }
}

watch(() => props.id, load)
onMounted(load)
</script>

<template>
  <div class="mx-auto flex w-full max-w-2xl flex-col">
    <AppSpinner v-if="loading" />

    <div v-else-if="!product" class="flex flex-col items-center gap-2 py-16 text-center text-sf-muted">
      <i class="pi pi-box text-4xl" />
      <span>Товар не найден</span>
      <button
        type="button"
        class="mt-2 rounded-full bg-sf-accent px-5 py-2.5 text-sm font-medium text-white"
        @click="goBack"
      >
        На главную
      </button>
    </div>

    <template v-else>
      <ProductGallery :photos="product.photo_paths" :video="product.video_path" :alt="product.name">
        <template #overlay>
          <!-- `pt-[max(...)]`, not plain `pt-safe-top`: Telegram's native
               header (Back/collapse/"...") floats as an overlay on top of
               the content in fullscreen mode (requestFullscreen() in
               sdk.ts), and `--tg-content-safe-area-inset-top` is meant to
               account for exactly that — but some clients under-report it,
               which used to leave these buttons tucked behind the native
               header instead of below it. The floor is a worst-case guess at
               that header's height, same "floor under an unreliable/absent
               CSS var" move App.vue's outer padding already makes with
               `max(1rem, var(--tg-safe-area-inset-top))` — but unlike that
               one it must only apply on mobile (see overlayTopPaddingClass
               above): desktop/web Telegram never goes fullscreen, so the
               same floor there just pushes the buttons down for nothing. -->
          <div
            class="absolute inset-x-0 top-0 flex flex-col items-center gap-2 px-4"
            :class="overlayTopPaddingClass"
          >
            <div class="flex w-full items-start">
              <button
                v-if="showOwnBackButton"
                type="button"
                class="flex size-10 items-center justify-center rounded-full bg-black/45 backdrop-blur md:hidden"
                aria-label="Назад"
                @click="goBack"
              >
                <i class="pi pi-arrow-left text-white" />
              </button>
              <div class="ml-auto flex gap-2">
                <button
                  v-if="product?.share_url"
                  type="button"
                  class="flex size-10 items-center justify-center rounded-full bg-black/45 backdrop-blur"
                  aria-label="Поделиться"
                  @click="onShare"
                >
                  <i class="pi pi-share-alt text-sm text-white" />
                </button>
                <button
                  type="button"
                  class="flex size-10 items-center justify-center rounded-full bg-black/45 backdrop-blur"
                  :aria-label="isFavorite ? 'Убрать из избранного' : 'В избранное'"
                  @click="toggleFavorite"
                >
                  <i
                    class="pi text-sm"
                    :class="isFavorite ? 'pi-heart-fill text-sf-danger' : 'pi-heart text-white'"
                  />
                </button>
              </div>
            </div>
            <p
              v-if="shareCopiedAt"
              class="rounded-full bg-black/70 px-3 py-1.5 text-xs text-white backdrop-blur"
            >
              Ссылка скопирована
            </p>
          </div>
        </template>
      </ProductGallery>

      <div class="flex flex-col gap-5 px-4 pb-36 pt-5">
        <div>
          <p v-if="categoryNames.length" class="text-[0.65rem] uppercase tracking-widest text-sf-muted">
            {{ categoryNames.join(' · ') }}
          </p>
          <h1 class="mt-1 text-2xl font-semibold leading-tight text-sf-ink">
            {{ product.name }}
          </h1>
          <p class="mt-2 text-xl font-bold text-sf-ink">{{ price }}</p>
        </div>

        <dl v-if="specs.length" class="divide-y divide-sf-line rounded-2xl border border-sf-line bg-sf-card px-4">
          <div v-for="spec in specs" :key="spec.label" class="flex items-center justify-between gap-4 py-3 text-sm">
            <dt class="text-sf-muted">{{ spec.label }}</dt>
            <dd class="text-right font-medium text-sf-ink">{{ spec.value }}</dd>
          </div>
        </dl>

        <div v-if="product.description" class="flex flex-col gap-1.5">
          <h2 class="font-semibold text-sf-ink">Описание</h2>
          <p class="whitespace-pre-line text-sm leading-relaxed text-sf-ink">
            {{ product.description }}
          </p>
        </div>

        <p class="text-xs text-sf-muted">Обновлено {{ updatedAt }}</p>
      </div>

      <div
        class="fixed bottom-0 left-1/2 z-10 w-full max-w-2xl -translate-x-1/2 border-t border-sf-line bg-sf-bg px-4 pb-safe-bottom pt-3"
      >
        <p v-if="addedToCartAt" class="mb-1 text-right text-sm text-sf-success">Добавлено в корзину</p>
        <div class="mb-3 flex items-center gap-3">
          <div class="min-w-0">
            <p class="text-[0.65rem] uppercase tracking-widest text-sf-muted">Цена</p>
            <p class="truncate text-lg font-semibold text-sf-ink">{{ price }}</p>
          </div>

          <div class="ml-auto flex shrink-0 items-center gap-2">
            <button
              v-if="!outOfStock"
              type="button"
              class="relative flex items-center justify-center rounded-full border border-sf-line bg-sf-card p-3"
              aria-label="В корзину"
              @click="addToCart"
            >
              <i class="pi pi-shopping-cart" />
              <span
                v-if="cartQuantity > 0"
                class="absolute -right-1 -top-1 flex min-w-4 items-center justify-center rounded-full bg-sf-danger px-1 text-[0.6rem] font-semibold leading-4 text-white"
              >
                {{ cartQuantity }}
              </span>
            </button>

            <button
              v-if="contacts.length"
              type="button"
              class="flex items-center gap-2 rounded-full bg-sf-accent px-6 py-3 font-medium text-white"
              @click="contactSeller"
            >
              <i class="pi pi-send" />
              Написать продавцу
            </button>
            <span v-else-if="outOfStock" class="text-sm text-sf-muted">Контакты не указаны</span>
          </div>
        </div>
      </div>

      <ContactPicker v-model:visible="contactPickerVisible" :contacts="contacts" />
    </template>
  </div>
</template>
