<script setup lang="ts">
import type {
  Product,
  ProductAvailability,
  SellerProductCreate,
  SellerProductPatch,
} from '@entities/product/types'
import { createSellerProduct, updateSellerProduct, uploadProductPhoto } from '@entities/product/api'
import { useCategoryStore } from '@entities/category/store'

const props = defineProps<{
  visible: boolean
  /** `null` opens the dialog in "create a new product" mode — there's no
   *  id yet, so photo upload (which needs one) is unavailable until after
   *  the first save; the seller can add photos afterwards via Изменить. */
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

const saving = ref(false)
const uploading = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)

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

async function onFileSelected(event: Event): Promise<void> {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  target.value = ''
  if (!file || !props.product) return

  uploading.value = true
  try {
    const updated = await uploadProductPhoto(props.product.id, file)
    photoPaths.value = [...updated.photo_paths]
  } finally {
    uploading.value = false
  }
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
      const created = await createSellerProduct(payload)
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
      <div v-if="!isCreateMode" class="flex gap-2 overflow-x-auto">
        <div
          v-for="photo in photoPaths"
          :key="photo"
          class="h-16 w-16 shrink-0 overflow-hidden rounded-md border border-sf-line"
        >
          <img :src="photo" class="h-full w-full object-cover" alt="Фото товара" />
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
      <p v-else class="text-xs text-sf-muted">
        Фото можно будет добавить после создания товара, в редактировании.
      </p>

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
