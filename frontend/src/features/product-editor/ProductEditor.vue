<script setup lang="ts">
import type {
  Product,
  ProductAvailability,
  SellerProductCreate,
  SellerProductPatch,
} from '@entities/product/types'
import {
  createSellerProduct,
  updateSellerProduct,
  uploadProductPhoto,
  uploadProductVideo,
} from '@entities/product/api'
import { useCategoryStore } from '@entities/category/store'

const props = defineProps<{
  visible: boolean
  /** `null` opens the dialog in "create a new product" mode. */
  product: Product | null
}>()

const isCreateMode = computed(() => props.product === null)

const emit = defineEmits<{
  'update:visible': [value: boolean]
  saved: [product: Product]
}>()

const categoryStore = useCategoryStore()

const availabilityOptions: { label: string; value: ProductAvailability }[] = [
  { label: 'В наличии', value: 'in_stock' },
  { label: 'На заказ', value: 'on_order' },
  { label: 'Нет в наличии', value: 'out_of_stock' },
  { label: 'Неизвестно', value: 'unknown' },
]

const name = ref('')
const price = ref('')
const currency = ref('')
const description = ref('')
const sku = ref('')
const availability = ref<ProductAvailability>('unknown')
const quantity = ref<number | null>(null)
const categoryIds = ref<number[]>([])
const publishToChannel = ref(false)
const photoPaths = ref<string[]>([])
const videoPath = ref<string | null>(null)

// Create mode has no product id yet, so anything picked before the first
// save can't be uploaded to anything (both upload endpoints are
// POST /products/{id}/...). Staged files are held here — as a File plus a
// local blob preview for photos — and only actually uploaded, one by one,
// right after `createSellerProduct` returns the new id. Edit mode skips all
// of this and uploads on selection, same as before this existed.
interface StagedPhoto {
  file: File
  previewUrl: string
}
const stagedPhotos = ref<StagedPhoto[]>([])
const stagedVideo = ref<File | null>(null)

const saving = ref(false)
const uploading = ref(false)
const uploadingVideo = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)
const videoInput = ref<HTMLInputElement | null>(null)

function clearStaged(): void {
  for (const staged of stagedPhotos.value) URL.revokeObjectURL(staged.previewUrl)
  stagedPhotos.value = []
  stagedVideo.value = null
}

function resetForm(product: Product | null): void {
  name.value = product?.name ?? ''
  price.value = product?.price ?? ''
  currency.value = product?.currency ?? 'RUB'
  description.value = product?.description ?? ''
  sku.value = product?.sku ?? ''
  availability.value = product?.availability ?? 'unknown'
  quantity.value = product?.quantity ?? null
  categoryIds.value = product ? [...product.category_ids] : []
  publishToChannel.value = product?.publish_to_channel ?? false
  photoPaths.value = product ? [...product.photo_paths] : []
  videoPath.value = product?.video_path ?? null
  clearStaged()
}

watch(
  () => props.product,
  (product) => resetForm(product),
  { immediate: true },
)

// `product` stays `null` across two consecutive "create" openings (no
// reference change to trigger the watcher above), so also reset whenever
// the dialog transitions to visible.
watch(
  () => props.visible,
  (visible) => {
    if (visible) resetForm(props.product)
  },
)

function close(): void {
  emit('update:visible', false)
}

function triggerFilePicker(): void {
  fileInput.value?.click()
}

function triggerVideoPicker(): void {
  videoInput.value?.click()
}

async function onFileSelected(event: Event): Promise<void> {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  target.value = ''
  if (!file) return

  if (isCreateMode.value) {
    stagedPhotos.value.push({ file, previewUrl: URL.createObjectURL(file) })
    return
  }

  if (!props.product) return
  uploading.value = true
  try {
    const updated = await uploadProductPhoto(props.product.id, file)
    photoPaths.value = [...updated.photo_paths]
  } finally {
    uploading.value = false
  }
}

