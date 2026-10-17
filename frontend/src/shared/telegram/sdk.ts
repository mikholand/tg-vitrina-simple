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
 *
 * Each step gets its own try/catch (rather than one big one around the
 * whole function) and `viewport.mount()` is *awaited* before anything that
 * depends on it. On a real client `mount()` round-trips to the native app
 * over postMessage and does NOT resolve synchronously (only a few desktop
 * platforms short-circuit) — calling `bindCssVars()`/`requestFullscreen()`
 * right after an un-awaited `mount()` throws `FunctionNotAvailableError`
 * ("parent component is not mounted"), which — under a single shared
 * try/catch — silently swallowed every later step including fullscreen.
 */
export async function initTelegram(): Promise<void> {
  try {
    init()
  } catch {
    // Not running inside Telegram (e.g. a plain browser during local dev).
    return
  }

  try {
    if (viewport.mount.isAvailable()) {
      await viewport.mount()
      viewport.bindCssVars(tgCssVarName)
    }
  } catch {
    // Viewport unavailable on this client — safe-area vars just won't be set.
  }

  try {
    if (miniApp.mount.isAvailable()) {
      await miniApp.mount()
      miniApp.bindCssVars()
    }
  } catch {
    // Mini app component unavailable — no theme-driven CSS vars from it.
  }

  try {
    if (themeParams.mount.isAvailable()) {
      await themeParams.mount()
      themeParams.bindCssVars()
    }
  } catch {
    // Theme params unavailable — fine, the app uses a fixed light palette.
  }

  try {
    if (viewport.expand.isAvailable()) {
      viewport.expand()
    }
  } catch {
    // Already expanded / not supported — no-op.
  }

  try {
    const platform = retrieveLaunchParams().tgWebAppPlatform
    if (isMobilePlatform(platform) && viewport.requestFullscreen.isAvailable()) {
      await viewport.requestFullscreen()
    }
  } catch {
    // Not supported by this client / request rejected — the app still
    // works fine in the regular expanded (non-fullscreen) viewport.
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
