<script setup lang="ts">
import type { AxiosError } from 'axios'
import type { SellerSettings } from '@entities/seller-settings/types'
import { getSellerSettings, updateSellerSettings, uploadStoreLogo } from '@entities/seller-settings/api'
import type { Moderator } from '@entities/moderator/types'
import { addModerator, getModerators, removeModerator } from '@entities/moderator/api'

const settings = ref<SellerSettings | null>(null)
const loading = ref(true)
const saving = ref(false)
const uploadingLogo = ref(false)
const savedAt = ref<number | null>(null)
const error = ref<string | null>(null)

const moderators = ref<Moderator[]>([])
const moderatorsLoading = ref(true)
const newModeratorId = ref('')
const addingModerator = ref(false)
const removingId = ref<number | null>(null)
const moderatorError = ref<string | null>(null)

function moderatorLabel(moderator: Moderator): string {
  if (moderator.tg_username) return moderator.tg_username
  const fullName = [moderator.tg_first_name, moderator.tg_last_name].filter(Boolean).join(' ')
  return fullName || `ID ${moderator.id}`
}

async function loadModerators(): Promise<void> {
  moderatorsLoading.value = true
  try {
    moderators.value = await getModerators()
  } finally {
    moderatorsLoading.value = false
  }
}

async function onAddModerator(): Promise<void> {
  const userId = Number(newModeratorId.value.trim())
  if (!Number.isInteger(userId) || userId <= 0) {
    moderatorError.value = 'Укажите корректный Telegram ID'
    return
  }

  addingModerator.value = true
  moderatorError.value = null
  try {
    const moderator = await addModerator(userId)
    moderators.value = [...moderators.value, moderator]
    newModeratorId.value = ''
  } catch (err) {
    const detail = (err as AxiosError<{ detail?: string }>).response?.data?.detail
    if (detail === 'user_not_found_must_open_app_first') {
      moderatorError.value = 'Этот пользователь ещё не открывал приложение'
    } else if (detail === 'user_is_owner') {
      moderatorError.value = 'Этот пользователь уже владелец магазина'
    } else {
      moderatorError.value = 'Не удалось добавить модератора'
    }
  } finally {
    addingModerator.value = false
  }
}

async function onRemoveModerator(moderator: Moderator): Promise<void> {
  removingId.value = moderator.id
  moderatorError.value = null
  try {
    await removeModerator(moderator.id)
    moderators.value = moderators.value.filter((m) => m.id !== moderator.id)
  } catch {
    moderatorError.value = 'Не удалось убрать модератора'
  } finally {
    removingId.value = null
  }
}

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
  void loadModerators()
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
  <div class="mx-auto flex w-full max-w-2xl flex-col gap-4 px-4">
    <h1 class="text-xl font-semibold leading-tight text-sf-ink">Настройки магазина</h1>

    <p v-if="loading" class="py-16 text-center text-sf-muted">Загрузка…</p>

    <div v-else-if="settings" class="flex flex-col gap-3">
      <div class="flex items-center gap-3 rounded-2xl border border-sf-line bg-sf-card p-3.5">
        <button
          type="button"
          class="relative shrink-0 appearance-none overflow-hidden rounded-full border-0 bg-transparent p-0 shadow-none outline-none disabled:opacity-60"
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

      <div class="flex flex-col gap-3 rounded-2xl border border-sf-line bg-sf-card p-3.5">
        <div>
          <h2 class="text-sm font-medium text-sf-ink">Модераторы</h2>
          <p class="text-xs text-sf-muted">
            Доступ ко всему, кроме этой страницы настроек. Пользователь должен хотя бы раз открыть
            приложение, прежде чем его можно назначить.
          </p>
        </div>

        <p v-if="moderatorsLoading" class="py-4 text-center text-sm text-sf-muted">Загрузка…</p>

        <div v-else-if="moderators.length > 0" class="flex flex-col gap-2">
          <div
            v-for="moderator in moderators"
            :key="moderator.id"
            class="flex items-center justify-between gap-2 rounded-xl border border-sf-line p-2.5"
          >
            <span class="truncate text-sm text-sf-ink">{{ moderatorLabel(moderator) }}</span>
            <Button
              icon="pi pi-times"
              severity="danger"
              text
              :loading="removingId === moderator.id"
              @click="onRemoveModerator(moderator)"
            />
          </div>
        </div>
        <p v-else class="text-sm text-sf-muted">Модераторов пока нет</p>

        <div class="flex items-center gap-2">
          <InputText
            v-model="newModeratorId"
            placeholder="Telegram ID"
            inputmode="numeric"
            fluid
            @keyup.enter="onAddModerator"
          />
          <Button icon="pi pi-plus" :loading="addingModerator" @click="onAddModerator" />
        </div>

        <Message v-if="moderatorError" severity="error" :closable="false">{{ moderatorError }}</Message>
      </div>
    </div>
  </div>
</template>
