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

void initTelegram()

// PrimeVue's "primary" defaults to Aura's emerald scale, which would make
// every untouched PrimeVue control (ToggleSwitch, ProgressSpinner, Tag,
// Button) read as green next to the storefront's blue --sf-accent. Seller
// pages use plenty of PrimeVue as-is, so the theme itself is pinned to the
// same blue instead of re-skinning each component by hand.
//
// Aura's default "surface" scale is already Tailwind's slate scale under
// the hood ({slate.50}, {slate.200}, {slate.900}, ...) — which is exactly
// what --sf-card/--sf-line/--sf-ink/etc. were built from (see main.css), so
// severity colors (red/green/amber) already line up with --sf-danger/
// --sf-success/--sf-warning for free. The one real mismatch is which shade
// of that scale each form-field token points at by default (white
// background instead of --sf-card, a too-dark border/placeholder, a
// too-small border radius) — overridden below so every PrimeVue input,
// textarea, select, and button matches the rest of the app's rounded
// sf-card look without hand-styling each component instance.
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
      light: {
        formField: {
          // White, not {surface.50} (a faint off-white) — same call as the
          // hand-rolled bg-sf-card -> bg-white switch on the categories page:
          // against the gray seller-cabinet background, off-white read as
          // barely distinguishable from the surrounding card.
          background: '#ffffff',
          borderColor: '{surface.200}',
          hoverBorderColor: '{surface.300}',
          color: '{surface.900}',
          placeholderColor: '{surface.400}',
          disabledBackground: '{surface.200}',
          disabledColor: '{surface.400}',
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
      // Defaults to 'system', which makes PrimeVue independently follow
      // the OS/Telegram `prefers-color-scheme: dark` media query — on a
      // device with dark theme active this flips Dialog and ToggleSwitch
      // (among others) to Aura's dark palette while the rest of the app
      // (styled via the static, deliberately-light --sf-* tokens in
      // main.css) stays light. The app has no dark mode of its own, so
      // PrimeVue should never switch palettes either.
      darkModeSelector: false,
      cssLayer: {
        name: 'primevue',
        order: 'tailwind-base, primevue, tailwind-utilities',
      },
    },
  },
})
app.use(ToastService)

app.mount('#app')
