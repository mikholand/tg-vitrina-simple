<script setup lang="ts">
import type { Product, ProductStatus } from '@entities/product/types'
import { deleteProduct, getSellerProducts, hideProduct, publishProduct } from '@entities/product/api'
import { productStatusChipClasses, productStatusLabels } from '@entities/product/labels'
import ProductEditor from '@features/product-editor/ProductEditor.vue'
import DeleteConfirm from '@features/product-delete/DeleteConfirm.vue'

const PAGE_SIZE = 20
const SEARCH_DEBOUNCE_MS = 300

type StatusFilter = ProductStatus | 'all'

const tabs: { label: string; value: StatusFilter }[] = [
  { label: 'Все', value: 'all' },
  { label: 'Черновики', value: 'draft' },
  { label: 'Опубликованные', value: 'published' },
  { label: 'Скрытые', value: 'hidden' },
]

const activeTab = ref<StatusFilter>('all')
const search = ref('')
const products = ref<Product[]>([])
const total = ref(0)
const offset = ref(0)
const loading = ref(true)
const loadingMore = ref(false)
const actionLoadingId = ref<number | null>(null)
const editorVisible = ref(false)
const editingProduct = ref<Product | null>(null)
const deleteVisible = ref(false)
const deletingProduct = ref<Product | null>(null)
const deleting = ref(false)

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
      q: search.value.trim() || undefined,
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

function openCreateEditor(): void {
  editingProduct.value = null
  editorVisible.value = true
}

function onSaved(updated: Product): void {
  const index = products.value.findIndex((p) => p.id === updated.id)
  if (index !== -1) {
    products.value[index] = updated
  } else {
    products.value = [updated, ...products.value]
    total.value += 1
  }
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

function askDelete(product: Product): void {
  deletingProduct.value = product
  deleteVisible.value = true
}

async function confirmDelete(): Promise<void> {
  const target = deletingProduct.value
  if (!target) return
  deleting.value = true
  try {
    await deleteProduct(target.id)
    deleteVisible.value = false
    products.value = products.value.filter((p) => p.id !== target.id)
    total.value -= 1
  } finally {
    deleting.value = false
  }
}

let searchTimer: ReturnType<typeof setTimeout> | undefined
watch(search, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => loadProducts(true), SEARCH_DEBOUNCE_MS)
})

watch(activeTab, () => {
  void loadProducts(true)
})

onMounted(() => {
  void loadProducts(true)
})
</script>

<template>
  <div class="mx-auto flex w-full max-w-2xl flex-col gap-4 px-4">
    <div class="flex items-center justify-between gap-2">
      <h1 class="text-xl font-semibold leading-tight text-sf-ink">Товары</h1>
      <!-- Plain button, not PrimeVue <Button> — the latter is pinned to a full
           pill (rounded-full) app-wide via the theme preset, which every other
           page's primary action intentionally keeps; this page's reference
           design wants a rounded rectangle instead. -->
      <button
        type="button"
        class="flex shrink-0 items-center gap-1 rounded-lg bg-sf-accent px-3 py-1.5 text-sm font-medium text-white"
        @click="openCreateEditor"
      >
        <i class="pi pi-plus text-xs" /> Добавить
      </button>
    </div>

    <div class="no-scrollbar -mx-4 flex gap-2 overflow-x-auto px-4">
      <button
        v-for="tab in tabs"
        :key="tab.value"
        type="button"
        class="shrink-0 rounded-full border px-3.5 py-1 text-sm"
        :class="
          activeTab === tab.value ? 'border-sf-accent bg-sf-accent text-white' : 'border-sf-line bg-sf-card text-sf-ink'
        "
        @click="activeTab = tab.value"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Shared storage can grow past a quick scroll — search narrows it to
         what the seller is actually looking for. -->
    <input
      v-model="search"
      type="search"
      placeholder="Поиск по названию"
      class="rounded-xl border border-sf-line bg-white px-3 py-2 text-sm text-sf-ink outline-none placeholder:text-sf-placeholder focus:border-sf-accent"
    />

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
          class="flex gap-3 rounded-2xl bg-white p-3 shadow-sm"
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

            <div class="mt-auto flex items-center gap-2 pt-2">
              <button
                type="button"
                class="rounded-lg border border-sf-line px-2 py-1 text-xs text-sf-ink disabled:opacity-50"
                :disabled="actionLoadingId === product.id"
                @click="openEditor(product)"
              >
                <i class="pi pi-pencil" /> Изменить
              </button>
              <button
                v-if="product.status !== 'published'"
                type="button"
                class="rounded-lg border border-sf-line px-2 py-1 text-xs text-sf-success disabled:opacity-50"
                :disabled="actionLoadingId === product.id"
                @click="onTogglePublish(product)"
              >
                Опубликовать
              </button>
              <button
                v-else
                type="button"
                class="rounded-lg border border-sf-line px-2 py-1 text-xs text-sf-ink disabled:opacity-50"
                :disabled="actionLoadingId === product.id"
                @click="onTogglePublish(product)"
              >
                Скрыть
              </button>
              <!-- Rightmost and borderless: an irreversible action shouldn't
                   sit flush against "Изменить" and catch a mis-tap. -->
              <button
                type="button"
                class="ml-auto rounded-lg px-2 py-1 text-xs text-sf-danger disabled:opacity-50"
                :disabled="actionLoadingId === product.id"
                aria-label="Удалить товар"
                @click="askDelete(product)"
              >
                <i class="pi pi-trash" />
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

    <DeleteConfirm
      :visible="deleteVisible"
      :product="deletingProduct"
      :busy="deleting"
      @update:visible="deleteVisible = $event"
      @confirm="confirmDelete"
    />
  </div>
</template>
