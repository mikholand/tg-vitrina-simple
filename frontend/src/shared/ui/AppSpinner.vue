<script setup lang="ts">
// Replaces the old plain-text `Загрузка…` paragraph that used to be
// copy-pasted identically (`py-16 text-center text-sf-muted`) into every
// page's loading state — a dozen call sites, see the pages under
// `src/pages/**`. Visually matches the static boot-time preloader in
// `index.html` (same border-spin construction, same --sf-line/--sf-accent
// colors) so there's one consistent spinner look from the very first paint
// (before Vue even mounts) through every in-app loading state afterwards,
// instead of a static preloader handing off to plain "Загрузка…" text.
withDefaults(
  defineProps<{
    /** Smaller inline spinner for a loading state scoped to a sub-section
     *  (e.g. one card within an otherwise-loaded page), as opposed to the
     *  default full-page/tab-level loading state. */
    compact?: boolean
  }>(),
  { compact: false },
)
</script>

<template>
  <div class="flex items-center justify-center" :class="compact ? 'py-4' : 'py-16'">
    <div
      class="animate-spin rounded-full border-sf-line border-t-sf-accent duration-[0.8s]"
      :class="compact ? 'h-5 w-5 border-2' : 'h-10 w-10 border-[3px]'"
      role="status"
      aria-label="Загрузка"
    />
  </div>
</template>
