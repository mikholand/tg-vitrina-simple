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
  type InitOptions,
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

type FallbackLaunchParams = NonNullable<InitOptions['launchParams']>

/**
 * Direct Link Mini Apps (`t.me/<bot>/<short_name>?startapp=...`, this
 * project's share/invite link format — see `BotClient.mini_app_url()`)
 * were observed, on Telegram Web specifically, landing with *only* a bare
 * `?tgWebAppStartParam=...` query string: no `tgWebAppPlatform`, no
 * `tgWebAppVersion`, nothing else. Native clients apparently pass the full
 * launch-params handshake some other way (the bug never reproduced there),
 * but Telegram Web — a plain cross-origin iframe with no native bridge —
 * can only hand data to the page through the URL, and for this link shape
 * it only puts the start param there.
 *
 * The SDK's `retrieveLaunchParams()` requires `tgWebAppPlatform`/
 * `tgWebAppVersion` unconditionally and throws on anything less — and
 * `init()` calls that *internally* before it does anything else (see
 * `@telegram-apps/sdk`'s `init.js`, which calls `configure()`, which calls
 * `retrieveLaunchParams()`). So on this exact link shape `init()` itself
 * throws before ever mounting a single component or sending
 * `iframe_ready` to the host. Telegram Web, having never heard back from
 * the Mini App, repeatedly sends it a `reload_iframe` command to retry —
 * and the SDK's own `init()` listens for that and calls
 * `window.location.reload()` in response. Since the reloaded URL is
 * identical every time, this reproduces forever: an infinite full-page
 * reload loop (observed directly in the user's Network tab — thousands of
 * identical `GET /?tgWebAppStartParam=...` requests), not just a blank
 * screen.
 *
 * `init()` accepts a `launchParams` override specifically to bypass its
 * internal `retrieveLaunchParams()` call, so `initTelegram()` below
 * retries with this minimal, self-constructed object instead of giving up
 * — `tgWebAppPlatform`/`tgWebAppVersion` are fabricated (we have no way to
 * know the real values here), but `tgWebAppPlatform: 'unknown'` safely
 * resolves to "not mobile" in `isMobilePlatform()` further down, so this
 * never mis-triggers the mobile-only fullscreen request. `tgWebAppVersion`
 * is picked high enough (not `'0.0'`, the SDK's own pre-init placeholder)
 * that `.isAvailable()` feature-detection elsewhere in this file doesn't
 * spuriously disable every component.
 *
 * Returns null when there's no start param either — i.e. genuinely outside
 * Telegram (plain browser, local dev), where giving up is correct.
 */
function fallbackLaunchParams(): FallbackLaunchParams | null {
  const startParam = new URLSearchParams(window.location.search).get('tgWebAppStartParam')
  if (!startParam) return null
  return {
    tgWebAppPlatform: 'unknown',
    tgWebAppVersion: '8.0',
    tgWebAppStartParam: startParam,
  } as FallbackLaunchParams
}

/**
 * `retrieveLaunchParams()` wrapped to survive the Direct-Link-on-Telegram-
 * Web scenario `fallbackLaunchParams()` documents above. Every place in
 * this file that previously called the SDK's `retrieveLaunchParams()`
 * directly goes through this instead, so none of them individually have to
 * special-case that scenario (`isInsideTelegram()`, in particular, used to
 * wrongly report "not inside Telegram" here, which showed a redundant
 * second back button on `ProductDetailPage.vue` on top of the native one).
 * Returns null only when truly outside Telegram.
 */
