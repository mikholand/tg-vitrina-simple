<script setup lang="ts">
import { useSyncStore } from '@entities/sync/store'
import AppSpinner from '@shared/ui/AppSpinner.vue'
import { syncStatusChipClasses, syncStatusLabels } from '@entities/sync/labels'

// tg-vitrina's SyncPage also has a channel-connect form and a "post
// storefront button to the channel" action — both apply to a mutable,
// per-seller channel binding. This project's channel is a single
// TELEGRAM_CHANNEL_ID env var (see SellerSettingsPage), so only the actual
// sync run — status, progress, start/resume/stop — carries over.
const syncStore = useSyncStore()

const loading = ref(true)
const actionLoading = ref(false)

let pollHandle: ReturnType<typeof setInterval> | undefined

const statusLabel = computed(() => syncStatusLabels[syncStore.state?.status ?? 'idle'])
const statusChipClasses = computed(() => syncStatusChipClasses[syncStore.state?.status ?? 'idle'])

const isActive = computed(
  () => syncStore.state?.status === 'running' || syncStore.state?.status === 'requested',
)
const canResume = computed(() => syncStore.state?.status === 'interrupted')

const progressTotal = computed(() => syncStore.state?.total_count ?? 0)
const progressDone = computed(() => syncStore.state?.done_count ?? 0)
const progressPercent = computed(() =>
  progressTotal.value > 0 ? Math.min(100, Math.round((progressDone.value / progressTotal.value) * 100)) : 0,
)

async function refreshStatus(): Promise<void> {
  await syncStore.fetchStatus()
}

async function onStart(resume: boolean): Promise<void> {
  actionLoading.value = true
  try {
    await syncStore.startSync(resume)
  } finally {
    actionLoading.value = false
  }
}

async function onStop(): Promise<void> {
  actionLoading.value = true
  try {
    await syncStore.stopSync()
  } finally {
    actionLoading.value = false
  }
}

onMounted(async () => {
  try {
    await refreshStatus()
  } finally {
    loading.value = false
  }

  pollHandle = setInterval(() => {
    if (isActive.value) void refreshStatus()
  }, 4000)
})

onUnmounted(() => {
  if (pollHandle) clearInterval(pollHandle)
})
</script>

<template>
  <div class="mx-auto flex w-full max-w-2xl flex-col gap-4 px-4">
    <h1 class="text-xl font-semibold leading-tight text-sf-ink">Синхронизация</h1>

    <AppSpinner v-if="loading" />

    <template v-else>
      <div class="flex flex-col gap-3 rounded-2xl border border-sf-line bg-sf-card p-3.5">
        <div class="flex items-center justify-between">
          <span class="text-sm text-sf-muted">Статус</span>
          <span class="shrink-0 rounded-full px-2 py-0.5 text-[0.65rem]" :class="statusChipClasses">
            {{ statusLabel }}
          </span>
        </div>

        <div v-if="isActive && progressTotal > 0">
          <div class="h-2 w-full overflow-hidden rounded-full bg-sf-line">
            <div class="h-full rounded-full bg-sf-accent transition-all" :style="{ width: `${progressPercent}%` }" />
          </div>
          <p class="mt-1 text-right text-xs text-sf-muted">{{ progressDone }} / {{ progressTotal }}</p>
        </div>
        <div v-else-if="syncStore.state" class="text-xs text-sf-muted">Загружено: {{ progressDone }}</div>

        <p v-if="syncStore.state?.last_error" class="text-xs text-sf-danger">{{ syncStore.state.last_error }}</p>

        <div class="flex gap-2">
          <button
            v-if="!isActive && !canResume"
            type="button"
            class="flex items-center gap-1.5 rounded-full bg-sf-accent px-4 py-2 text-sm font-medium text-sf-bg disabled:opacity-60"
            :disabled="actionLoading"
            @click="onStart(false)"
          >
            <i class="pi pi-play text-xs" /> Запустить синхронизацию
          </button>
          <button
            v-if="canResume"
            type="button"
            class="flex items-center gap-1.5 rounded-full bg-sf-accent px-4 py-2 text-sm font-medium text-sf-bg disabled:opacity-60"
            :disabled="actionLoading"
            @click="onStart(true)"
          >
            <i class="pi pi-play text-xs" /> Продолжить
          </button>
          <button
            v-if="isActive"
            type="button"
            class="flex items-center gap-1.5 rounded-full border border-sf-danger px-4 py-2 text-sm font-medium text-sf-danger disabled:opacity-60"
            :disabled="actionLoading"
            @click="onStop"
          >
            <i class="pi pi-stop text-xs" /> Остановить
          </button>
        </div>
      </div>
    </template>
  </div>
</template>