function removeStagedPhoto(index: number): void {
  const [removed] = stagedPhotos.value.splice(index, 1)
  if (removed) URL.revokeObjectURL(removed.previewUrl)
}

async function onVideoSelected(event: Event): Promise<void> {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  target.value = ''
  if (!file) return

  if (isCreateMode.value) {
    stagedVideo.value = file
    return
  }

  if (!props.product) return
  uploadingVideo.value = true
  try {
    const updated = await uploadProductVideo(props.product.id, file)
    videoPath.value = updated.video_path
  } finally {
    uploadingVideo.value = false
  }
}

function removeStagedVideo(): void {
  stagedVideo.value = null
}

async function onSave(): Promise<void> {
  if (!name.value.trim()) return

  saving.value = true
  try {
    if (isCreateMode.value) {
      const payload: SellerProductCreate = {
        name: name.value,
        price: price.value === '' ? null : price.value,
        currency: currency.value || 'RUB',
        description: description.value === '' ? null : description.value,
        sku: sku.value === '' ? null : sku.value,
        availability: availability.value,
        quantity: quantity.value,
        category_ids: categoryIds.value,
      }
      let created = await createSellerProduct(payload)
      // Photos/video couldn't be attached until the product had an id —
      // upload every staged file now, in sequence, to the id we just got.
      for (const staged of stagedPhotos.value) {
        created = await uploadProductPhoto(created.id, staged.file)
      }
      if (stagedVideo.value) {
        created = await uploadProductVideo(created.id, stagedVideo.value)
      }
      clearStaged()
      emit('saved', created)
      close()
      return
    }

    if (!props.product) return
    const patch: SellerProductPatch = {
      name: name.value,
      price: price.value === '' ? null : price.value,
      currency: currency.value,
      description: description.value === '' ? null : description.value,
      sku: sku.value === '' ? null : sku.value,
      availability: availability.value,
      quantity: quantity.value,
      category_ids: categoryIds.value,
      publish_to_channel: publishToChannel.value,
    }
    const updated = await updateSellerProduct(props.product.id, patch)
    emit('saved', updated)
    close()
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  void categoryStore.fetchCategories()
})
</script>

