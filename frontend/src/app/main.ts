import 'primeicons/primeicons.css'
import './styles/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config'
import { definePreset } from '@primeuix/themes'
import Aura from '@primeuix/themes/aura'
import ToastService from 'primevue/toastservice'

import App from './App.vue'
import { router } from './router'
import { initTelegram } from '@shared/telegram/sdk'
// Side-effect import: resolves the initial light/dark theme (Telegram
// colorScheme -> OS prefers-color-scheme -> the localStorage override
// index.html's inline bootstrap script already applied before this module
// even loaded) and keeps `<html data-theme>` in sync afterwards. Imported
// here, not inside App.vue, so the PrimeVue preset below and the rest of
// the app boot already agreeing on a theme instead of racing it.
import '@shared/theme/theme'

void initTelegram()

// PrimeVue's "primary" defaults to Aura's emerald scale, which would make
// every untouched PrimeVue control (ToggleSwitch, ProgressSpinner, Tag,
// Button) read as green next to the app's own accent. Seller pages use
// plenty of PrimeVue as-is, so the theme itself is pinned to match instead
// of re-skinning each component by hand. The scale below is the blue it was
// briefly reverted to everywhere (direct request, undoing the Alena Zhao
// gold rebrand's accent); a further request then asked for dark mode
// specifically to keep that gold instead — since light and dark now
// genuinely disagree on the hue (not just the shade), that split lives in
// `colorScheme.light/dark.primary` below, not in this single scale (see the
// comment there for why). This scale itself still matters as the fallback
// base every other token derives from (e.g. the pale `{primary.50}`
// selection-highlight tint) — left as blue since light mode is unchanged
// from the original revert and is the one actually built from it.
//
// Aura's default "surface" scale is already Tailwind's slate scale under
// the hood ({slate.50}, {slate.200}, {slate.900}, ...) — which is exactly
// what the seller cabinet's --sf-card/--sf-line/--sf-ink tokens are (see
// main.css's `.admin-scheme` block: also reverted back to the original
// gray/white scheme in light mode), so severity colors (red/green/amber)
// line up with --sf-danger/--sf-success/--sf-warning for free, and the
// `formField.light` override below can reference `{surface.*}` directly
// again instead of duplicating literal hex. The cabinet's DARK theme is
// unrelated to this revert (it never had a "before" — see main.css), so
// `formField.dark` below stays pinned to its own literal hex, same as it
// was before this revert.
const SfPreset = definePreset(Aura, {
  semantic: {
    primary: {
      50: '#eff6ff',
      100: '#dbeafe',
      200: '#bfdbfe',
      300: '#93c5fd',
      400: '#60a5fa',
      500: '#3b82f6',
      600: '#2563eb',
      700: '#1d4ed8',
      800: '#1e40af',
      900: '#1e3a8a',
      950: '#172554',
    },
    formField: {
      // Aura's default paddingX/Y (0.75rem/0.5rem) reads noticeably smaller
      // than the hand-rolled pill search bars elsewhere in the app
      // (px-4 py-2.5 = 1rem/0.625rem) — bumped to match so PrimeVue fields
      // feel like the same touch-friendly size, not a cramped afterthought.
      // Button paddingX/Y reference these same tokens, so pill buttons grow
      // in step automatically.
      paddingX: '1rem',
      paddingY: '0.625rem',
      borderRadius: '0.75rem',
      // size="small" components (e.g. the "Добавить" buttons) read from this
      // separate `sm` namespace, not the root paddingX/Y above — left
      // unset it falls back to Aura's stock 0.625rem/0.375rem, which paired
      // with the forced pill radius below produces a squished aspect ratio.
      // Scaled down proportionally from the root override instead.
      sm: {
        paddingX: '0.875rem',
        paddingY: '0.5rem',
      },
    },
    colorScheme: {
      // `darkModeSelector` below tells PrimeVue to pick between these two
      // slots off the same `[data-theme="dark"]` attribute main.css's
      // `:root[data-theme="dark"]` block already keys off, so both stay in
      // sync automatically. PrimeVue form fields only ever render inside
      // the seller cabinet (customer-facing pages use hand-rolled --sf-card
      // inputs, see CLAUDE.md) — `light` below is back to referencing
      // Aura's own untouched `{surface.*}` slate scale, matching the
      // cabinet's reverted-to-original `.admin-scheme` light palette in
      // main.css exactly, instead of duplicating its literal hex here.
      // `dark` stays pinned to its own hex — the cabinet's dark theme was
      // never part of this revert (see main.css).
      light: {
        // Blue — see the top-of-file comment and main.css's --sf-accent.
        // Overridden here (not just via the `primary` scale above) because
        // Aura's own light/dark semantic defaults point `primary.color` at
        // different steps of that one scale ({primary.500} light,
        // {primary.400} dark) — fine when light and dark use the same hue,
        // but insufficient now that they're different hues entirely. This
        // is what Button/ToggleSwitch/Tag/etc. actually read via
        // `{primary.color}`/`{primary.hover.color}`/etc.
        primary: {
          color: '#2563eb',
          contrastColor: '#ffffff',
          hoverColor: '#1d4ed8',
          activeColor: '#1e40af',
        },
        formField: {
          background: '#ffffff',
          borderColor: '{surface.200}',
          hoverBorderColor: '{surface.300}',
          color: '{surface.900}',
          placeholderColor: '{surface.400}',
          disabledBackground: '{surface.200}',
          disabledColor: '{surface.400}',
        },
      },
      dark: {
        // Gold — kept from the Alena Zhao rebrand on direct request, unlike
        // every other dark-mode token here (which matches main.css's
        // `:root[data-theme="dark"]` block, itself unaffected by any of
        // this file's light-mode reverts). hoverColor/activeColor go
        // lighter, not darker, matching Aura's own light-gets-darker/
        // dark-gets-lighter hover convention (see the comment on `light`
        // above).
        primary: {
          color: '#c9a15a',
          contrastColor: '#1a1510',
          hoverColor: '#d4af6c',
          activeColor: '#dfc08a',
        },
        formField: {
          background: '#1e1e1e',
          borderColor: '#2e2e2e',
          hoverBorderColor: '#3f3f46',
          color: '#ffffff',
          placeholderColor: '#52525b',
          disabledBackground: '#262626',
          disabledColor: '#52525b',
        },
      },
    },
  },
  components: {
    // Every hand-rolled button elsewhere in the app is a full pill
    // (rounded-full); PrimeVue's <Button> defaults to the same radius as
    // form fields (12px) unless told otherwise, so it'd be the only
    // non-pill button on the page.
    button: {
      root: {
        borderRadius: '9999px',
      },
    },
  },
})

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(PrimeVue, {
  theme: {
    preset: SfPreset,
    options: {
      // Defaults to 'system', which makes PrimeVue independently follow the
      // OS `prefers-color-scheme` media query — a second theme source the
      // app would have no control over, racing shared/theme/theme.ts's own
      // resolution (Telegram colorScheme / manual toggle included, not just
      // the OS setting). Pointed at the exact same selector
      // tailwind.config.js's `darkMode` already uses and theme.ts already
      // sets on `<html>`, so PrimeVue and the --sf-* tokens in main.css
      // always agree on which scheme is active.
      darkModeSelector: '[data-theme="dark"]',
      cssLayer: {
        name: 'primevue',
        order: 'tailwind-base, primevue, tailwind-utilities',
      },
    },
  },
})
app.use(ToastService)

// Delayed until the router's initial navigation — including the async
// ensureAuthInitialized() / redeemPendingInvite() / pendingStartRedirect()
// guard chain in router/index.ts — fully resolves. app.mount() synchronously
// replaces #app's contents the instant it runs, regardless of whether that
// guard chain has decided where the app actually lands; without this, a
// deep link (e.g. a shared product) would render the home page first (the
// initial `to` before the guard redirects it) and only flash over to the
// real destination once the redirect lands, instead of going there
// directly. The static HTML/CSS preloader in index.html fills the screen
// for this entire window, so there's nothing to flash — it's swapped out
// for the final, already-correct page in one shot.
void router.isReady().then(() => {
  app.mount('#app')
})
