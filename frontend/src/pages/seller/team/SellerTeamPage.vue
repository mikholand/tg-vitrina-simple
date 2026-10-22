<script setup lang="ts">
import type { Moderator } from '@entities/moderator/types'
import AppSpinner from '@shared/ui/AppSpinner.vue'
import { getModerators, removeModerator } from '@entities/moderator/api'
import type { Invite } from '@entities/invite/types'
import { createInvite, getActiveInvite } from '@entities/invite/api'
import { shareLink } from '@shared/telegram/sdk'

const moderators = ref<Moderator[]>([])
const moderatorsLoading = ref(true)
const removingId = ref<number | null>(null)
const moderatorError = ref<string | null>(null)
// Telegram's photo_url can expire/rotate — if the <img> 404s we fall back to
// the letter avatar instead of showing PrimeVue's broken-image placeholder.
const brokenAvatarIds = ref(new Set<number>())

const invite = ref<Invite | null>(null)
const inviteLoading = ref(true)
const generatingInvite = ref(false)
const inviteError = ref<string | null>(null)
const copiedAt = ref<number | null>(null)

function moderatorName(moderator: Moderator): string {
  const fullName = [moderator.tg_first_name, moderator.tg_last_name].filter(Boolean).join(' ')
  return fullName || `ID ${moderator.id}`
}

function moderatorInitial(moderator: Moderator): string {
  return moderatorName(moderator)[0]?.toUpperCase() ?? '?'
}

function moderatorAvatarUrl(moderator: Moderator): string | undefined {
  if (!moderator.tg_photo_url || brokenAvatarIds.value.has(moderator.id)) return undefined
  return moderator.tg_photo_url
}

function onAvatarError(moderator: Moderator): void {
  brokenAvatarIds.value.add(moderator.id)
}

async function loadModerators(): Promise<void> {
  moderatorsLoading.value = true
  try {
    moderators.value = await getModerators()
  } finally {
    moderatorsLoading.value = false
  }
}

async function loadInvite(): Promise<void> {
  inviteLoading.value = true
  try {
    invite.value = await getActiveInvite()
  } finally {
    inviteLoading.value = false
  }
}

// Приглашение одноразовое: тот, кто откроет ссылку, сразу становится
// модератором — ни подтверждения, ни отдельного «принять приглашение»
// экрана с нашей стороны (см. App.vue/router/index.ts).
async function onGenerateInvite(): Promise<void> {
  generatingInvite.value = true
  inviteError.value = null
  try {
    invite.value = await createInvite()
  } catch {
    inviteError.value = 'Не удалось создать ссылку'
  } finally {
    generatingInvite.value = false
  }
}

// На телефоне внутри Telegram открываем системную шторку «Поделиться» —
// это быстрее, чем копировать ссылку и переключаться в другой чат самому.
// Если недоступно (десктоп/обычный браузер), откатываемся на буфер обмена.
async function onShareInvite(): Promise<void> {
  if (!invite.value) return
  const shared = shareLink(invite.value.url, 'Приглашение в команду магазина')
  if (!shared) await onCopyInvite()
}

async function onCopyInvite(): Promise<void> {
  if (!invite.value) return
  try {
    await navigator.clipboard.writeText(invite.value.url)
    copiedAt.value = Date.now()
  } catch {
    inviteError.value = 'Не удалось скопировать ссылку'
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
  void loadInvite()
})
</script>

<template>
  <div class="mx-auto flex w-full max-w-2xl flex-col gap-4 px-4">
    <div>
      <h1 class="text-xl font-semibold leading-tight text-sf-ink">Команда</h1>
      <p class="text-sm text-sf-muted">Доступ ко всему, кроме настроек магазина.</p>
    </div>

    <div class="flex flex-col gap-3 rounded-2xl bg-white p-3.5 shadow-sm">
      <p class="text-sm font-medium text-sf-ink">Пригласить</p>
      <p class="text-xs text-sf-muted">
        Отправьте ссылку человеку, которого хотите добавить — как только он её откроет, он
        станет модератором. Ссылка одноразовая: новая делает старую недействительной.
      </p>

      <AppSpinner v-if="inviteLoading" compact />

      <template v-else-if="invite">
        <div class="flex items-center gap-2 rounded-xl border border-sf-line p-2.5">
          <span class="min-w-0 flex-1 truncate text-sm text-sf-ink">{{ invite.url }}</span>
          <Button icon="pi pi-copy" text severity="secondary" @click="onCopyInvite" />
        </div>
        <Message v-if="copiedAt" severity="success" :closable="false">Ссылка скопирована</Message>
        <div class="flex items-center gap-2">
          <Button
            label="Поделиться"
            icon="pi pi-send"
            class="flex-1"
            @click="onShareInvite"
          />
          <Button
            label="Новая ссылка"
            icon="pi pi-refresh"
            severity="secondary"
            outlined
            :loading="generatingInvite"
            @click="onGenerateInvite"
          />
        </div>
      </template>

      <Button
        v-else
        label="Создать ссылку-приглашение"
        icon="pi pi-link"
        :loading="generatingInvite"
        @click="onGenerateInvite"
      />

      <Message v-if="inviteError" severity="error" :closable="false">{{ inviteError }}</Message>
    </div>

    <div class="flex flex-col gap-3 rounded-2xl bg-white p-3.5 shadow-sm">
      <p class="text-sm font-medium text-sf-ink">Модераторы</p>

      <AppSpinner v-if="moderatorsLoading" compact />

      <div v-else-if="moderators.length > 0" class="flex flex-col gap-2">
        <div
          v-for="moderator in moderators"
          :key="moderator.id"
          class="flex items-center gap-2.5 rounded-xl border border-sf-line p-2.5"
        >
          <Avatar
            :image="moderatorAvatarUrl(moderator)"
            :label="moderatorAvatarUrl(moderator) ? undefined : moderatorInitial(moderator)"
            shape="circle"
            style="background-color: var(--sf-accent); color: #fff"
            class="shrink-0"
            :pt="{ image: { class: 'object-cover object-center' } }"
            @error="onAvatarError(moderator)"
          />
          <div class="min-w-0 flex-1">
            <p class="truncate text-sm text-sf-ink">{{ moderatorName(moderator) }}</p>
            <p v-if="moderator.tg_username" class="truncate text-xs text-sf-muted">
              (@{{ moderator.tg_username }})
            </p>
          </div>
          <Button
            icon="pi pi-times"
            severity="danger"
            text
            rounded
            class="shrink-0"
            :loading="removingId === moderator.id"
            @click="onRemoveModerator(moderator)"
          />
        </div>
      </div>
      <p v-else class="text-sm text-sf-muted">Модераторов пока нет</p>

      <Message v-if="moderatorError" severity="error" :closable="false">{{ moderatorError }}</Message>
    </div>
  </div>
</template>
