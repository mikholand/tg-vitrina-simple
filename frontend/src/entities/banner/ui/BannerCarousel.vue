<script setup lang="ts">
import type { Banner } from '@entities/banner/types'

defineProps<{ banners: Banner[] }>()

function onBannerClick(banner: Banner): void {
  if (!banner.link_url) return
  window.open(banner.link_url, '_blank', 'noopener,noreferrer')
}

// Banners uploaded before the mobile/desktop split only have the 16:9 crop
// — fall back to it on wide screens too rather than showing nothing until
// the seller re-uploads a dedicated 4:1 image.
function desktopSrc(banner: Banner): string {
  return banner.image_path_desktop ?? banner.image_path_mobile
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
      class="relative aspect-[16/9] w-full shrink-0 snap-start overflow-hidden rounded-3xl bg-sf-soft md:aspect-[4/1]"
      :class="banner.link_url ? 'cursor-pointer' : 'cursor-default'"
      @click="onBannerClick(banner)"
    >
      <!-- Mobile crop (16:9) — swapped out below the `md` breakpoint for
           the wide 4:1 desktop crop, the same cutoff the rest of the layout
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

      <!-- Desktop crop (4:1), same blurred-background + sharp-foreground
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
</template>
