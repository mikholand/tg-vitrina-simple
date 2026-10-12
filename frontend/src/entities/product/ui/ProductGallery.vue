<script setup lang="ts">
const props = defineProps<{
  /** Photo URLs (first is the cover). */
  photos: string[]
  /** Alt-text base (product name). */
  alt: string
}>()

const track = ref<HTMLElement | null>(null)
const activeIndex = ref(0)

function onScroll(): void {
  const element = track.value
  if (!element) return
  activeIndex.value = Math.round(element.scrollLeft / element.clientWidth)
}

// Reset to the cover whenever the product (its photo set) changes.
watch(
  () => props.photos,
  () => {
    activeIndex.value = 0
    track.value?.scrollTo({ left: 0 })
  },
)

const initial = computed(() => props.alt[0]?.toUpperCase() ?? '')
</script>

<template>
  <div class="relative aspect-[4/5] overflow-hidden rounded-b-[2rem] bg-sf-soft">
    <!-- Листается пальцем: scroll-snap отдаёт жест системе, инерция и
         скорость — те же, что в остальных приложениях телефона. -->
    <div
      v-if="photos.length"
      ref="track"
      class="no-scrollbar flex size-full snap-x snap-mandatory overflow-x-auto"
      @scroll.passive="onScroll"
    >
      <img
        v-for="(photo, index) in photos"
        :key="photo"
        :src="photo"
        :alt="index === 0 ? alt : `${alt} — фото ${index + 1}`"
        class="size-full shrink-0 snap-center object-contain"
        :loading="index === 0 ? 'eager' : 'lazy'"
      />
    </div>
    <div v-else class="flex size-full items-center justify-center text-5xl font-semibold text-sf-disabled">
      {{ initial }}
    </div>

    <!-- Точки: сколько ещё фото и где мы сейчас. -->
    <div v-if="photos.length > 1" class="absolute inset-x-0 bottom-5 flex justify-center gap-1.5">
      <span
        v-for="(photo, index) in photos"
        :key="photo"
        class="size-1.5 rounded-full transition-all"
        :class="index === activeIndex ? 'w-4 bg-white' : 'bg-white/60'"
      />
    </div>

    <!-- Кнопки «назад» и сердечко ложатся поверх фото. -->
    <slot name="overlay" />
  </div>
</template>
