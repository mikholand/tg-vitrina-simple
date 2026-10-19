import {
  init,
  viewport,
  miniApp,
  themeParams,
  backButton,
  mountSwipeBehavior,
  disableVerticalSwipes,
  retrieveLaunchParams,
  retrieveRawInitData,
  shareURL,
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
 * Mounts `viewport` and binds its CSS vars. Split out so it can be awaited
 * on its own — `requestFullscreen()` only depends on this, not on
 * miniApp/themeParams.
 */
async function mountViewport(): Promise<void> {
  try {
    if (viewport.mount.isAvailable()) {
      await viewport.mount()
      viewport.bindCssVars(tgCssVarName)
    }
  } catch {
    // Viewport unavailable on this client — safe-area vars just won't be set.
  }
}

async function mountMiniApp(): Promise<void> {
  try {
    if (miniApp.mount.isAvailable()) {
      await miniApp.mount()
      miniApp.bindCssVars()
    }
  } catch {
    // Mini app component unavailable — no theme-driven CSS vars from it.
  }
}

async function mountThemeParams(): Promise<void> {
  try {
    if (themeParams.mount.isAvailable()) {
      await themeParams.mount()
      themeParams.bindCssVars()
    }
  } catch {
    // Theme params unavailable — fine, the app uses a fixed light palette.
  }
}

/**
 * Unlike viewport/miniApp/themeParams, `mount()` here is synchronous (no
 * server round-trip) — it just restores the button's last known state.
 * Still wrapped the same way so `showBackButton()`/`hideBackButton()` below
 * stay no-ops on clients without the component instead of throwing.
 */
function mountBackButton(): void {
  try {
    if (backButton.mount.isAvailable()) backButton.mount()
  } catch {
    // Back button unavailable on this client — show/hide calls below are
    // no-ops too, so pages just never get one.
  }
}

/**
 * A swipe-down anywhere on the page is Telegram's own gesture to minimize/
 * close the Mini App — same gesture ProductGallery's photo/video slides use
 * to scroll vertically-adjacent content, and the one a user swiping down to
 * dismiss the on-screen keyboard or just scroll a long description would
 * hit by accident. Disabled app-wide right after boot so none of that
 * accidentally collapses the app.
 */
function disableSwipeToClose(): void {
  try {
    if (mountSwipeBehavior.isAvailable()) mountSwipeBehavior()
    if (disableVerticalSwipes.isAvailable()) disableVerticalSwipes()
  } catch {
    // Unavailable on this client — the gesture just behaves as before.
  }
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
 *
 * `viewport`/`miniApp`/`themeParams` are mounted *concurrently* rather than
 * one after another: each `mount()` is its own round-trip over postMessage
 * to the native client, and `requestFullscreen()` only needs `viewport` to
 * be mounted — chaining all three sequentially before requesting fullscreen
 * (as this used to do) tripled the round-trip latency on first launch for
 * no reason. `miniApp`/`themeParams` are left to mount in the background;
 * only `viewport` is awaited before expand/fullscreen.
 */
export async function initTelegram(): Promise<void> {
  try {
    init()
  } catch {
    // Not running inside Telegram (e.g. a plain browser during local dev).
    return
  }

  const viewportMounted = mountViewport()
  void mountMiniApp()
  void mountThemeParams()
  mountBackButton()
  disableSwipeToClose()

  await viewportMounted

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
 * True when running inside an actual Telegram client (launch params parsed
 * successfully), false in a plain browser (local dev, a desktop web preview
 * outside Telegram). Used to hide UI that would duplicate what Telegram's
 * own chrome already provides there — e.g. ProductDetailPage's own
 * "Назад" button, redundant next to the native Back Button `showBackButton()`
 * already puts in Telegram's header.
 */
export function isInsideTelegram(): boolean {
  try {
    retrieveLaunchParams()
    return true
  } catch {
    return false
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

/**
 * Returns the Mini App deep-link `start_param` (the `startapp=...` value
 * from the `https://t.me/<bot>?startapp=...` link that opened this app), or
 * null when absent / outside Telegram. Checked once at boot to detect an
 * invite link (`startapp=invite_<token>`) — see `app/router/index.ts`.
 */
export function getStartParam(): string | null {
  try {
    return retrieveLaunchParams().tgWebAppStartParam ?? null
  } catch {
    return null
  }
}

/**
 * Opens Telegram's native share sheet pre-filled with `url`/`text`. Only
 * available on real Telegram clients (not desktop web / plain browser) —
 * returns false when unsupported so the caller can fall back to a plain
 * copy-to-clipboard button instead.
 */
export function shareLink(url: string, text?: string): boolean {
  try {
    if (!shareURL.isAvailable()) return false
    shareURL(url, text)
    return true
  } catch {
    return false
  }
}

/**
 * Shows Telegram's native top-left Back Button. Driven centrally from
 * `App.vue` (one watcher on the current route), not from individual pages —
 * see `backButton` section there for which routes get one.
 */
export function showBackButton(): void {
  try {
    if (backButton.show.isAvailable()) backButton.show()
  } catch {
    // Not supported by this client — page just won't have a back button.
  }
}

/** Hides the native Back Button — used on each tab's root screen. */
export function hideBackButton(): void {
  try {
    if (backButton.hide.isAvailable()) backButton.hide()
  } catch {
    // Not supported — no-op.
  }
}

/**
 * Registers a Back Button click handler and returns an unsubscribe function.
 * Outside Telegram (or on clients without the component) the handler simply
 * never fires — callers don't need to branch on support themselves.
 */
export function onBackButtonClick(fn: () => void): VoidFunction {
  try {
    if (backButton.onClick.isAvailable()) return backButton.onClick(fn)
  } catch {
    // Not supported — listener just never gets attached.
  }
  return () => {}
}
