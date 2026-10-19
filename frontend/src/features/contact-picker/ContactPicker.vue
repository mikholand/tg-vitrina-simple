<script setup lang="ts">
import type { PublicContact } from '@entities/contact/types'
import { contactTypeIcons } from '@entities/contact/labels'
import AppModal from '@shared/ui/AppModal.vue'

defineProps<{
  visible: boolean
  contacts: PublicContact[]
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
}>()

function close(): void {
  emit('update:visible', false)
}

function pick(contact: PublicContact): void {
  close()
  // `noopener,noreferrer` — тот же способ открытия, что уже используется для
  // прямого перехода на единственный контакт на этой странице.
  window.open(contact.url, '_blank', 'noopener,noreferrer')
}
</script>

<template>
  <AppModal :visible="visible" title="Написать продавцу" @update:visible="(value: boolean) => emit('update:visible', value)">
    <ul class="flex flex-col gap-2">
      <li v-for="contact in contacts" :key="contact.id">
        <button
          type="button"
          class="flex w-full items-center gap-3 rounded-2xl border border-sf-line bg-sf-card p-3 text-left active:bg-sf-soft"
          @click="pick(contact)"
        >
          <span class="flex size-10 shrink-0 items-center justify-center rounded-full bg-sf-soft text-sf-accent">
            <i class="pi" :class="contactTypeIcons[contact.type]" />
          </span>
          <span class="min-w-0 flex-1">
            <span class="block truncate text-sm font-medium leading-tight text-sf-ink">{{ contact.label }}</span>
            <span class="block truncate text-sm text-sf-muted">{{ contact.value }}</span>
          </span>
          <i class="pi pi-chevron-right shrink-0 text-xs text-sf-disabled" />
        </button>
      </li>
    </ul>
  </AppModal>
</template>
