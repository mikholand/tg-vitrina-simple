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

initTelegram()

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
      borderRadius: '0.75rem',
    },
    colorScheme: {
      light: {
        formField: {
          background: '{surface.50}',
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
      cssLayer: {
        name: 'primevue',
        order: 'tailwind-base, primevue, tailwind-utilities',
      },
    },
  },
})
app.use(ToastService)

app.mount('#app')
