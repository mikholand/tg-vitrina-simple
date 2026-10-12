<script setup lang="ts">
import type { RawPost, RawPostStatus } from '@entities/raw-post/types'
import { getRawPosts } from '@entities/raw-post/api'
import { rawPostStatusChipClasses, rawPostStatusLabels } from '@entities/raw-post/labels'

const PAGE_SIZE = 20

type StatusFilter = RawPostStatus | 'all'

const tabs: { label: string; value: StatusFilter }[] = [
  { label: 'Все', value: 'all' },
  { label: 'Новые', value: 'new' },
  { label: 'Распознано', value: 'extracted' },
  { label: 'Ошибка', value: 'failed' },
]

const activeTab = ref<StatusFilter>('all')
const posts = ref<RawPost[]>([])
const total = ref(0)
const offset = ref(0)
const loading = ref(true)
const loadingMore = ref(false)

const hasMore = computed(() => posts.value.length < total.value)

function formatDate(value: string): string {
  return new Date(value).toLocaleString()
}

async function loadPosts(reset: boolean): Promise<void> {
  if (reset) {
    loading.value = true
    offset.value = 0
  } else {
    loadingMore.value = true
  }

  try {
    const result = await getRawPosts({
      status: activeTab.value === 'all' ? undefined : activeTab.value,
      limit: PAGE_SIZE,
      offset: reset ? 0 : offset.value,
    })

    posts.value = reset ? result.items : [...posts.value, ...result.items]
    total.value = result.total
    offset.value = (reset ? 0 : offset.value) + result.items.length
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

watch(activeTab, () => {
  void loadPosts(true)
})

onMounted(() => {
  void loadPosts(true)
})
</script>

<template>
  <div class="flex flex-col gap-4 px-4">
    <h1 class="text-xl font-semibold leading-tight text-sf-ink">Посты</h1>

    <div class="no-scrollbar -mx-4 flex gap-2 overflow-x-auto px-4">
      <button
        v-for="tab in tabs"
        :key="tab.value"
        type="button"
        class="shrink-0 rounded-full border px-3.5 py-1.5 text-sm"
        :class="
          activeTab === tab.value ? 'border-sf-accent bg-sf-accent text-white' : 'border-sf-line bg-sf-card text-sf-ink'
        "
        @click="activeTab = tab.value"
      >
        {{ tab.label }}
      </button>
    </div>

    <p v-if="loading" class="py-16 text-center text-sf-muted">Загрузка…</p>

    <template v-else>
      <div v-if="posts.length === 0" class="flex flex-col items-center gap-2 py-16 text-center text-sf-muted">
        <i class="pi pi-inbox text-4xl" />
        <span>В этом разделе пока нет постов</span>
      </div>

      <div v-else class="flex flex-col gap-2">
        <div v-for="post in posts" :key="post.id" class="flex flex-col gap-2 rounded-2xl border border-sf-line bg-sf-card p-3">
          <div class="flex items-center justify-between gap-2">
            <span class="shrink-0 rounded-full px-2 py-0.5 text-[0.65rem]" :class="rawPostStatusChipClasses[post.status]">
              {{ rawPostStatusLabels[post.status] }}
            </span>
            <span class="text-xs text-sf-muted">{{ formatDate(post.posted_at) }}</span>
          </div>

          <p v-if="post.raw_text" class="line-clamp-3 text-sm text-sf-ink">{{ post.raw_text }}</p>
          <p v-else class="text-sm italic text-sf-muted">Без текста</p>

          <div v-if="post.photo_paths.length > 0" class="no-scrollbar flex gap-2 overflow-x-auto">
            <img
              v-for="photo in post.photo_paths"
              :key="photo"
              :src="photo"
              class="size-14 shrink-0 rounded-xl object-cover"
              alt=""
            />
          </div>

          <RouterLink
            v-if="post.product_id"
            :to="`/product/${post.product_id}`"
            class="flex items-center gap-1 text-xs text-sf-accent"
          >
            Посмотреть товар
            <i class="pi pi-arrow-right" />
          </RouterLink>
        </div>
      </div>

      <div v-if="hasMore" class="flex justify-center py-2 pb-4">
        <button
          type="button"
          class="rounded-full border border-sf-line bg-sf-card px-5 py-2.5 text-sm font-medium text-sf-ink disabled:opacity-60"
          :disabled="loadingMore"
          @click="loadPosts(false)"
        >
          {{ loadingMore ? 'Загрузка…' : 'Показать ещё' }}
        </button>
      </div>
    </template>
  </div>
</template>
