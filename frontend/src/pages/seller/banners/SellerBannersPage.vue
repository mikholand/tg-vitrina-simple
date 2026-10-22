<script setup lang="ts">
import type { Banner } from '@entities/banner/types'
import AppSpinner from '@shared/ui/AppSpinner.vue'
import { createBanner, deleteBanner, getSellerBanners, updateBanner } from '@entities/banner/api'

const MAX_BANNERS = 3

const banners = ref<Banner[]>([])
const loading = ref(true)
const uploading = ref(false)
const savingId = ref<number | null>(null)
const deletingId = ref<number | null>(null)
const error = ref<string | null>(null)

const linkDrafts = ref<Record<number, string>>({})

const fileInput = ref<HTMLInputElement | null>(null)

const canAddMore = computed(() => banners.value.length < MAX_BANNERS)

function syncDrafts(): void {
  linkDrafts.value = Object.fromEntries(banners.value.map((b) => [b.id, b.link_url ?? '']))
}

async function loadBanners(): Promise<void> {
  loading.value = true
  try {
    banners.value = await getSellerBanners()
    syncDrafts()
  } finally {
    loading.value = false
  }
}

function triggerFilePicker(): void {
  if (!canAddMore.value) return
  fileInput.value?.click()
}

async function onFileSelected(event: Event): Promise<void> {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  target.value = ''
  if (!file) return

  uploading.value = true
  error.value = null
  try {
    const banner = await createBanner(file)
    banners.value = [...banners.value, banner]
    syncDrafts()
  } catch {
    error.value = 'Не удалось загрузить баннер'
  } finally {
    uploading.value = false
  }
}

async function onSaveLink(banner: Banner): Promise<void> {
  savingId.value = banner.id
  error.value = null
  try {
    const value = linkDrafts.value[banner.id]?.trim() ?? ''
    const updated = await updateBanner(banner.id, { link_url: value || null })
    const index = banners.value.findIndex((b) => b.id === updated.id)
    if (index !== -1) banners.value[index] = updated
  } catch {
    error.value = 'Не удалось сохранить ссылку'
  } finally {
    savingId.value = null
  }
}

async function onDelete(banner: Banner): Promise<void> {
  deletingId.value = banner.id
  error.value = null
  try {
    await deleteBanner(banner.id)
    banners.value = banners.value.filter((b) => b.id !== banner.id)
    syncDrafts()
  } catch {
    error.value = 'Не удалось удалить баннер'
  } finally {
    deletingId.value = null
  }
}

onMounted(() => {
  void loadBanners()
})
</script>

<template>
  <div class="mx-auto flex w-full max-w-2xl flex-col gap-4 px-4">
    <div>
      <h1 class="text-xl font-semibold leading-tight text-sf-ink">Баннеры</h1>
      <p class="text-sm text-sf-muted">Карусель на главной — до {{ MAX_BANNERS }} баннеров</p>
    </div>

    <AppSpinner v-if="loading" />

    <template v-else>
      <Message v-if="error" severity="error" :closable="false">{{ error }}</Message>

      <div v-if="banners.length === 0" class="flex flex-col items-center gap-2 py-10 text-center text-sf-muted">
        <i class="pi pi-images text-4xl" />
        <span>Баннеров пока нет</span>
      </div>

      <div v-else class="flex flex-col gap-3">
        <div
          v-for="banner in banners"
          :key="banner.id"
          class="flex flex-col gap-2 rounded-2xl border border-sf-line bg-sf-card p-3"
        >
          <img :src="banner.image_path" alt="" class="aspect-[16/7] w-full rounded-xl object-cover" />
          <div class="flex items-center gap-2">
            <IconField class="flex-1">
              <InputIcon class="pi pi-link" />
              <InputText v-model="linkDrafts[banner.id]" placeholder="https://…" fluid />
            </IconField>
            <Button
              icon="pi pi-check"
              :loading="savingId === banner.id"
              severity="secondary"
              @click="onSaveLink(banner)"
            />
            <Button
              icon="pi pi-trash"
              severity="danger"
              :loading="deletingId === banner.id"
              @click="onDelete(banner)"
            />
          </div>
        </div>
      </div>

      <input ref="fileInput" type="file" accept="image/*" class="hidden" @change="onFileSelected" />
      <Button
        label="Добавить баннер"
        icon="pi pi-plus"
        :disabled="!canAddMore"
        :loading="uploading"
        fluid
        @click="triggerFilePicker"
      />
      <p v-if="!canAddMore" class="text-center text-xs text-sf-muted">
        Достигнут лимит в {{ MAX_BANNERS }} баннера — удалите один, чтобы добавить новый
      </p>
    </template>
  </div>
</template>
