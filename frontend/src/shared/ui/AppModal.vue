<script setup lang="ts">
defineProps<{
  visible: boolean
  title: string
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
}>()

function close(): void {
  emit('update:visible', false)
}
</script>

<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div
        v-if="visible"
        class="fixed inset-0 z-50 flex items-end justify-center bg-black/40"
        @click.self="close"
      >
        <div class="max-h-[90vh] w-full max-w-web-app overflow-y-auto rounded-t-2xl bg-sf-card pb-safe-bottom">
          <header class="sticky top-0 flex items-center justify-between border-b border-sf-line bg-sf-card px-4 py-3">
            <h2 class="text-base font-semibold text-sf-ink">{{ title }}</h2>
            <button type="button" class="text-sf-muted" aria-label="Закрыть" @click="close">
              <i class="pi pi-times text-lg" />
            </button>
          </header>
          <div class="px-4 py-4">
            <slot />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}
.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
</style>
