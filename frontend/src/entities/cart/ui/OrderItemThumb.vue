<script setup lang="ts">
const props = defineProps<{ src: string | null }>()

// The snapshotted path outlives the product: deleting a product removes
// its photo files (ProductService.delete_product), so an old order's
// thumbnail can 404 — show the same placeholder as "no photo at all".
const failed = ref(false)
watch(
  () => props.src,
  () => {
    failed.value = false
  },
)
</script>

<template>
  <img v-if="src && !failed" :src="src" alt="" loading="lazy" class="object-cover" @error="failed = true" />
  <span v-else class="flex items-center justify-center bg-sf-surface text-sf-disabled">
    <i class="pi pi-image text-xs" />
  </span>
</template>
