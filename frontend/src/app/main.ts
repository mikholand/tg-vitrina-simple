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
