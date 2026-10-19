<script setup lang="ts">
import type { Contact, ContactType } from '@entities/contact/types'
import { createContact, deleteContact, getSellerContacts, updateContact } from '@entities/contact/api'
import {
  contactTypeIcons,
  contactTypeValueLabels,
  contactTypeValuePlaceholders,
} from '@entities/contact/labels'

// Та же граница, что и на сервере (`MAX_CONTACTS`) — только для подсказки в
// форме, настоящий лимит проверяет бэкенд.
const MAX_CONTACTS = 10

const contacts = ref<Contact[]>([])
const loading = ref(true)
const saving = ref(false)
const togglingId = ref<number | null>(null)
const deletingId = ref<number | null>(null)
const error = ref<string | null>(null)

const label = ref('')
const type = ref<ContactType>('telegram')
const value = ref('')

const canSubmit = computed(
  () => Boolean(label.value.trim()) && Boolean(value.value.trim()) && contacts.value.length < MAX_CONTACTS,
)

async function load(): Promise<void> {
  loading.value = true
  try {
    contacts.value = await getSellerContacts()
  } finally {
    loading.value = false
  }
}

async function onAdd(): Promise<void> {
  if (!canSubmit.value || saving.value) return
  saving.value = true
  error.value = null
  try {
    const created = await createContact({
      label: label.value.trim(),
      type: type.value,
      value: value.value.trim(),
    })
    contacts.value = [...contacts.value, created]
    label.value = ''
    value.value = ''
  } catch {
    error.value = 'Не удалось добавить менеджера'
  } finally {
    saving.value = false
  }
}

async function onToggleActive(contact: Contact): Promise<void> {
  togglingId.value = contact.id
  error.value = null
  try {
    const updated = await updateContact(contact.id, { is_active: !contact.is_active })
    const index = contacts.value.findIndex((c) => c.id === updated.id)
    if (index !== -1) contacts.value[index] = updated
  } catch {
    error.value = 'Не удалось изменить менеджера'
  } finally {
    togglingId.value = null
  }
}

async function onRemove(contact: Contact): Promise<void> {
  deletingId.value = contact.id
  error.value = null
  try {
    await deleteContact(contact.id)
    contacts.value = contacts.value.filter((c) => c.id !== contact.id)
  } catch {
    error.value = 'Не удалось удалить менеджера'
  } finally {
    deletingId.value = null
  }
}

onMounted(load)
</script>

<template>
  <div class="mx-auto flex w-full max-w-2xl flex-col gap-4 px-4">
    <div>
      <h1 class="text-xl font-semibold leading-tight text-sf-ink">Менеджеры</h1>
      <p class="text-sm text-sf-muted">
        Кому покупатель пишет из карточки товара — имя он увидит в списке выбора. Если менеджер
        один, кнопка «Написать продавцу» сразу ведёт к нему.
      </p>
    </div>

    <p v-if="loading" class="py-16 text-center text-sf-muted">Загрузка…</p>

    <template v-else>
      <div
        v-if="!contacts.length"
        class="flex flex-col items-center gap-2 rounded-2xl bg-white py-12 text-center text-sf-muted shadow-sm"
      >
        <i class="pi pi-users text-3xl" />
        <span>Пока никого не добавили</span>
      </div>

      <ul v-else class="flex flex-col gap-2">
        <li
          v-for="contact in contacts"
          :key="contact.id"
          class="flex items-center gap-3 rounded-2xl bg-white p-3 shadow-sm"
        >
          <span class="flex size-10 shrink-0 items-center justify-center rounded-full bg-sf-soft text-sf-accent">
            <i class="pi" :class="contactTypeIcons[contact.type]" />
          </span>
          <div class="min-w-0 flex-1" :class="contact.is_active ? '' : 'opacity-50'">
            <p class="truncate text-sm font-medium leading-tight text-sf-ink">{{ contact.label }}</p>
            <p class="truncate text-sm text-sf-muted">{{ contact.value }}</p>
          </div>
          <button
            type="button"
            class="shrink-0 text-sm text-sf-muted disabled:opacity-50"
            :disabled="togglingId === contact.id"
            @click="onToggleActive(contact)"
          >
            {{ contact.is_active ? 'Скрыть' : 'Показать' }}
          </button>
          <button
            type="button"
            class="shrink-0 text-sf-danger disabled:opacity-50"
            aria-label="Удалить"
            :disabled="deletingId === contact.id"
            @click="onRemove(contact)"
          >
            <i v-if="deletingId !== contact.id" class="pi pi-trash" />
            <i v-else class="pi pi-spin pi-spinner" />
          </button>
        </li>
      </ul>

      <div class="flex flex-col gap-3 rounded-2xl bg-white p-3.5 shadow-sm">
        <h2 class="text-sm font-medium text-sf-ink">Добавить менеджера</h2>

        <label class="flex flex-col gap-1 text-sm">
          <span class="text-sf-muted">Имя менеджера</span>
          <InputText v-model="label" placeholder="Например: Анна, отдел продаж" maxlength="100" fluid />
        </label>

        <label class="flex flex-col gap-1 text-sm">
          <span class="text-sf-muted">Способ связи</span>
          <Select
            v-model="type"
            :options="[
              { label: 'Telegram', value: 'telegram' },
              { label: 'Телефон', value: 'phone' },
            ]"
            option-label="label"
            option-value="value"
            fluid
          />
        </label>

        <label class="flex flex-col gap-1 text-sm">
          <span class="text-sf-muted">{{ contactTypeValueLabels[type] }}</span>
          <InputText
            v-model="value"
            :placeholder="contactTypeValuePlaceholders[type]"
            maxlength="200"
            fluid
            @keyup.enter="onAdd"
          />
        </label>

        <Message v-if="error" severity="error" :closable="false">{{ error }}</Message>

        <Button label="Добавить" :loading="saving" :disabled="!canSubmit" fluid @click="onAdd" />

        <span v-if="contacts.length >= MAX_CONTACTS" class="text-center text-xs text-sf-muted">
          Больше {{ MAX_CONTACTS }} менеджеров витрина не покажет.
        </span>
      </div>
    </template>
  </div>
</template>
