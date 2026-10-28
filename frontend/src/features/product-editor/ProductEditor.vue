<script setup lang="ts">
import type { CategoryTreeNode } from '@entities/category/types'
import type {
  Product,
  ProductAvailability,
  SellerProductCreate,
  SellerProductPatch,
} from '@entities/product/types'
import {
  MAX_PHOTO_BYTES,
  MAX_PHOTOS,
  MAX_VIDEO_BYTES,
  createSellerProduct,
  updateSellerProduct,
  uploadProductPhoto,
  uploadProductVideo,
} from '@entities/product/api'
import { useCategoryStore } from '@entities/category/store'
import AppModal from '@shared/ui/AppModal.vue'
import CategoryPickNode from '@entities/category/ui/CategoryPickNode.vue'

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

// "Неизвестно" (Availability.UNKNOWN) isn't offered here — it only ever
// comes from the extractor's own LLM guess on a freshly-imported product
// it couldn't read a status from (see resolve_availability), never
// something a seller should deliberately pick by hand.
const availabilityOptions: { label: string; value: ProductAvailability }[] = [
  { label: 'В наличии', value: 'in_stock' },
  { label: 'На заказ', value: 'on_order' },
  { label: 'Нет в наличии', value: 'out_of_stock' },
]

const name = ref('')
const price = ref('')
const currency = ref('')
const description = ref('')
const sku = ref('')
const availability = ref<ProductAvailability>('in_stock')
const quantity = ref<number | null>(null)

// "На заказ" is always the buyer's choice, never a tracked count, and "нет
// в наличии" has nothing to track until it's back — so quantity is
// disabled for both. Backend mirrors this (ProductService._normalize_stock
// drops it on save either way), but the form shouldn't show/accept a
// number that's about to be discarded.
const quantityDisabled = computed(
  () => availability.value === 'on_order' || availability.value === 'out_of_stock',
)

watch(availability, () => {
  if (quantityDisabled.value) quantity.value = null
})

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

/** Already-persisted photos plus not-yet-uploaded staged ones — the number
 * the "N / 10" counter and the add-photo cap both need to agree on. */
const totalPhotoCount = computed(() => photoPaths.value.length + stagedPhotos.value.length)

interface FlatCategory {
  id: number
  name: string
  /** Full breadcrumb from root — the shared catalog repeats names across
   * branches ("Игрушки" under both dogs and cats), so a search hit without
   * its path is unidentifiable. */
  path: string
}

function flattenCategories(nodes: CategoryTreeNode[], parents: string[] = []): FlatCategory[] {
  const acc: FlatCategory[] = []
  for (const node of nodes) {
    acc.push({ id: node.id, name: node.name, path: [...parents, node.name].join(' → ') })
    acc.push(...flattenCategories(node.children, [...parents, node.name]))
  }
  return acc
}

const categoryQuery = ref('')

const flatCategories = computed(() => flattenCategories(categoryStore.tree))

/** Empty query returns nothing — with no search the tree renders instead, so
 * there's no flat several-hundred-row list to fall back to. */
