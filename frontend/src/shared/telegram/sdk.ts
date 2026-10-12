import {
  init,
  viewport,
  miniApp,
  themeParams,
  retrieveLaunchParams,
  retrieveRawInitData,
} from '@telegram-apps/sdk'

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
      viewport.bindCssVars()
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
