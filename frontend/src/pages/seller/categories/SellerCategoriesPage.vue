<script setup lang="ts">
import type { Category } from '@entities/category/types'
import { getSellerCategories, setCategoryVisibility } from '@entities/category/api'

const categories = ref<Category[]>([])
const loading = ref(true)
const togglingId = ref<number | null>(null)

const sortedCategories = computed(() =>
  [...categories.value].sort((a, b) => a.depth - b.depth || a.sort_order - b.sort_order),
)

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

onMounted(() => {
  void loadCategories()
})
</script>

<template>
  <div class="flex flex-col gap-4 px-4">
    <div>
      <h1 class="text-xl font-semibold leading-tight text-sf-ink">Категории</h1>
      <p class="text-sm text-sf-muted">Общий справочник — скрывайте то, чего не продаёте</p>
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

        <ToggleSwitch
          :model-value="!category.is_hidden"
          :disabled="togglingId === category.id"
          @update:model-value="(value: boolean) => onToggleHidden(category, !value)"
        />
      </div>
    </div>
  </div>
</template>
