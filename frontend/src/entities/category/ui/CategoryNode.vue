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

// tg-vitrina's catalog is shared platform-wide (hundreds of nodes), so its
// tree starts collapsed. A single shop's catalog here is a handful of
// branches — collapsing by default would hide the very nesting this view
// exists to show off, so it starts open; a seller with a deep branch can
// still fold it away.
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
