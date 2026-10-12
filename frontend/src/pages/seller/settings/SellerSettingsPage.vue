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
          class="relative shrink-0 overflow-hidden rounded-full disabled:opacity-60"
          :disabled="uploadingLogo"
          @click="triggerFilePicker"
        >
          <Avatar
            :image="settings.store_logo ?? undefined"
            :label="settings.store_logo ? undefined : name[0]?.toUpperCase()"
            shape="circle"
            size="xlarge"
            style="background-color: var(--sf-accent); color: #fff"
          />
          <span
            class="absolute inset-0 flex items-center justify-center rounded-full bg-black/40 text-white"
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
          <InputText v-model="name" fluid />
        </label>

        <label class="flex flex-col gap-1 text-sm">
          <span class="text-sf-muted">Описание</span>
          <Textarea v-model="description" auto-resize rows="3" fluid />
        </label>

        <label class="flex flex-col gap-1 text-sm">
          <span class="text-sf-muted">Контакт (Telegram)</span>
          <IconField>
            <InputIcon class="pi pi-at" />
            <InputText v-model="contactTg" placeholder="username" fluid />
          </IconField>
        </label>

        <Message v-if="error" severity="error" :closable="false">{{ error }}</Message>
        <Message v-else-if="savedAt" severity="success" :closable="false">Сохранено</Message>

        <Button label="Сохранить" :loading="saving" fluid @click="onSave" />
      </div>

      <div class="flex flex-col gap-2 rounded-2xl border border-sf-line bg-sf-card p-3.5 text-sm">
        <div class="flex items-center justify-between gap-2">
          <span class="text-sf-muted">ID канала Telegram</span>
          <span class="truncate text-sf-ink">{{ settings.telegram_channel_id }}</span>
        </div>
        <div class="flex items-center justify-between gap-2">
          <span class="text-sf-muted">Экстрактор настроен</span>
          <Tag
            :severity="settings.extractor_configured ? 'success' : 'danger'"
            :value="settings.extractor_configured ? 'Да' : 'Нет'"
            rounded
          />
        </div>
        <p class="text-xs text-sf-muted">
          Эти два параметра заданы на сервере переменными окружения и не редактируются здесь.
        </p>
      </div>
    </div>
  </div>
</template>
