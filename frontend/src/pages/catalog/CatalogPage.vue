<script setup lang="ts">
import type { Product } from '@entities/product/types'
import type { Category } from '@entities/category/types'
import AppSpinner from '@shared/ui/AppSpinner.vue'
import { getCatalogProducts } from '@entities/product/api'
import ProductCard from '@entities/product/ui/ProductCard.vue'
import { useCategoryStore } from '@entities/category/store'
import { useFavoriteStore } from '@entities/favorite/store'
import { useStoreInfoStore } from '@entities/store-info/store'
import { useSeoMeta } from '@shared/seo/useSeoMeta'

const PAGE_SIZE = 20

// Same dark warm-gold tints as the product card tiles, so a category grid
// without icons doesn't read as a grey administrative list.
const TINTS = ['bg-[#201a10]', 'bg-[#1c1c1c]', 'bg-[#22190e]', 'bg-[#1a1a1a]', 'bg-[#241c11]']

const route = useRoute()
const categoryStore = useCategoryStore()
const favoriteStore = useFavoriteStore()
const storeInfoStore = useStoreInfoStore()

const products = ref<Product[]>([])
const total = ref(0)
const offset = ref(0)
const loading = ref(false)
const loadingMore = ref(false)
const search = ref('')
const selectedCategoryId = ref<number | null>(
  route.query.category_id ? Number(route.query.category_id) : null,
)

let searchDebounceHandle: ReturnType<typeof setTimeout> | undefined
let requestToken = 0

const hasMore = computed(() => products.value.length < total.value)

const visibleCategories = computed(() => categoryStore.categories.filter((c) => !c.is_hidden))
const categoriesById = computed(() => new Map(visibleCategories.value.map((c) => [c.id, c])))
const rootCategories = computed(() => visibleCategories.value.filter((c) => c.parent_id === null))

function pathTo(id: number | null): Category[] {
  if (id === null) return []
  const path: Category[] = []
  let current = categoriesById.value.get(id)
  while (current) {
    path.unshift(current)
    current = current.parent_id !== null ? categoriesById.value.get(current.parent_id) : undefined
  }
  return path
}

const selectedPath = computed(() => pathTo(selectedCategoryId.value))
const selectedRoot = computed<Category | undefined>(() => selectedPath.value[0])

const storeName = computed(() => storeInfoStore.storeInfo?.name ?? 'Магазин')

useSeoMeta(() => {
  const categoryName = selectedPath.value.at(-1)?.name
  return {
    title: categoryName
      ? `${categoryName} — Каталог — ${storeName.value}`
      : `Каталог — ${storeName.value}`,
    description: categoryName
      ? `${categoryName}: товары магазина ${storeName.value}`
      : `Весь каталог товаров магазина ${storeName.value}`,
  }
})

const tiles = computed(() => [
  { id: null as number | null, name: 'Все', letter: 'В', tint: TINTS[0] },
  ...rootCategories.value.map((root, index) => ({
    id: root.id,
    name: root.name,
    letter: root.name[0]?.toUpperCase() ?? '',
    tint: TINTS[(index + 1) % TINTS.length],
  })),
])

const chips = computed(() =>
  visibleCategories.value
    .filter((c) => c.parent_id === selectedRoot.value?.id)
    .map((child) => ({
      id: child.id,
      name: child.name,
      active: selectedPath.value.some((node) => node.id === child.id),
    })),
)

const title = computed(() => selectedPath.value.at(-1)?.name ?? 'Товары')

async function loadProducts(reset: boolean): Promise<void> {
  const token = ++requestToken
  if (reset) {
    loading.value = true
    offset.value = 0
  } else {
    loadingMore.value = true
  }

  try {
    const result = await getCatalogProducts({
      search: search.value || undefined,
      category_id: selectedCategoryId.value ?? undefined,
      limit: PAGE_SIZE,
      offset: reset ? 0 : offset.value,
    })

    if (token !== requestToken) return

    products.value = reset ? result.items : [...products.value, ...result.items]
    total.value = result.total
    offset.value = (reset ? 0 : offset.value) + result.items.length
  } finally {
    if (token === requestToken) {
      loading.value = false
      loadingMore.value = false
    }
  }
}

