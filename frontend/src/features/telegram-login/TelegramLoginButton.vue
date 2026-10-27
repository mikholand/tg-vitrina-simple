<script setup lang="ts">
import { useAuthStore } from '@entities/user/store'
import { useStoreInfoStore } from '@entities/store-info/store'
import { mountTelegramLoginWidget, type TelegramWidgetAuthResult } from '@shared/telegram/widget'
import AppModal from '@shared/ui/AppModal.vue'

const authStore = useAuthStore()
const storeInfoStore = useStoreInfoStore()

const visible = ref(false)
const container = ref<HTMLElement | null>(null)
const error = ref<string | null>(null)

async function handleAuth(result: TelegramWidgetAuthResult): Promise<void> {
  error.value = null
  if (!result.id_token) {
    error.value = 'Не удалось войти через Telegram. Попробуйте ещё раз.'
    return
  }
  try {
    await authStore.loginWithTelegramWidget(result.id_token)
    visible.value = false
  } catch {
    error.value = 'Не удалось войти через Telegram. Попробуйте ещё раз.'
  }
}

// The widget is Telegram's own `<script>` embed (see `widget.ts`) — it has
// to be (re-)mounted into the container every time the modal opens, since
// `AppModal`'s `v-if` tears the container down on close. `flush: 'post'`
// is load-bearing here: the default `'pre'` timing runs this callback
// *before* Vue has patched the DOM for the `visible` change that triggered
// it, so `container.value` would still be null (AppModal's own `v-if`
// hasn't rendered the `<div ref="container">` yet) — the widget silently
// never mounted, leaving just the modal's static text.
watch(
  () => [visible.value, storeInfoStore.storeInfo?.bot_client_id] as const,
  ([isVisible, botClientId]) => {
    if (isVisible && botClientId && container.value) {
      mountTelegramLoginWidget(container.value, botClientId, handleAuth)
    }
  },
  { flush: 'post' },
)
</script>

<template>
  <button
    type="button"
    class="flex shrink-0 items-center gap-1.5 text-sm font-medium text-sf-accent"
    @click="visible = true"
  >
    <i class="pi pi-user text-base" />
    Войти
  </button>

  <AppModal v-model:visible="visible" title="Вход через Telegram">
    <div class="flex flex-col items-center gap-4 py-2">
      <p class="text-center text-sm text-sf-muted">Войдите через свой аккаунт Telegram.</p>
      <div ref="container" class="min-h-11" />
      <p v-if="error" class="text-center text-sm text-sf-danger">{{ error }}</p>
    </div>
  </AppModal>
</template>
