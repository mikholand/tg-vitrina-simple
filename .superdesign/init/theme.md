# Theme / Design Tokens

## Part 1 — Compact token summary

### Color palette (`--sf-*` CSS variables, defined in `frontend/src/app/styles/main.css`, wired into Tailwind via `frontend/tailwind.config.js`)

No dark theme exists (`darkModeSelector: false` in `main.ts`); these are fixed light
values, deliberately **not** wired to Telegram's `--tg-theme-*` vars — a faithful
visual clone of the original `tg-vitrina` project needs a fixed palette.

| Token | Value | Tailwind class | Usage |
|---|---|---|---|
| `--sf-bg` | `#ffffff` | `bg-sf-bg` / `text-sf-bg` | Customer-facing page background |
| `--sf-surface` | `#f3f4f6` | `bg-sf-surface` | Seller cabinet page background (gray, makes white cards read as elevated) |
| `--sf-card` | `#f8fafc` | `bg-sf-card` | Card/input background on customer pages |
| `--sf-accent` | `#2563eb` | `bg-sf-accent` / `text-sf-accent` | Primary blue accent (buttons, links, active states) |
| `--sf-accent-soft` | `#eff4ff` | `bg-sf-soft` | Soft accent background (active nav pill, icon badges) |
| `--sf-ink` | `#0f172a` | `text-sf-ink` | Primary text color |
| `--sf-muted` | `#64748b` | `text-sf-muted` | Secondary/muted text |
| `--sf-line` | `#e2e8f0` | `border-sf-line` | Default border color |
| `--sf-placeholder` | `#94a3b8` | `text-sf-placeholder` | Placeholder text, inactive nav icons |
| `--sf-disabled` | `#cbd5e1` | `text-sf-disabled` | Disabled/empty-state icon color |
| `--sf-success` | `#16a34a` | `text-sf-success` | Success state (in-stock, order confirmed) |
| `--sf-success-soft` | `#f0fdf4` | `bg-sf-success-soft` | Success chip background |
| `--sf-danger` | `#ef4444` | `bg-sf-danger` / `text-sf-danger` | Destructive actions, errors, cart/favorite badges |
| `--sf-danger-soft` | `#fef2f2` | `bg-sf-danger-soft` | Danger chip/warning-block background |
| `--sf-warning` | `#f59e0b` | `text-sf-warning` | Warning state (on-order availability) |
| `--sf-warning-soft` | `#fffbeb` | `bg-sf-warning-soft` | Warning chip background |

### PrimeVue preset overrides (`definePreset(Aura, ...)` in `frontend/src/main.ts`)

- `semantic.primary` — full blue scale (50→950, `#eff6ff` → `#172554`), pinned instead
  of Aura's default emerald, so every untouched PrimeVue control (Button, ToggleSwitch,
  ProgressSpinner, Tag) matches `--sf-accent` (`#2563eb` = primary.600).
- `semantic.formField` — `paddingX: 1rem`, `paddingY: 0.625rem`, `borderRadius: 0.75rem`
  (root); `sm: { paddingX: 0.875rem, paddingY: 0.5rem }` for `size="small"` components.
- `semantic.colorScheme.light.formField` — `background: #ffffff`, `borderColor:
  {surface.200}`, `hoverBorderColor: {surface.300}`, `color: {surface.900}`,
  `placeholderColor: {surface.400}`, `disabledBackground: {surface.200}`,
  `disabledColor: {surface.400}`.
- `components.button.root.borderRadius` — `9999px` (full pill, matching every
  hand-rolled button in the app).
- PrimeVue config: `darkModeSelector: false`, `cssLayer: { name: 'primevue', order:
  'tailwind-base, primevue, tailwind-utilities' }`.

### Typography

- Font family: `'Inter', sans-serif` (set on `body` in `main.css`; no `@font-face` —
  relies on a system/browser-available Inter or falls back to `sans-serif`).
- No custom type-scale config in `tailwind.config.js` — pages use Tailwind's default
  scale directly in templates (commonly seen: `text-xs`, `text-sm`, `text-base`,
  `text-lg`, `text-xl`, `text-2xl`, with `font-medium`/`font-semibold`/`font-bold`
  weights).

### Spacing scale

Default Tailwind spacing scale, extended with two safe-area tokens (for Telegram Mini
App viewport insets, set by `@telegram-apps/sdk`'s `viewport.bindCssVars`, default
`0px` outside Telegram):

| Tailwind class | Value |
|---|---|
| `pt-safe-top` / `safe-top` | `var(--tg-content-safe-area-inset-top, 0px)` |
| `pb-safe-bottom` / `safe-bottom` | `calc(var(--tg-safe-area-inset-bottom, 0px) + var(--tg-content-safe-area-inset-bottom, 0px))` |

### Border radius

No custom radius scale — Tailwind defaults used directly (`rounded-xl`, `rounded-2xl`,
`rounded-3xl`, `rounded-full` are the most common in templates). PrimeVue form
fields/buttons are forced to `0.75rem` / `9999px` respectively via the preset (see
above) to match.

### Shadows

