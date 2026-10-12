<script setup lang="ts">
import type { Product, ProductStatus } from '@entities/product/types'
import { getSellerProducts, hideProduct, publishProduct } from '@entities/product/api'
import { productStatusChipClasses, productStatusLabels } from '@entities/product/labels'
import ProductEditor from '@features/product-editor/ProductEditor.vue'

const PAGE_SIZE = 20

type StatusFilter = ProductStatus | 'all'

const tabs: { label: string; value: StatusFilter }[] = [
  { label: 'Все', value: 'all' },
  { label: 'Черновики', value: 'draft' },
  { label: 'Опубликованные', value: 'published' },
  { label: 'Скрытые', value: 'hidden' },
]

const activeTab = ref<StatusFilter>('all')
const products = ref<Product[]>([])
const total = ref(0)
const offset = ref(0)
const loading = ref(true)
const loadingMore = ref(false)
const actionLoadingId = ref<number | null>(null)
const editorVisible = ref(false)
const editingProduct = ref<Product | null>(null)

const hasMore = computed(() => products.value.length < total.value)

async function loadProducts(reset: boolean): Promise<void> {
  if (reset) {
    loading.value = true
    offset.value = 0
  } else {
    loadingMore.value = true
  }

  try {
    const result = await getSellerProducts({
      status: activeTab.value === 'all' ? undefined : activeTab.value,
      limit: PAGE_SIZE,
      offset: reset ? 0 : offset.value,
    })

    products.value = reset ? result.items : [...products.value, ...result.items]
    total.value = result.total
    offset.value = (reset ? 0 : offset.value) + result.items.length
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

function openEditor(product: Product): void {
  editingProduct.value = product
  editorVisible.value = true
}

function onSaved(updated: Product): void {
  const index = products.value.findIndex((p) => p.id === updated.id)
  if (index !== -1) products.value[index] = updated
}

async function onTogglePublish(product: Product): Promise<void> {
  actionLoadingId.value = product.id
  try {
    const updated =
      product.status === 'published' ? await hideProduct(product.id) : await publishProduct(product.id)
    const index = products.value.findIndex((p) => p.id === updated.id)
    if (index !== -1) products.value[index] = updated
  } finally {
    actionLoadingId.value = null
  }
}

watch(activeTab, () => {
  void loadProducts(true)
})

onMounted(() => {
  void loadProducts(true)
})
</script>

<template>
  <div class="mx-auto flex w-full max-w-2xl flex-col gap-4 px-4">
    <h1 class="text-xl font-semibold leading-tight text-sf-ink">Товары</h1>

    <div class="no-scrollbar -mx-4 flex gap-2 overflow-x-auto px-4">
      <button
        v-for="tab in tabs"
        :key="tab.value"
        type="button"
        class="shrink-0 rounded-full border px-3.5 py-1.5 text-sm"
        :class="
          activeTab === tab.value ? 'border-sf-accent bg-sf-accent text-white' : 'border-sf-line bg-sf-card text-sf-ink'
        "
        @click="activeTab = tab.value"
      >
        {{ tab.label }}
      </button>
    </div>

    <p v-if="loading" class="py-16 text-center text-sf-muted">Загрузка…</p>

    <template v-else>
      <div v-if="products.length === 0" class="flex flex-col items-center gap-2 py-16 text-center text-sf-muted">
        <i class="pi pi-box text-4xl" />
        <span>В этом разделе пока нет товаров</span>
      </div>

      <div v-else class="flex flex-col gap-2">
        <article
          v-for="product in products"
          :key="product.id"
          class="flex gap-3 rounded-2xl border border-sf-line bg-sf-card p-3"
        >
          <img
            v-if="product.photo_paths[0]"
            :src="product.photo_paths[0]"
            :alt="product.name"
            class="size-16 shrink-0 rounded-xl object-cover"
            loading="lazy"
          />
          <div v-else class="flex size-16 shrink-0 items-center justify-center rounded-xl bg-sf-bg text-sf-disabled">
            <i class="pi pi-image text-xl" />
          </div>

          <div class="flex min-w-0 flex-1 flex-col">
            <div class="flex items-start justify-between gap-2">
              <h3 class="truncate text-sm font-medium text-sf-ink">{{ product.name }}</h3>
              <span
                class="shrink-0 rounded-full px-2 py-0.5 text-[0.65rem]"
                :class="productStatusChipClasses[product.status]"
              >
                {{ productStatusLabels[product.status] }}
              </span>
            </div>
            <p class="text-sm font-semibold text-sf-ink">{{ product.price ?? 'Цена по запросу' }} {{ product.currency }}</p>
            <p class="text-xs text-sf-muted">{{ product.views_total }} просм.</p>

            <div class="mt-auto flex gap-2 pt-2">
              <button
                type="button"
                class="rounded-full border border-sf-line px-2.5 py-1 text-xs text-sf-ink disabled:opacity-50"
                :disabled="actionLoadingId === product.id"
                @click="openEditor(product)"
              >
                <i class="pi pi-pencil" /> Изменить
              </button>
              <button
                v-if="product.status !== 'published'"
                type="button"
                class="rounded-full border border-sf-line px-2.5 py-1 text-xs text-sf-success disabled:opacity-50"
                :disabled="actionLoadingId === product.id"
                @click="onTogglePublish(product)"
              >
                Опубликовать
              </button>
              <button
                v-else
                type="button"
                class="rounded-full border border-sf-line px-2.5 py-1 text-xs text-sf-ink disabled:opacity-50"
                :disabled="actionLoadingId === product.id"
                @click="onTogglePublish(product)"
              >
                Скрыть
              </button>
            </div>
          </div>
        </article>
      </div>

      <div v-if="hasMore" class="flex justify-center py-2 pb-4">
        <button
          type="button"
          class="rounded-full border border-sf-line bg-sf-card px-5 py-2.5 text-sm font-medium text-sf-ink disabled:opacity-60"
          :disabled="loadingMore"
          @click="loadProducts(false)"
        >
          {{ loadingMore ? 'Загрузка…' : 'Показать ещё' }}
        </button>
      </div>
    </template>

    <ProductEditor v-model:visible="editorVisible" :product="editingProduct" @saved="onSaved" />
  </div>
</template>