const foundCategories = computed(() => {
  const query = categoryQuery.value.trim().toLowerCase()
  if (!query) return []
  return flatCategories.value.filter((category) => category.name.toLowerCase().includes(query))
})

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
  availability.value = product?.availability ?? 'in_stock'
  quantity.value = quantityDisabled.value ? null : (product?.quantity ?? null)
  categoryIds.value = product ? [...product.category_ids] : []
  publishToChannel.value = product?.publish_to_channel ?? false
  photoPaths.value = product ? [...product.photo_paths] : []
  videoPath.value = product?.video_path ?? null
  categoryQuery.value = ''
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

  if (totalPhotoCount.value >= MAX_PHOTOS) {
    window.alert(`Можно добавить не более ${MAX_PHOTOS} фото.`)
    return
  }
  if (file.size > MAX_PHOTO_BYTES) {
    window.alert('Файл слишком большой: фото принимаются до 5 МБ.')
    return
  }

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

  if (file.size > MAX_VIDEO_BYTES) {
    window.alert('Файл слишком большой: видео принимается до 50 МБ.')
    return
  }

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
  <AppModal
    :visible="visible"
    :title="isCreateMode ? 'Новый товар' : 'Редактирование товара'"
    @update:visible="(value: boolean) => emit('update:visible', value)"
  >
    <form class="flex flex-col gap-4" @submit.prevent="onSave">
      <label class="flex flex-col gap-1.5 text-sm">
        <span class="text-sf-muted">Название *</span>
        <InputText v-model="name" placeholder="Например, Кроссовки Nike" fluid />
      </label>

      <div class="flex flex-col gap-2">
        <div class="flex items-baseline justify-between">
          <span class="text-sm text-sf-muted">Фото</span>
          <span class="text-xs text-sf-placeholder">{{ totalPhotoCount }} / {{ MAX_PHOTOS }}</span>
        </div>
        <div class="grid grid-cols-4 gap-2">
          <div
            v-for="(photo, index) in photoPaths"
            :key="photo"
            class="relative aspect-square overflow-hidden rounded-xl border border-sf-line bg-sf-soft"
          >
            <img :src="photo" class="size-full object-cover" :alt="`Фото ${index + 1}`" />
            <span
              v-if="index === 0"
              class="absolute inset-x-0 bottom-0 bg-black/50 py-0.5 text-center text-[0.6rem] text-white"
            >
              Обложка
            </span>
          </div>
          <!-- Create mode only: picked, not-yet-uploaded photos — removable
               before the first save, unlike the already-persisted ones above. -->
          <div
            v-for="(staged, index) in stagedPhotos"
            :key="staged.previewUrl"
            class="relative aspect-square overflow-hidden rounded-xl border border-sf-line bg-sf-soft"
          >
            <img :src="staged.previewUrl" class="size-full object-cover" alt="Фото товара" />
            <span
              v-if="photoPaths.length === 0 && index === 0"
              class="absolute inset-x-0 bottom-0 bg-black/50 py-0.5 text-center text-[0.6rem] text-white"
            >
              Обложка
            </span>
            <button
              type="button"
              class="absolute right-1 top-1 flex size-5 items-center justify-center rounded-full bg-black/60 text-white"
              aria-label="Убрать фото"
              @click="removeStagedPhoto(index)"
            >
              <i class="pi pi-times text-[0.6rem]" />
            </button>
          </div>
          <button
            v-if="totalPhotoCount < MAX_PHOTOS"
            type="button"
            class="flex aspect-square items-center justify-center rounded-xl border border-dashed border-sf-line text-sf-muted disabled:opacity-50"
            :disabled="uploading"
            aria-label="Добавить фото"
            @click="triggerFilePicker"
          >
            <i v-if="!uploading" class="pi pi-plus" />
            <i v-else class="pi pi-spin pi-spinner" />
          </button>
        </div>
        <span class="text-xs text-sf-placeholder">Первое фото — обложка. JPG/PNG/WebP, до 5 МБ.</span>
        <input ref="fileInput" type="file" accept="image/*" class="hidden" @change="onFileSelected" />
      </div>

      <div class="flex flex-col gap-2">
        <span class="text-sm text-sf-muted">Видео</span>

        <div
          v-if="videoPath || stagedVideo"
          class="flex items-center justify-between gap-2 rounded-xl border border-sf-line p-3"
        >
          <span class="flex items-center gap-2 text-sm text-sf-ink">
            <i class="pi pi-video text-sf-muted" />
            Видео добавлено
          </span>
          <!-- Only the not-yet-uploaded staged video can be removed here —
               same asymmetry as photos: nothing already persisted has a
               delete control yet. -->
          <button
            v-if="stagedVideo"
            type="button"
            class="flex items-center gap-1 text-xs text-sf-danger"
            @click="removeStagedVideo"
          >
            <i class="pi pi-trash" /> Убрать
          </button>
        </div>
        <button
          v-else
          type="button"
          class="flex items-center justify-center gap-2 rounded-xl border border-dashed border-sf-line py-3 text-sm text-sf-muted disabled:opacity-50"
          :disabled="uploadingVideo"
          @click="triggerVideoPicker"
        >
          <i :class="uploadingVideo ? 'pi pi-spin pi-spinner' : 'pi pi-video'" />
          {{ uploadingVideo ? 'Загрузка…' : 'Добавить видео' }}
        </button>
        <span class="text-xs text-sf-placeholder">Одно видео, MP4/MOV/WebM, до 50 МБ.</span>
        <input ref="videoInput" type="file" accept="video/*" class="hidden" @change="onVideoSelected" />
      </div>

      <div class="flex gap-3">
        <label class="flex flex-1 flex-col gap-1.5 text-sm">
          <span class="text-sf-muted">Цена</span>
          <InputText v-model="price" placeholder="990.00" fluid />
        </label>
        <label class="flex w-24 flex-col gap-1.5 text-sm">
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
        <!-- flex-[3] vs flex-[2] (не 1/1): "Нет в наличии" — самый длинный
             вариант — впритык умещался бы в равной половине, а степпер
             количества своей половине не нужен — цифра плюс две узкие
             кнопки, там всегда остаётся пустое место. -->
        <label class="flex flex-[3] flex-col gap-1.5 text-sm">
          <span class="text-sf-muted">Наличие</span>
          <Select
            v-model="availability"
            :options="availabilityOptions"
            option-label="label"
            option-value="value"
            fluid
          />
        </label>
        <!-- "На заказ"/"нет в наличии" — ни то ни другое не трактуется как
             остаток (на заказ — выбор покупателя, нет в наличии — нечего
             считать, пока не привезли), поэтому поле для них просто
             отключено (сервер тоже обнуляет quantity при этих статусах —
             см. ProductService._normalize_stock). Поле остаётся в
             разметке во всех статусах (не v-if), а не только скрывает
             значение — иначе "Наличие" растягивается на всю строку и
             макет визуально "прыгает" между статусами. -->
        <label class="flex flex-[2] flex-col gap-1.5 text-sm">
          <span class="text-sf-muted">Количество</span>
          <InputNumber
            v-model="quantity"
            :min="0"
            show-buttons
            button-layout="horizontal"
            fluid
            :disabled="quantityDisabled"
          />
        </label>
      </div>

      <div v-if="categoryStore.tree.length" class="flex flex-col gap-2">
        <div class="flex items-baseline justify-between">
          <span class="text-sm text-sf-muted">Категории</span>
          <span v-if="categoryIds.length" class="text-xs text-sf-placeholder">
            выбрано: {{ categoryIds.length }}
          </span>
        </div>
        <!-- The shared catalog can be large; without search the seller would
             scroll past hundreds of rows for one category. -->
        <input
          v-model="categoryQuery"
          type="search"
          placeholder="Поиск категории"
          class="w-full rounded-xl border border-sf-line bg-sf-card px-3 py-2 text-sm text-sf-ink outline-none placeholder:text-sf-placeholder focus:border-sf-accent"
        />
        <div class="max-h-56 overflow-y-auto rounded-xl border border-sf-line bg-sf-card p-2">
          <template v-if="categoryQuery.trim()">
            <label
              v-for="category in foundCategories"
              :key="category.id"
              class="flex items-center gap-2 py-1 text-sm text-sf-ink"
            >
              <input v-model="categoryIds" type="checkbox" :value="category.id" class="size-4" />
              <span>{{ category.path }}</span>
            </label>
            <p v-if="!foundCategories.length" class="py-1 text-sm text-sf-placeholder">Ничего не найдено</p>
          </template>

          <ul v-else>
            <CategoryPickNode
              v-for="node in categoryStore.tree"
              :key="node.id"
              v-model="categoryIds"
              :category="node"
            />
          </ul>
        </div>
      </div>

      <label class="flex items-center justify-between text-sm">
        <span class="text-sf-muted">Публикация в канал</span>
        <ToggleSwitch v-model="publishToChannel" />
      </label>

      <button
        type="submit"
        :disabled="saving || !name.trim()"
        class="mt-2 rounded-xl bg-sf-accent py-3 font-semibold text-sf-bg disabled:opacity-50"
      >
        {{ saving ? 'Сохранение…' : 'Сохранить' }}
      </button>
    </form>
  </AppModal>
</template>