No custom shadow scale — Tailwind defaults (`shadow-sm`, `shadow-lg`) used directly,
occasionally combined with opacity utilities (e.g. `shadow-lg shadow-black/5` on
`BottomNav`'s customer pill).

### Breakpoints

Default Tailwind breakpoints (`sm: 640px`, `md: 768px`, `lg: 1024px`, `xl: 1280px`),
used extensively to widen the mobile-first Mini App layout on desktop/tablet
(`App.vue`'s `max-w-web-app sm:max-w-2xl md:max-w-4xl lg:max-w-6xl xl:max-w-7xl`,
product grids going `grid-cols-2` → `sm:grid-cols-3` → `md:grid-cols-4` →
`lg:grid-cols-5` → `xl:grid-cols-6`).

Custom `maxWidth`:
| Token | Value | Usage |
|---|---|---|
| `max-w-web-app` | `28rem` | The Telegram Mini App's own width cap — the baseline mobile column width before `sm:`/`md:`/etc. widen it |

### Dark mode

None. `darkMode: ['selector', '[data-theme="dark"]']` is configured in
`tailwind.config.js` but nothing in the app ever sets `data-theme="dark"`, and
`darkModeSelector: false` explicitly stops PrimeVue from following the OS/Telegram
`prefers-color-scheme` media query either. Treat this app as light-mode-only.

---

## Part 2 — Raw source dumps

### `frontend/tailwind.config.js`

```js
import tailwindcssPrimeui from 'tailwindcss-primeui'

/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ['selector', '[data-theme="dark"]'],
  content: ['./index.html', './src/**/*.{vue,ts}'],
  theme: {
    extend: {
      colors: {
        'sf-bg': 'var(--sf-bg)',
        'sf-surface': 'var(--sf-surface)',
        'sf-card': 'var(--sf-card)',
        'sf-accent': 'var(--sf-accent)',
        'sf-soft': 'var(--sf-accent-soft)',
        'sf-ink': 'var(--sf-ink)',
        'sf-muted': 'var(--sf-muted)',
        'sf-line': 'var(--sf-line)',
        'sf-placeholder': 'var(--sf-placeholder)',
        'sf-disabled': 'var(--sf-disabled)',
        'sf-danger': 'var(--sf-danger)',
        'sf-danger-soft': 'var(--sf-danger-soft)',
        'sf-success': 'var(--sf-success)',
        'sf-success-soft': 'var(--sf-success-soft)',
        'sf-warning': 'var(--sf-warning)',
        'sf-warning-soft': 'var(--sf-warning-soft)',
      },
      spacing: {
        // Mirrors tg-vitrina's safe-area tokens: `safe-top` is the
        // content-safe inset (below Telegram's own floating header in
        // fullscreen mode), `safe-bottom` adds the home-indicator inset on
        // top of it. Both vars are set by @telegram-apps/sdk
        // (viewport.bindCssVars) and default to 0 outside Telegram.
        'safe-top': 'var(--tg-content-safe-area-inset-top, 0px)',
        'safe-bottom':
          'calc(var(--tg-safe-area-inset-bottom, 0px) + var(--tg-content-safe-area-inset-bottom, 0px))',
      },
      maxWidth: {
        'web-app': '28rem',
      },
    },
  },
  plugins: [tailwindcssPrimeui],
}
```

### `frontend/src/app/styles/main.css`

```css
@layer tailwind-base, primevue, tailwind-utilities;

/* Tailwind v3's @tailwind directives do NOT wrap their own output in
   @layer blocks — they emit plain, unlayered CSS. Per the CSS Cascade
   Layers spec, unlayered rules always beat ANY layered rule regardless of
   layer order or selector specificity, so without this explicit wrapping
   Tailwind's preflight button reset (background-color: transparent;
   padding: 0) silently overrode PrimeVue's .p-button styles (which PrimeVue
   injects inside `@layer primevue`), even though the theme tokens
   themselves were configured correctly. Wrapping base/utilities in the
   named layers declared above makes the `@layer tailwind-base, primevue,
   tailwind-utilities;` ordering above actually take effect. */
@layer tailwind-base {
  @tailwind base;
}

@tailwind components;

@layer tailwind-utilities {
  @tailwind utilities;
}

:root {
  /* Storefront palette — ported verbatim from tg-vitrina (the original
     project this is a slimmed-down rebuild of) so the storefront looks
     pixel-identical regardless of the visitor's Telegram theme: white
     background, cool greys, blue accent. Deliberately NOT wired to
     --tg-theme-* vars (unlike the previous revision of this file) — a
     faithful visual clone needs a fixed palette, not one that follows the
     user's dark/light mode. */
  --sf-bg: #ffffff;
  /* tg-vitrina's cabinet runs on a separate gray --surface, not its white
     storefront --sf-bg — the gray is what makes white shadow-sm cards (see
     DashboardPage) actually read as elevated instead of blending into the
     page. Customer-facing pages keep --sf-bg; only the seller cabinet uses
     this (see App.vue's root background class). */
  --sf-surface: #f3f4f6;
  --sf-card: #f8fafc;
  --sf-accent: #2563eb;
  --sf-accent-soft: #eff4ff;
  --sf-ink: #0f172a;
  --sf-muted: #64748b;
  --sf-line: #e2e8f0;
  --sf-placeholder: #94a3b8;
  --sf-disabled: #cbd5e1;

  --sf-success: #16a34a;
  --sf-success-soft: #f0fdf4;
  --sf-danger: #ef4444;
  --sf-danger-soft: #fef2f2;
  --sf-warning: #f59e0b;
  --sf-warning-soft: #fffbeb;
}

body {
  font-family: 'Inter', sans-serif;
}

/* Telegram Mini Apps are touch/swipe-driven, so the OS scrollbar track is
   pure visual clutter here (most visible as a thin grey strip down the
   right edge on desktop Telegram/Chrome) — scrolling itself still works
   with it hidden. Applied to the document root, not a wrapper div: the
   page body itself is what actually overflows/scrolls on every route. */
html {
  scrollbar-width: none;
}

html::-webkit-scrollbar {
  display: none;
}

.no-scrollbar::-webkit-scrollbar {
  display: none;
}

.no-scrollbar {
  scrollbar-width: none;
}
```

### `definePreset(Aura, ...)` block — from `frontend/src/main.ts`

```ts
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
```
