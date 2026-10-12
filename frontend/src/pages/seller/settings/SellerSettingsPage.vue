<script setup lang="ts">
import type { SellerSettings } from '@entities/seller-settings/types'
import { getSellerSettings, updateSellerSettings, uploadStoreLogo } from '@entities/seller-settings/api'

const settings = ref<SellerSettings | null>(null)
const loading = ref(true)
const saving = ref(false)
const uploadingLogo = ref(false)
const savedAt = ref<number | null>(null)
const error = ref<string | null>(null)

const name = ref('')
const description = ref('')
const contactTg = ref('')

const fileInput = ref<HTMLInputElement | null>(null)

function applySettings(value: SellerSettings): void {
  settings.value = value
  name.value = value.store_name
  description.value = value.store_description
  contactTg.value = value.store_contact_tg ?? ''
}

onMounted(async () => {
  try {
    applySettings(await getSellerSettings())
  } finally {
    loading.value = false
  }
})

async function onSave(): Promise<void> {
  saving.value = true
  error.value = null
  try {
    applySettings(
      await updateSellerSettings({
        name: name.value,
        description: description.value,
        contact_tg: contactTg.value,
      }),
    )
    savedAt.value = Date.now()
  } catch {
    error.value = 'Не удалось сохранить изменения'
  } finally {
    saving.value = false
  }
}

function triggerFilePicker(): void {
  fileInput.value?.click()
}

async function onLogoSelected(event: Event): Promise<void> {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  target.value = ''
  if (!file) return

  uploadingLogo.value = true
  error.value = null
  try {
    applySettings(await uploadStoreLogo(file))
  } catch {
    error.value = 'Не удалось загрузить логотип'
  } finally {
    uploadingLogo.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-4 px-4">
    <h1 class="text-xl font-semibold leading-tight text-sf-ink">Настройки магазина</h1>

    <p v-if="loading" class="py-16 text-center text-sf-muted">Загрузка…</p>

    <div v-else-if="settings" class="flex flex-col gap-3">
      <div class="flex items-center gap-3 rounded-2xl border border-sf-line bg-sf-card p-3.5">
        <button
          type="button"
          class="relative flex size-14 shrink-0 items-center justify-center overflow-hidden rounded-full bg-sf-accent text-sm font-semibold text-white disabled:opacity-60"
          :disabled="uploadingLogo"
          @click="triggerFilePicker"
        >
          <img
            v-if="settings.store_logo"
            :src="settings.store_logo"
            :alt="name"
            class="size-full object-cover"
          />
          <span v-else>{{ name[0]?.toUpperCase() }}</span>
          <span
            class="absolute inset-0 flex items-center justify-center bg-black/40 text-white"
            :class="uploadingLogo ? 'opacity-100' : 'opacity-0 transition-opacity hover:opacity-100'"
          >
            <i v-if="!uploadingLogo" class="pi pi-camera text-sm" />
            <i v-else class="pi pi-spin pi-spinner text-sm" />
          </span>
        </button>
        <input ref="fileInput" type="file" accept="image/*" class="hidden" @change="onLogoSelected" />
        <div class="min-w-0 flex-1 text-xs text-sf-muted">
          Нажмите на логотип, чтобы загрузить новое изображение
        </div>
      </div>

      <div class="flex flex-col gap-3 rounded-2xl border border-sf-line bg-sf-card p-3.5">
        <label class="flex flex-col gap-1 text-sm">
          <span class="text-sf-muted">Название магазина</span>
          <InputText v-model="name" />
        </label>

        <label class="flex flex-col gap-1 text-sm">
          <span class="text-sf-muted">Описание</span>
          <Textarea v-model="description" auto-resize rows="3" />
        </label>

        <label class="flex flex-col gap-1 text-sm">
          <span class="text-sf-muted">Контакт (Telegram)</span>
          <InputText v-model="contactTg" placeholder="@username" />
        </label>

        <p v-if="error" class="text-xs text-sf-danger">{{ error }}</p>
        <p v-else-if="savedAt" class="text-xs text-sf-success">Сохранено</p>

        <button
          type="button"
          class="flex items-center justify-center gap-1.5 rounded-full bg-sf-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
          :disabled="saving"
          @click="onSave"
        >
          <i v-if="saving" class="pi pi-spin pi-spinner text-xs" />
          Сохранить
        </button>
      </div>

      <div class="flex flex-col gap-2 rounded-2xl border border-sf-line bg-sf-card p-3.5 text-sm">
        <div class="flex items-center justify-between gap-2">
          <span class="text-sf-muted">ID канала Telegram</span>
          <span class="truncate text-sf-ink">{{ settings.telegram_channel_id }}</span>
        </div>
        <div class="flex items-center justify-between gap-2">
          <span class="text-sf-muted">Экстрактор настроен</span>
          <span
            class="shrink-0 rounded-full px-2 py-0.5 text-[0.65rem]"
            :class="settings.extractor_configured ? 'bg-sf-success-soft text-sf-success' : 'bg-sf-danger-soft text-sf-danger'"
          >
            {{ settings.extractor_configured ? 'Да' : 'Нет' }}
          </span>
        </div>
        <p class="text-xs text-sf-muted">
          Эти два параметра заданы на сервере переменными окружения и не редактируются здесь.
        </p>
      </div>
    </div>
  </div>
</template>