<template>
  <Dialog
    :visible="visible"
    modal
    :header="isCreateMode ? 'Новый товар' : 'Редактирование товара'"
    class="w-[90vw] max-w-md"
    @update:visible="(value: boolean) => emit('update:visible', value)"
  >
    <div class="flex flex-col gap-4">
      <div class="flex flex-col gap-2">
        <div class="flex gap-2 overflow-x-auto">
          <div
            v-for="photo in photoPaths"
            :key="photo"
            class="h-16 w-16 shrink-0 overflow-hidden rounded-md border border-sf-line"
          >
            <img :src="photo" class="h-full w-full object-cover" alt="Фото товара" />
          </div>
          <!-- Create mode only: picked, not-yet-uploaded photos — removable
               before the first save, unlike the already-persisted ones above. -->
          <div
            v-for="(staged, index) in stagedPhotos"
            :key="staged.previewUrl"
            class="relative h-16 w-16 shrink-0 overflow-hidden rounded-md border border-sf-line"
          >
            <img :src="staged.previewUrl" class="h-full w-full object-cover" alt="Фото товара" />
            <button
              type="button"
              class="absolute right-0.5 top-0.5 flex size-4 items-center justify-center rounded-full bg-black/60 text-white"
              aria-label="Убрать фото"
              @click="removeStagedPhoto(index)"
            >
              <i class="pi pi-times text-[10px]" />
            </button>
          </div>
          <button
            type="button"
            class="flex h-16 w-16 shrink-0 items-center justify-center rounded-md border border-dashed border-sf-line text-sf-muted"
            :disabled="uploading"
            @click="triggerFilePicker"
          >
            <i v-if="!uploading" class="pi pi-plus" />
            <i v-else class="pi pi-spin pi-spinner" />
          </button>
          <input
            ref="fileInput"
            type="file"
            accept="image/*"
            class="hidden"
            @change="onFileSelected"
          />
        </div>

        <div class="flex gap-2">
          <div
            v-if="videoPath || stagedVideo"
            class="relative flex h-16 w-28 shrink-0 flex-col items-center justify-center gap-1 rounded-md border border-sf-line bg-sf-soft text-xs text-sf-muted"
          >
            <i class="pi pi-video text-lg" />
            <span>Видео</span>
            <!-- Only the not-yet-uploaded staged video can be removed here —
                 same asymmetry as photos: nothing already persisted has a
                 delete control yet. -->
            <button
              v-if="stagedVideo"
              type="button"
              class="absolute right-0.5 top-0.5 flex size-4 items-center justify-center rounded-full bg-black/60 text-white"
              aria-label="Убрать видео"
              @click="removeStagedVideo"
            >
              <i class="pi pi-times text-[10px]" />
            </button>
          </div>
          <button
            v-else
            type="button"
            class="flex h-16 w-28 shrink-0 items-center justify-center gap-1.5 rounded-md border border-dashed border-sf-line text-xs text-sf-muted"
            :disabled="uploadingVideo"
            @click="triggerVideoPicker"
          >
            <i v-if="!uploadingVideo" class="pi pi-video" />
            <i v-else class="pi pi-spin pi-spinner" />
            <span>Видео</span>
          </button>
          <input
            ref="videoInput"
            type="file"
            accept="video/*"
            class="hidden"
            @change="onVideoSelected"
          />
        </div>
      </div>

      <label class="flex flex-col gap-1.5 text-sm">
        <span class="text-sf-muted">Название</span>
        <InputText v-model="name" fluid />
      </label>

      <div class="flex gap-3">
        <label class="flex flex-1 flex-col gap-1.5 text-sm">
          <span class="text-sf-muted">Цена</span>
          <InputText v-model="price" fluid />
        </label>
        <label class="flex flex-1 flex-col gap-1.5 text-sm">
          <span class="text-sf-muted">Валюта</span>
          <InputText v-model="currency" fluid />
        </label>
      </div>

      <label class="flex flex-col gap-1.5 text-sm">
        <span class="text-sf-muted">Описание</span>
        <Textarea v-model="description" auto-resize rows="3" fluid />
      </label>

      <label class="flex flex-col gap-1.5 text-sm">
        <span class="text-sf-muted">Артикул</span>
        <InputText v-model="sku" fluid />
      </label>

      <div class="flex gap-3">
        <label class="flex flex-1 flex-col gap-1.5 text-sm">
          <span class="text-sf-muted">Наличие</span>
          <Select
            v-model="availability"
            :options="availabilityOptions"
            option-label="label"
            option-value="value"
            fluid
          />
        </label>
        <label class="flex flex-1 flex-col gap-1.5 text-sm">
          <span class="text-sf-muted">Количество</span>
          <InputNumber v-model="quantity" :min="0" show-buttons button-layout="horizontal" fluid />
        </label>
      </div>

      <label class="flex flex-col gap-1.5 text-sm">
        <span class="text-sf-muted">Категории</span>
        <MultiSelect
          v-model="categoryIds"
          :options="categoryStore.categories"
          option-label="name"
          option-value="id"
          placeholder="Выберите категории"
          display="chip"
          fluid
        />
      </label>

      <label class="flex items-center justify-between text-sm">
        <span class="text-sf-muted">Публикация в канал</span>
        <ToggleSwitch v-model="publishToChannel" />
      </label>
    </div>

    <template #footer>
      <Button label="Отмена" text @click="close" />
      <Button label="Сохранить" :loading="saving" :disabled="!name.trim()" @click="onSave" />
    </template>
  </Dialog>
</template>
