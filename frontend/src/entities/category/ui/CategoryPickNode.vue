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

/**
 * How many are ticked inside a collapsed branch — otherwise a pick buried
 * deep in the tree disappears from view, and the seller either thinks
 * nothing is selected or hunts for it across every node.
 */
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
