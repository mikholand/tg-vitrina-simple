<script setup lang="ts">
import type { Category } from '@entities/category/types'
import {
  createSellerCategory,
  deleteSellerCategory,
  getSellerCategories,
  setCategoryVisibility,
} from '@entities/category/api'

const categories = ref<Category[]>([])
const loading = ref(true)
const togglingId = ref<number | null>(null)
const deletingId = ref<number | null>(null)

const createDialogVisible = ref(false)
const creating = ref(false)
const newCategoryName = ref('')
const newCategoryParentId = ref<number | null>(null)

const sortedCategories = computed(() =>
  [...categories.value].sort((a, b) => a.depth - b.depth || a.sort_order - b.sort_order),
)

const parentOptions = computed(() => [
  { label: 'Без родителя', value: null },
  ...sortedCategories.value.map((c) => ({ label: c.name, value: c.id })),
])

async function loadCategories(): Promise<void> {
  loading.value = true
  try {
    categories.value = await getSellerCategories()
  } finally {
    loading.value = false
  }
}

async function onToggleHidden(category: Category, isHidden: boolean): Promise<void> {
  togglingId.value = category.id
  try {
    const updated = await setCategoryVisibility(category.id, isHidden)
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
      <div>
        <h1 class="text-xl font-semibold leading-tight text-sf-ink">Категории</h1>
        <p class="text-sm text-sf-muted">Общий справочник — скрывайте то, чего не продаёте</p>
      </div>
      <Button label="Добавить" icon="pi pi-plus" size="small" @click="openCreateDialog" />
    </div>

    <p v-if="loading" class="py-16 text-center text-sf-muted">Загрузка…</p>

    <div v-else class="flex flex-col gap-2">
      <div
        v-for="category in sortedCategories"
        :key="category.id"
        class="flex items-center justify-between gap-2 rounded-2xl border border-sf-line bg-sf-card p-3"
        :class="category.is_hidden ? 'opacity-60' : ''"
        :style="{ marginLeft: `${category.depth * 12}px` }"
      >
        <div class="flex min-w-0 flex-col">
          <span class="truncate text-sm text-sf-ink">{{ category.name }}</span>
          <span v-if="category.is_fallback" class="text-xs text-sf-muted">Категория по умолчанию</span>
        </div>

        <div class="flex items-center gap-2">
          <ToggleSwitch
            :model-value="!category.is_hidden"
            :disabled="togglingId === category.id"
            @update:model-value="(value: boolean) => onToggleHidden(category, !value)"
          />
          <button
            v-if="!category.is_fallback"
            type="button"
            class="flex h-8 w-8 items-center justify-center rounded-full text-sf-muted disabled:opacity-50"
            :disabled="deletingId === category.id"
            @click="onDeleteCategory(category)"
          >
            <i v-if="deletingId !== category.id" class="pi pi-trash" />
            <i v-else class="pi pi-spin pi-spinner" />
          </button>
        </div>
      </div>
    </div>

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
