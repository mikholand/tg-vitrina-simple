<script setup lang="ts">
import type { Banner } from '@entities/banner/types'

defineProps<{ banners: Banner[] }>()

function onBannerClick(banner: Banner): void {
  if (!banner.link_url) return
  window.open(banner.link_url, '_blank', 'noopener,noreferrer')
}

// Banners uploaded before the mobile/desktop split only have the 16:9 crop
// — fall back to it on wide screens too rather than showing nothing until
// the seller re-uploads a dedicated 3:1 image.
function desktopSrc(banner: Banner): string {
  return banner.image_path_desktop ?? banner.image_path_mobile
}

// Arrow controls on top of the native scroll-snap track — swipe/scroll still
// works unchanged, this just gives a mouse-driven way to step one slide at a
// time. Each slide is exactly the scrollport's own width (`w-full`), so
// stepping by `clientWidth` always lands precisely on the next/previous
// snap point.
const scrollEl = ref<HTMLDivElement | null>(null)
const atStart = ref(true)
const atEnd = ref(true)

function updateEdges(): void {
  const el = scrollEl.value
  if (!el) return
  atStart.value = el.scrollLeft <= 1
  atEnd.value = el.scrollLeft >= el.scrollWidth - el.clientWidth - 1
}

function scrollByOne(direction: -1 | 1): void {
  const el = scrollEl.value
  if (!el) return
  el.scrollBy({ left: direction * el.clientWidth, behavior: 'smooth' })
}

onMounted(() => {
  updateEdges()
})
</script>

<template>
  <!-- Relative wrapper just to anchor the two arrow buttons below over the
       scroll track — they're overlay controls, not part of the scrollable
       content itself. -->
  <div class="relative">
    <!-- Same native scroll-snap convention as the "Новинки" shelf on the home
         page — no carousel/gallery library in this codebase, so a second one
         for 1-3 slides would be overkill. Snaps to one slide at a time since
         each is full-bleed width, unlike the multi-card product shelf. -->
    <div
      ref="scrollEl"
      class="no-scrollbar flex snap-x snap-mandatory overflow-x-auto"
      @scroll="updateEdges"
    >
      <button
        v-for="banner in banners"
        :key="banner.id"
        type="button"
        class="relative aspect-[16/9] w-full shrink-0 snap-start overflow-hidden rounded-3xl bg-sf-soft md:aspect-[3/1]"
        :class="banner.link_url ? 'cursor-pointer' : 'cursor-default'"
        @click="onBannerClick(banner)"
      >
        <!-- Mobile crop (16:9) — swapped out below the `md` breakpoint for
             the wide 3:1 desktop crop, the same cutoff the rest of the layout
             (App.vue's max-width steps, HomePage's padding) switches at. -->
        <!-- Blurred cover fills the slot edge-to-edge regardless of the
             uploaded image's own aspect ratio, so the foreground image below
             never leaves bare background bars. scale-110 hides the lighter
             halo blur() otherwise leaves at the edges of a cropped image. -->
        <img
          :src="banner.image_path_mobile"
          alt=""
          aria-hidden="true"
          class="absolute inset-0 size-full scale-110 object-cover blur-xl md:hidden"
          loading="lazy"
        />
        <!-- Sharp foreground, shown in full via object-contain (not cover) so
             nothing near the edges — logo, phone numbers, promo text — gets
             cropped on screens whose width doesn't match the source image's
             own aspect ratio. -->
        <img
          :src="banner.image_path_mobile"
          alt=""
          class="relative size-full object-contain md:hidden"
          loading="lazy"
        />

        <!-- Desktop crop (3:1), same blurred-background + sharp-foreground
             pairing as the mobile pair above. -->
        <img
          :src="desktopSrc(banner)"
          alt=""
          aria-hidden="true"
          class="absolute inset-0 hidden size-full scale-110 object-cover blur-xl md:block"
          loading="lazy"
        />
        <img
          :src="desktopSrc(banner)"
          alt=""
          class="relative hidden size-full object-contain md:block"
          loading="lazy"
        />
      </button>
    </div>

    <!-- Step-by-one arrow controls — only meaningful with more than one
         slide. Fade out (rather than unmount) at each end so the layout
         never jumps, and `pointer-events-none` on a hidden arrow keeps it
         from eating clicks meant for the banner underneath. -->
    <template v-if="banners.length > 1">
      <button
        type="button"
        aria-label="Предыдущий баннер"
        class="absolute left-2 top-1/2 flex size-8 -translate-y-1/2 items-center justify-center rounded-full bg-black/40 text-white backdrop-blur-sm transition-opacity"
        :class="atStart ? 'pointer-events-none opacity-0' : 'opacity-100'"
        @click="scrollByOne(-1)"
      >
        <i class="pi pi-chevron-left text-sm" />
      </button>
      <button
        type="button"
        aria-label="Следующий баннер"
        class="absolute right-2 top-1/2 flex size-8 -translate-y-1/2 items-center justify-center rounded-full bg-black/40 text-white backdrop-blur-sm transition-opacity"
        :class="atEnd ? 'pointer-events-none opacity-0' : 'opacity-100'"
        @click="scrollByOne(1)"
      >
        <i class="pi pi-chevron-right text-sm" />
      </button>
    </template>
  </div>
</template>
