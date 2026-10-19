<script setup lang="ts">
import type { Product } from '@entities/product/types'
import AppModal from '@shared/ui/AppModal.vue'

defineProps<{
  visible: boolean
  product: Product | null
  busy?: boolean
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  confirm: []
}>()

function close(): void {
  emit('update:visible', false)
}
</script>

<template>
  <AppModal :visible="visible" title="Удалить товар" @update:visible="(value: boolean) => emit('update:visible', value)">
    <div class="flex flex-col gap-4">
      <p class="text-sm text-sf-ink">
        Товар «{{ product?.name }}» будет удалён навсегда — вместе с фото, видео и статистикой просмотров.
      </p>

      <!-- A separate warning block, not a small caption under the button —
           this is the one irreversible action in the cabinet. -->
      <p class="rounded-xl bg-sf-danger-soft px-3 py-2 text-sm text-sf-danger" role="alert">
        Восстановить его будет нельзя. Если товар нужен позже — скройте его вместо удаления.
      </p>

      <div class="flex gap-2">
        <button
          type="button"
          class="flex-1 rounded-xl border border-sf-line py-2.5 text-sf-muted"
          @click="close"
        >
          Отмена
        </button>
        <button
          type="button"
          :disabled="busy"
          class="flex-1 rounded-xl bg-sf-danger py-2.5 font-semibold text-white disabled:opacity-50"
          @click="emit('confirm')"
        >
          Удалить навсегда
        </button>
      </div>
    </div>
  </AppModal>
</template>