function selectTile(categoryId: number | null): void {
  selectedCategoryId.value = categoryId
}

function selectChip(categoryId: number): void {
  selectedCategoryId.value = selectedCategoryId.value === categoryId ? selectedRoot.value?.id ?? null : categoryId
}

function onSearchInput(): void {
  if (searchDebounceHandle) clearTimeout(searchDebounceHandle)
  searchDebounceHandle = setTimeout(() => {
    void loadProducts(true)
  }, 350)
}

watch(selectedCategoryId, () => {
  void loadProducts(true)
})

onMounted(async () => {
  await Promise.all([
    categoryStore.fetchCategories(),
    favoriteStore.fetchFavorites(),
    loadProducts(true),
  ])
})
</script>

<template>
  <div class="flex flex-col gap-4 px-4 sm:px-6 md:px-8 lg:px-10">
    <div class="flex items-center gap-2">
      <input
        v-model="search"
        type="search"
        placeholder="Поиск по названию или артикулу"
        class="w-full rounded-full border border-sf-line bg-sf-card px-4 py-2.5 text-sm text-sf-ink outline-none placeholder:text-sf-muted focus:border-sf-accent"
        @input="onSearchInput"
      />
    </div>

    <div v-if="tiles.length > 1" class="grid grid-cols-2 gap-2.5 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
      <button
        v-for="tile in tiles"
        :key="tile.id ?? 'all'"
        type="button"
        class="flex min-h-[6.25rem] flex-col justify-between rounded-3xl border p-3.5 text-left transition-colors"
        :class="
          (tile.id === null ? selectedCategoryId === null : selectedRoot?.id === tile.id)
            ? 'border-sf-accent bg-sf-accent text-sf-accent-ink'
            : 'border-sf-line bg-sf-card'
        "
        @click="selectTile(tile.id)"
      >
        <span
          class="flex size-9 shrink-0 items-center justify-center rounded-xl text-sm font-semibold"
          :class="
            (tile.id === null ? selectedCategoryId === null : selectedRoot?.id === tile.id)
              ? 'bg-sf-accent-ink/15 text-sf-accent-ink'
              : [tile.tint, 'text-sf-accent']
          "
        >
          {{ tile.letter }}
        </span>
        <span
          class="block truncate pt-3 text-sm font-medium leading-tight"
          :class="
            (tile.id === null ? selectedCategoryId === null : selectedRoot?.id === tile.id)
              ? 'text-sf-accent-ink'
              : 'text-sf-ink'
          "
        >
          {{ tile.name }}
        </span>
      </button>
    </div>

    <div
      v-if="chips.length > 0"
      class="no-scrollbar -mx-4 flex gap-2 overflow-x-auto px-4 sm:-mx-6 sm:px-6 md:-mx-8 md:px-8 lg:-mx-10 lg:px-10"
    >
      <button
        v-for="chip in chips"
        :key="chip.id"
        type="button"
        class="shrink-0 rounded-full border px-3.5 py-1.5 text-sm"
        :class="chip.active ? 'border-sf-accent bg-sf-accent text-sf-accent-ink' : 'border-sf-line bg-sf-card text-sf-ink'"
        @click="selectChip(chip.id)"
      >
        {{ chip.name }}
      </button>
    </div>

    <div>
      <h1 class="text-xl font-semibold leading-tight text-sf-ink">{{ title }}</h1>
      <p class="text-sm text-sf-muted">Все, что сейчас в продаже</p>
    </div>

    <AppSpinner v-if="loading" />

    <template v-else>
      <div v-if="products.length === 0" class="flex flex-col items-center gap-2 py-16 text-center text-sf-muted">
        <i class="pi pi-box text-4xl" />
        <span>Ничего не найдено</span>
      </div>

      <div v-else class="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6">
        <ProductCard v-for="product in products" :key="product.id" :product="product" />
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
  </div>
</template>
