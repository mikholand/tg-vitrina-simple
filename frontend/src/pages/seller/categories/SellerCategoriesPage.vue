<script setup lang="ts">
import type { Category, CategoryTreeNode } from '@entities/category/types'
import {
  createSellerCategory,
  deleteSellerCategory,
  getSellerCategories,
  setCategoryVisibility,
} from '@entities/category/api'
import { buildCategoryTree } from '@entities/category/tree'
import CategoryNode from '@entities/category/ui/CategoryNode.vue'

const categories = ref<Category[]>([])
const loading = ref(true)
const togglingId = ref<number | null>(null)
const deletingId = ref<number | null>(null)
const query = ref('')

const createDialogVisible = ref(false)
const creating = ref(false)
const newCategoryName = ref('')
const newCategoryParentId = ref<number | null>(null)

const sortedCategories = computed(() =>
  [...categories.value].sort((a, b) => a.depth - b.depth || a.sort_order - b.sort_order),
)

const tree = computed<CategoryTreeNode[]>(() => buildCategoryTree(categories.value))

const parentOptions = computed(() => [
  { label: 'Без родителя', value: null },
  ...sortedCategories.value.map((c) => ({ label: `${'— '.repeat(c.depth)}${c.name}`, value: c.id })),
])

// Путь от корня для каждой категории («Одежда → Куртки») — в результатах
// поиска совпадение из глубины дерева иначе не опознать, а дерево под
// найденное разворачивать не хочется (см. CategoryNode).
const pathById = computed<Map<number, string>>(() => {
  const byId = new Map(categories.value.map((c) => [c.id, c]))
  const paths = new Map<number, string>()
  function pathOf(category: Category): string {
    const cached = paths.get(category.id)
    if (cached) return cached
    const parent = category.parent_id !== null ? byId.get(category.parent_id) : undefined
    const path = parent ? `${pathOf(parent)} → ${category.name}` : category.name
    paths.set(category.id, path)
    return path
  }
  for (const category of categories.value) pathOf(category)
  return paths
})

const found = computed<Category[]>(() => {
  const needle = query.value.trim().toLowerCase()
  if (!needle) return []
  return sortedCategories.value.filter((c) => c.name.toLowerCase().includes(needle))
})

async function loadCategories(): Promise<void> {
  loading.value = true
  try {
    categories.value = await getSellerCategories()
  } finally {
    loading.value = false
  }
}

async function onToggleVisibility(category: Category): Promise<void> {
  togglingId.value = category.id
  try {
    const updated = await setCategoryVisibility(category.id, !category.is_hidden)
    const index = categories.value.findIndex((c) => c.id === updated.id)
    if (index !== -1) categories.value[index] = updated
  } finally {
    togglingId.value = null
  }
}

function openCreateDialog(): void {
  newCategoryName.value = ''
  newCategoryParentId.value = null
  createDialogVisible.value = true
}

async function onCreateCategory(): Promise<void> {
  if (!newCategoryName.value.trim()) return

  creating.value = true
  try {
    await createSellerCategory({
      name: newCategoryName.value.trim(),
      parent_id: newCategoryParentId.value,
    })
    createDialogVisible.value = false
    await loadCategories()
  } finally {
    creating.value = false
  }
}

async function onDeleteCategory(category: Category): Promise<void> {
  if (!window.confirm(`Удалить категорию «${category.name}»? Подкатегории будут удалены вместе с ней.`)) {
    return
  }

  deletingId.value = category.id
  try {
    await deleteSellerCategory(category.id)
    await loadCategories()
  } finally {
    deletingId.value = null
  }
}

onMounted(() => {
  void loadCategories()
})
</script>

<template>
  <div class="mx-auto flex w-full max-w-2xl flex-col gap-4 px-4">
    <div class="flex items-start justify-between gap-2">
      <div class="min-w-0">
        <h1 class="text-xl font-semibold leading-tight text-sf-ink">Категории</h1>
        <p class="text-sm text-sf-muted">Каталог вашего магазина — скрывайте то, чего не продаёте</p>
      </div>
      <Button label="Добавить" icon="pi pi-plus" size="small" class="shrink-0" @click="openCreateDialog" />
    </div>

    <p v-if="loading" class="py-16 text-center text-sf-muted">Загрузка…</p>

    <template v-else>
      <input
        v-model="query"
        type="search"
        placeholder="Поиск категории"
        class="w-full rounded-xl border border-sf-line bg-white px-3 py-2 text-sm text-sf-ink outline-none placeholder:text-sf-placeholder focus:border-sf-accent"
      />

      <!-- Поиск идёт по всему каталогу и потому отвечает плоским списком с
           путём от корня — дерево, в котором разворачивать пришлось бы
           каждую ветку вручную ради одного совпадения, только мешало бы. -->
      <ul v-if="query.trim()" class="flex flex-col gap-2">
        <li
          v-for="category in found"
          :key="category.id"
          class="flex items-center gap-2 rounded-xl border border-sf-line bg-white px-3 py-2"
          :class="category.is_hidden ? 'opacity-60' : ''"
        >
          <span class="min-w-0 flex-1 truncate text-sm text-sf-ink">{{ pathById.get(category.id) }}</span>
          <button
            type="button"
            class="shrink-0 text-sf-muted disabled:opacity-50"
            :aria-label="category.is_hidden ? 'Показывать' : 'Скрыть'"
            :disabled="togglingId === category.id"
            @click="onToggleVisibility(category)"
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
            @click="onDeleteCategory(category)"
          >
            <i v-if="deletingId !== category.id" class="pi pi-trash text-sm" />
            <i v-else class="pi pi-spin pi-spinner text-sm" />
          </button>
        </li>
        <li v-if="!found.length" class="py-8 text-center text-sm text-sf-muted">Ничего не найдено</li>
      </ul>

      <ul v-else class="flex flex-col gap-2">
        <CategoryNode
          v-for="node in tree"
          :key="node.id"
          :category="node"
          :toggling-id="togglingId"
          :deleting-id="deletingId"
          @toggle-visibility="onToggleVisibility"
          @delete="onDeleteCategory"
        />
      </ul>
    </template>

    <Dialog v-model:visible="createDialogVisible" modal header="Новая категория" class="w-[90vw] max-w-sm">
      <div class="flex flex-col gap-4">
        <label class="flex flex-col gap-1.5 text-sm">
          <span class="text-sf-muted">Название</span>
          <InputText v-model="newCategoryName" fluid />
        </label>
        <label class="flex flex-col gap-1.5 text-sm">
          <span class="text-sf-muted">Родительская категория</span>
          <Select
            v-model="newCategoryParentId"
            :options="parentOptions"
            option-label="label"
            option-value="value"
            fluid
          />
        </label>
      </div>

      <template #footer>
        <Button label="Отмена" text @click="createDialogVisible = false" />
        <Button
          label="Создать"
          :loading="creating"
          :disabled="!newCategoryName.trim()"
          @click="onCreateCategory"
        />
      </template>
    </Dialog>
  </div>
</template>
