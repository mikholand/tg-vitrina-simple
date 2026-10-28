<script setup lang="ts">
import type { SellerSettings } from '@entities/seller-settings/types'
import AppSpinner from '@shared/ui/AppSpinner.vue'
import { getSellerSettings, updateSellerSettings, uploadStoreLogo } from '@entities/seller-settings/api'

const settings = ref<SellerSettings | null>(null)
const loading = ref(true)
const saving = ref(false)
const uploadingLogo = ref(false)
const savedAt = ref<number | null>(null)
const error = ref<string | null>(null)

const name = ref('')
const description = ref('')

const fileInput = ref<HTMLInputElement | null>(null)

function applySettings(value: SellerSettings): void {
  settings.value = value
  name.value = value.store_name
  description.value = value.store_description
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

    <AppSpinner v-if="loading" />

    <div v-else-if="settings" class="flex flex-col gap-3">
      <div class="flex items-center gap-3 rounded-2xl bg-sf-card p-3.5 shadow-sm">
        <button
          type="button"
          class="relative flex shrink-0 appearance-none overflow-hidden rounded-full border-0 bg-transparent p-0 shadow-none outline-none disabled:opacity-60"
          :disabled="uploadingLogo"
          @click="triggerFilePicker"
        >
          <!-- `flex` above is load-bearing, not decorative: PrimeVue's Avatar
               renders as `display: inline-flex`, an inline-level box, and
               inline-level children leave a few px of "phantom" space below
               themselves inside a plain block parent (the same reason a bare
               <img> in a <div> leaves a gap underneath unless you set
               display:block/vertical-align). That gap was exactly the sliver
               showing below the circle (first as a stray shadow, then as a
               trailing bit of the hover overlay) — the button's own box was a
               few px taller than the avatar it wraps. Making the button a flex
               container turns the Avatar into a flex item, which doesn't get
               that baseline gap, so the button's box now hugs the avatar
               exactly and overflow-hidden clips the overlay flush with it.

               PrimeVue's own Avatar CSS also sets `.p-avatar img { width: 100%;
               height: 100%; }` with no object-fit, so a non-square uploaded
               logo gets stretched to fill the circle instead of being cropped —
               object-cover + object-center via pt below crops it like a normal
               avatar instead of distorting it. -->
          <Avatar
            :image="settings.store_logo ?? undefined"
            :label="settings.store_logo ? undefined : name[0]?.toUpperCase()"
            shape="circle"
            size="xlarge"
            style="background-color: var(--sf-accent); color: #fff"
            :pt="{ image: { class: 'object-cover object-center' } }"
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

      <div class="flex flex-col gap-3 rounded-2xl bg-sf-card p-3.5 shadow-sm">
        <label class="flex flex-col gap-1 text-sm">
          <span class="text-sf-muted">Название магазина</span>
          <InputText v-model="name" fluid />
        </label>

        <label class="flex flex-col gap-1 text-sm">
          <span class="text-sf-muted">Описание</span>
          <Textarea v-model="description" auto-resize rows="3" fluid />
        </label>

        <Message v-if="error" severity="error" :closable="false">{{ error }}</Message>
        <Message v-else-if="savedAt" severity="success" :closable="false">Сохранено</Message>

        <Button label="Сохранить" :loading="saving" fluid @click="onSave" />
      </div>

      <!-- Контакты и команда переехали на свои экраны — у «Менеджеров» их
           может быть несколько, а «Команда» — это уже не настройка профиля
           магазина, а список людей с доступом в кабинет. -->
      <RouterLink
        :to="{ name: 'seller-contacts' }"
        class="flex items-center gap-3 rounded-2xl bg-sf-card p-3 shadow-sm"
      >
        <span class="flex size-10 shrink-0 items-center justify-center rounded-full bg-sf-soft text-sf-accent">
          <i class="pi pi-users" />
        </span>
        <span class="min-w-0 flex-1">
          <span class="block text-sm font-medium leading-tight text-sf-ink">Менеджеры</span>
          <span class="block text-xs text-sf-muted">Кому пишут покупатели из карточки товара</span>
        </span>
        <i class="pi pi-chevron-right shrink-0 text-xs text-sf-disabled" />
      </RouterLink>

      <RouterLink
        :to="{ name: 'seller-team' }"
        class="flex items-center gap-3 rounded-2xl bg-sf-card p-3 shadow-sm"
      >
        <span class="flex size-10 shrink-0 items-center justify-center rounded-full bg-sf-soft text-sf-accent">
          <i class="pi pi-user-plus" />
        </span>
        <span class="min-w-0 flex-1">
          <span class="block text-sm font-medium leading-tight text-sf-ink">Команда</span>
          <span class="block text-xs text-sf-muted">Кто ещё ведёт этот магазин из кабинета</span>
        </span>
        <i class="pi pi-chevron-right shrink-0 text-xs text-sf-disabled" />
      </RouterLink>

      <div class="flex flex-col gap-2 rounded-2xl bg-sf-card p-3.5 shadow-sm text-sm">
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
        <div class="flex items-center justify-between gap-2">
          <span class="text-sf-muted">Уведомления о заказах</span>
          <Tag
            :severity="settings.order_notification_chat_id ? 'success' : 'warn'"
            :value="settings.order_notification_chat_id ? 'Настроены' : 'Не настроены'"
            rounded
          />
        </div>
        <p class="text-xs text-sf-muted">
          Чтобы заказы из корзины приходили в чат, администратор магазина должен отправить
          команду /setorderchat боту прямо в этом чате.
        </p>
      </div>
    </div>
  </div>
</template>
