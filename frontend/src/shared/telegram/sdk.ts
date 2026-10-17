import {
  init,
  viewport,
  miniApp,
  themeParams,
  retrieveLaunchParams,
  retrieveRawInitData,
  type ViewportGetCSSVarNameKey,
} from '@telegram-apps/sdk'

/**
 * `viewport.bindCssVars()` defaults to the `--tg-viewport-*` naming scheme
 * (e.g. `--tg-viewport-safe-area-inset-top`), but the rest of the app
 * (tailwind.config.js's `safe-top`/`safe-bottom` tokens, App.vue's inline
 * paddings) was written against `--tg-*` without the `viewport` segment.
 * Rather than touch every consumer, generate the names those already expect.
 */
function tgCssVarName(key: ViewportGetCSSVarNameKey): string {
  return `--tg-${key.replace(/[A-Z]/g, (letter) => `-${letter.toLowerCase()}`)}`
}

/** Mobile Telegram clients — the only platforms this storefront should ask
 *  for fullscreen on (desktop/web clients already behave like a normal
 *  window and don't need it). */
function isMobilePlatform(platform: string): boolean {
  return platform === 'ios' || platform === 'android' || platform === 'android_x'
}

/**
 * Bootstraps the Telegram Mini App SDK: initializes the environment, mounts
 * the viewport/theme/mini-app components and syncs their CSS variables onto
 * :root (safe-area insets, theme colors, etc). Safe to call outside of
 * Telegram (e.g. a plain browser during local dev) — all failures are
 * swallowed so the app still boots.
 */
export function initTelegram(): void {
  try {
    init()

    if (viewport.mount.isAvailable()) {
      viewport.mount()
      viewport.bindCssVars(tgCssVarName)
    }

    if (miniApp.mount.isAvailable()) {
      miniApp.mount()
      miniApp.bindCssVars()
    }

    if (themeParams.mount.isAvailable()) {
      themeParams.mount()
      themeParams.bindCssVars()
    }

    if (viewport.expand.isAvailable()) {
      viewport.expand()
    }

    const platform = retrieveLaunchParams().tgWebAppPlatform
    if (isMobilePlatform(platform) && viewport.requestFullscreen.isAvailable()) {
      // Fire-and-forget: older/desktop clients or a user declining the
      // prompt shouldn't block the rest of the app from booting.
      viewport.requestFullscreen().catch(() => {
        // Not supported by this client / request rejected — the app still
        // works fine in the regular expanded (non-fullscreen) viewport.
      })
    }
  } catch {
    // Not running inside Telegram (e.g. local browser dev) — no-op.
  }
}

/**
 * Returns the raw Telegram WebApp init data string, or an empty string when
 * unavailable (e.g. running outside Telegram).
 */
export function getInitDataRaw(): string {
  try {
    return retrieveRawInitData() ?? ''
  } catch {
    return ''
  }
}

/**
 * Returns the current Telegram user from the launch params, or null when
 * unavailable (e.g. running outside Telegram).
 */
export function getTelegramUser() {
  try {
    const { tgWebAppData } = retrieveLaunchParams()
    return tgWebAppData?.user ?? null
  } catch {
    return null
  }
}
