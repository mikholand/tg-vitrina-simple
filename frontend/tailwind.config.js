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
        // Text/icon color for content sitting ON a bg-sf-accent (gold) fill —
        // deliberately its own token, not --sf-ink: --sf-accent-ink stays the
        // same fixed dark value in BOTH light and dark themes (see
        // styles/main.css), because --sf-accent itself doesn't change
        // between themes either. If this used --sf-ink/--sf-bg instead, text
        // on gold would flip to white-on-gold in light mode and fail
        // contrast, even though it reads fine in dark mode.
        'sf-accent-ink': 'var(--sf-accent-ink)',
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
