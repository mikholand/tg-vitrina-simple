<script setup lang="ts">
import { useAuthStore } from '@entities/user/store'
import { useStoreInfoStore } from '@entities/store-info/store'
import { mountTelegramLoginWidget, type TelegramWidgetAuthResult } from '@shared/telegram/widget'

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
// the modal's own `v-if` below tears the container down on close.
// `flush: 'post'` is load-bearing here: the default `'pre'` timing runs
// this callback *before* Vue has patched the DOM for the `visible` change
// that triggered it, so `container.value` would still be null (the
// `v-if="visible"` below hasn't rendered the `<div ref="container">` yet)
// — the widget silently never mounted, leaving just the modal's static
// text.
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

  <!-- A centered dialog, not AppModal's bottom sheet — this is a short,
       single-purpose prompt (one button), not a list/form someone scrolls,
       so anchoring it to the bottom edge like AppModal's other users
       (contact picker, confirmation sheets) buys nothing here. -->
  <Teleport to="body">
    <Transition name="tg-login-modal-fade">
      <div
        v-if="visible"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
        @click.self="visible = false"
      >
        <div class="w-full max-w-sm rounded-2xl bg-white p-5">
          <header class="mb-4 flex items-center justify-between">
            <h2 class="text-base font-semibold text-sf-ink">Вход через Telegram</h2>
            <button type="button" class="text-sf-muted" aria-label="Закрыть" @click="visible = false">
              <i class="pi pi-times text-lg" />
            </button>
          </header>
          <div class="flex flex-col items-center gap-4 pb-1">
            <p class="text-center text-sm text-sf-muted">Войдите через свой аккаунт Telegram.</p>
            <div ref="container" class="min-h-11" />
            <p v-if="error" class="text-center text-sm text-sf-danger">{{ error }}</p>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.tg-login-modal-fade-enter-active,
.tg-login-modal-fade-leave-active {
  transition: opacity 0.2s ease;
}
.tg-login-modal-fade-enter-from,
.tg-login-modal-fade-leave-to {
  opacity: 0;
}
</style>
