<script setup lang="ts">
import type { AxiosError } from 'axios'
import type { Moderator } from '@entities/moderator/types'
import { addModerator, getModerators, removeModerator } from '@entities/moderator/api'

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

onMounted(() => {
  void loadModerators()
})
</script>

<template>
  <div class="mx-auto flex w-full max-w-2xl flex-col gap-4 px-4">
    <div>
      <h1 class="text-xl font-semibold leading-tight text-sf-ink">Команда</h1>
      <p class="text-sm text-sf-muted">
        Доступ ко всему, кроме настроек магазина. Пользователь должен хотя бы раз открыть
        приложение, прежде чем его можно назначить.
      </p>
    </div>

    <div class="flex flex-col gap-3 rounded-2xl bg-white p-3.5 shadow-sm">
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
</template>
