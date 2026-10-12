<script setup lang="ts">
import type { Banner } from '@entities/banner/types'

defineProps<{ banners: Banner[] }>()

function onBannerClick(banner: Banner): void {
  if (!banner.link_url) return
  window.open(banner.link_url, '_blank', 'noopener,noreferrer')
}
</script>

<template>
  <!-- Same native scroll-snap convention as the "Новинки" shelf on the home
       page — no carousel/gallery library in this codebase, so a second one
       for 1-3 slides would be overkill. Snaps to one slide at a time since
       each is full-bleed width, unlike the multi-card product shelf. -->
  <div class="no-scrollbar -mx-4 flex snap-x snap-mandatory overflow-x-auto px-4">
    <button
      v-for="banner in banners"
      :key="banner.id"
      type="button"
      class="aspect-[16/7] w-full shrink-0 snap-start overflow-hidden rounded-3xl bg-sf-soft"
      :class="banner.link_url ? 'cursor-pointer' : 'cursor-default'"
      @click="onBannerClick(banner)"
    >
      <img :src="banner.image_path" alt="" class="size-full object-cover" loading="lazy" />
    </button>
  </div>
</template>
