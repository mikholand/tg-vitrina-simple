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
// Button) read as green next to the storefront's gold --sf-accent. Seller
// pages use plenty of PrimeVue as-is, so the theme itself is pinned to the
// same warm gold (Alena Zhao brand accent, #c9a15a at 600 — same slot the
// old blue used to sit at) instead of re-skinning each component by hand.
//
// Aura's default "surface" scale is Tailwind's slate scale ({slate.50},
// {slate.200}, {slate.900}, ...) — built for a light theme, and its bundled
// "dark" colorScheme is a different, unrelated dark gray scale — neither
// matches this app's own --sf-card/--sf-line/--sf-ink tokens (main.css,
// which now has its own light AND dark blocks, toggled the same way as
// PrimeVue's below: the `[data-theme="dark"]` attribute on <html>, driven
// by shared/theme/theme.ts). Severity colors (red/green/amber) still line
// up with --sf-danger/--sf-success/--sf-warning in both schemes without
// changes, but the form-field colors below can't lean on {surface.*}
// references in either scheme — overridden with literal hex values that
// mirror main.css's two blocks instead.
const SfPreset = definePreset(Aura, {
  semantic: {
    primary: {
      50: '#fcf8f1',
      100: '#f8f0e3',
      200: '#f2e4ce',
      300: '#e9d3ac',
      400: '#dfc08a',
      500: '#d4af6c',
      600: '#c9a15a',
      700: '#a98447',
      800: '#866934',
      900: '#624c26',
      950: '#3d2f17',
      // Aura's Button/Tag text color reads from here, not a hardcoded
      // white class — white-on-gold fails contrast (the old blue didn't
      // need this override, white-on-blue was already readable).
      contrastColor: '#121212',
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
      // Both slots now map 1:1 to main.css's two --sf-* blocks (literal hex,
      // not var()/`{surface.*}` references — Aura's bundled "surface" scale
      // doesn't match this brand's tokens in either scheme). `darkModeSelector`
      // below tells PrimeVue to pick between them off the same
      // `[data-theme="dark"]` attribute main.css's `:root[data-theme="dark"]`
      // block already keys off, so both stay in sync automatically.
      light: {
        formField: {
          background: '#ffffff',
          borderColor: '#e7e0d2',
          hoverBorderColor: '#d8d0c0',
          color: '#1a1510',
          placeholderColor: '#a89d89',
          disabledBackground: '#f4f0e6',
          disabledColor: '#a89d89',
        },
      },
      dark: {
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