function safeRetrieveLaunchParams(): ReturnType<typeof retrieveLaunchParams> | FallbackLaunchParams | null {
  try {
    return retrieveLaunchParams()
  } catch {
    return fallbackLaunchParams()
  }
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

/**
 * Tells the Telegram client the app has finished loading and its own
 * loading placeholder (a generic grey icon shown over the host-provided
 * iframe/webview) can be dismissed. Without this call Telegram only hides
 * that placeholder once the *page* finishes loading — which, for an SPA,
 * can leave it stuck over fully-rendered, interactive content (observed on
 * Telegram Web opening a product deep link: blank panel, stuck placeholder
 * icon, nothing clickable, despite the page itself having loaded fine).
 * Safe to call as early as possible; unlike `bindCssVars`, it doesn't
 * require `miniApp` to be mounted first.
 */
function markMiniAppReady(): void {
  try {
    if (miniApp.ready.isAvailable()) miniApp.ready()
  } catch {
    // Not supported by this client — no placeholder to dismiss anyway.
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
 *
 * `markMiniAppReady()` fires right after `init()`, ahead of every
 * mount/expand/fullscreen call below — unlike `bindCssVars()` it has no
 * dependency on `miniApp` being mounted, and Telegram's own docs say to
 * call it "as early as possible". Waiting until after the other
 * (round-trip) calls resolve left the host's loading placeholder up over
 * an already-rendered, already-interactive app for a very visible stretch
 * — the "blank panel with a stuck grey icon" symptom seen opening a
 * product deep link on Telegram Web.
 *
 * `init()` is retried once with `fallbackLaunchParams()` (see its docstring
 * above) before giving up — without this retry, a Direct Link opened on
 * Telegram Web throws here on every single attempt (same URL every reload)
 * and the function returns immediately, never mounting anything and never
 * sending `iframe_ready` — which is what drove the infinite reload loop,
 * not just a blank screen.
 */
export async function initTelegram(): Promise<void> {
  try {
    init()
  } catch {
    const fallback = fallbackLaunchParams()
    if (!fallback) return // Genuinely outside Telegram — no start param either.
    try {
      init({ launchParams: fallback })
    } catch {
      // Even the fallback didn't help — bail out same as before.
      return
    }
  }

  markMiniAppReady()

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
    const launchParams = safeRetrieveLaunchParams()
    if (
      launchParams &&
      isMobilePlatform(launchParams.tgWebAppPlatform) &&
      viewport.requestFullscreen.isAvailable()
    ) {
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
  return safeRetrieveLaunchParams() !== null
}

/**
 * True only on mobile Telegram clients (ios/android/android_x) — the same
 * check `initTelegram()` uses above to decide whether to request
 * fullscreen. Desktop/web Telegram clients never go fullscreen, so they
 * never get the floating native header that overlaps page content; pages
 * that compensate for that overlap (see ProductDetailPage.vue) need to know
 * this *in addition to* `isInsideTelegram()` — applying the same clearance
 * on desktop just pushes content down for no reason. False outside Telegram
 * entirely (no launch params → no fullscreen → no overlap either).
 */
export function isMobileTelegramPlatform(): boolean {
  const launchParams = safeRetrieveLaunchParams()
  return launchParams !== null && isMobilePlatform(launchParams.tgWebAppPlatform)
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
  return safeRetrieveLaunchParams()?.tgWebAppData?.user ?? null
}

/**
 * Returns the Mini App deep-link `start_param` (the `startapp=...` value
 * from the `https://t.me/<bot>?startapp=...` link that opened this app), or
 * null when absent / outside Telegram. Checked once at boot to detect an
 * invite link (`startapp=invite_<token>`) — see `app/router/index.ts`.
 *
 * `retrieveLaunchParams()` validates the *entire* launch-params blob, which
 * requires `tgWebAppPlatform`/`tgWebAppVersion` to be present alongside
 * `tgWebAppStartParam` — fine for the regular "Main Mini App" launch (full
 * handshake in the URL hash), but Direct Link Mini Apps
 * (`t.me/<bot>/<short_name>?startapp=...`, used for this project's share/
 * invite links, see `BotClient.mini_app_url()`) were observed in production
 * access logs landing as a bare `GET /?tgWebAppStartParam=product_3` query
 * string with nothing else — Telegram's own documented mechanism for
 * exposing the start param to a page before/without the full handshake.
 * `safeRetrieveLaunchParams()` already falls back to reading
 * `tgWebAppStartParam` straight off `location.search` for exactly this case
 * (see `fallbackLaunchParams()`), so this just reads through it.
 */
export function getStartParam(): string | null {
  return safeRetrieveLaunchParams()?.tgWebAppStartParam ?? null
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
