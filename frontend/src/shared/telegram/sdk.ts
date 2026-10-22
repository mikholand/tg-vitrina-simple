/**
 * Thin wrapper around Telegram's own `window.Telegram.WebApp` global —
 * provided by the official `telegram-web-app.js` script, self-hosted at
 * `/js/telegram-web-app.js` (see that file's header comment) and loaded via
 * a plain `<script>` tag in `index.html` *before* this module ever runs.
 *
 * This replaced `@telegram-apps/sdk` (a third-party wrapper package)
 * entirely — removed from package.json too. The switch wasn't cosmetic: on
 * Telegram Web specifically, opening a Direct Link Mini App
 * (`t.me/<bot>/<short_name>?startapp=...`, this project's share/invite link
 * format — see `BotClient.mini_app_url()`) lands the page with *only* a bare
 * `?tgWebAppStartParam=...` query string — no `tgWebAppPlatform`, no
 * `tgWebAppVersion`, nothing else. `@telegram-apps/sdk`'s `init()`
 * internally calls a strict launch-params validator that requires
 * `tgWebAppPlatform`/`tgWebAppVersion` unconditionally and throws on
 * anything less — and it does this *before* ever signalling `iframe_ready`
 * back to the host. Telegram Web, having never heard back, kept sending the
 * page a `reload_iframe` command, which the SDK's own `init()` answered with
 * `window.location.reload()` — same URL, same failure, forever (observed
 * directly: thousands of identical `GET /?tgWebAppStartParam=...` requests
 * in the user's Network tab).
 *
 * The official script has no such validation gate: it posts `iframe_ready`
 * to the parent unconditionally, synchronously, the moment it loads,
 * regardless of what (if anything) it could parse from the URL — so the
 * reload loop's root cause simply doesn't exist here. The tradeoff: this
 * script *also* doesn't read `tgWebAppStartParam` from the query string at
 * all (checked both this self-hosted copy and the current one straight from
 * telegram.org — neither does) — so `getStartParam()` below reads it off the
 * URL itself rather than through `WebApp.initDataUnsafe.start_param`.
 *
 * Every function here is a defensive wrapper: outside Telegram (plain
 * browser, local dev) the script still defines `window.Telegram.WebApp`
 * (it's not gated on actually running inside Telegram), just with empty/
 * default fields (`platform: 'unknown'`, `version: '6.0'`, `initData: ''`)
 * — and even inside Telegram, older clients lack newer methods. Callers
 * never need to branch on support themselves; every function degrades to a
 * safe no-op/null/false instead of throwing.
 */

interface TelegramWebAppUser {
  id: number
  first_name: string
  last_name?: string
  username?: string
  language_code?: string
  photo_url?: string
}

interface TelegramWebAppInitDataUnsafe {
  user?: TelegramWebAppUser
  start_param?: string
}

interface TelegramWebAppBackButton {
  show(): void
  hide(): void
  onClick(fn: () => void): void
  offClick(fn: () => void): void
}

interface TelegramWebApp {
  initData: string
  initDataUnsafe: TelegramWebAppInitDataUnsafe
  version: string
  platform: string
  BackButton: TelegramWebAppBackButton
  isVersionAtLeast(version: string): boolean
  ready(): void
  expand(): void
  enableVerticalSwipes(): void
  disableVerticalSwipes(): void
  requestFullscreen(): void
  exitFullscreen(): void
  addToHomeScreen(): void
  checkHomeScreenStatus(callback: (status: string) => void): void
  openTelegramLink(url: string): void
}

declare global {
  interface Window {
    Telegram?: {
      WebApp?: TelegramWebApp
    }
  }
}

function getWebApp(): TelegramWebApp | undefined {
  return window.Telegram?.WebApp
}

/** Mobile Telegram clients — the only platforms this storefront should ask
 *  for fullscreen on (desktop/web clients already behave like a normal
 *  window and don't need it). */
function isMobilePlatform(platform: string): boolean {
  return platform === 'ios' || platform === 'android' || platform === 'android_x'
}

/**
 * Reads the Mini App deep-link `start_param` straight off the URL rather
 * than through `WebApp.initDataUnsafe.start_param` — see this file's header
 * comment for why: the official script only ever populates that field from
 * the signed `tgWebAppData` blob in the URL *hash* (the native full-handshake
 * path), never from a bare `tgWebAppStartParam` query param, which is
 * exactly the shape Telegram Web Direct Links use.
 */
function readStartParam(): string | null {
  const fromInitData = getWebApp()?.initDataUnsafe?.start_param
  if (fromInitData) return fromInitData

  const fromQuery = new URLSearchParams(window.location.search).get('tgWebAppStartParam')
  if (fromQuery) return fromQuery

  // Defensive: cover a bare `#tgWebAppStartParam=...` hash too, in case some
  // client ever delivers it that way instead of as a query param.
  const fromHash = new URLSearchParams(window.location.hash.replace(/^#/, '')).get(
    'tgWebAppStartParam',
  )
  return fromHash || null
}

/**
 * Tells the Telegram client the app has finished loading and its own
 * loading placeholder (a generic grey icon shown over the host-provided
 * iframe/webview) can be dismissed. Without this call Telegram only hides
 * that placeholder once the *page* finishes loading — which, for an SPA,
 * can leave it stuck over fully-rendered, interactive content. Safe to call
 * as early as possible, unconditionally — unlike the old SDK wrapper, the
 * raw method has no mount/availability precondition.
 */
function markMiniAppReady(): void {
  try {
    getWebApp()?.ready()
  } catch {
    // Not supported by this client — no placeholder to dismiss anyway.
  }
}

/**
 * A swipe-down anywhere on the page is Telegram's own gesture to minimize/
 * close the Mini App — same gesture ProductGallery's photo/video slides use
 * to scroll vertically-adjacent content, and the one a user swiping down to
 * dismiss the on-screen keyboard or just scroll a long description would hit
 * by accident. Disabled app-wide right after boot so none of that
 * accidentally collapses the app. Version-gated (7.7+) by the script itself
 * — it just logs a console warning below that, doesn't throw.
 */
function disableSwipeToClose(): void {
  try {
    getWebApp()?.disableVerticalSwipes()
  } catch {
    // Unavailable on this client — the gesture just behaves as before.
  }
}

/**
 * Bootstraps the Mini App: marks it ready, expands the viewport, disables
 * the swipe-to-close gesture, and requests fullscreen on mobile clients.
 * Safe to call outside of Telegram (e.g. a plain browser during local dev)
 * — every step is independently wrapped and swallows failures so the app
 * still boots.
 *
 * Safe-area CSS vars (`--tg-safe-area-inset-*`, `--tg-content-safe-area-
 * inset-*` — consumed by tailwind.config.js and App.vue/ProductDetailPage.vue)
 * need no JS glue here: the official script requests and binds them onto
 * `document.documentElement` itself, automatically, on load (see
 * `telegram-web-app.js`'s `setSafeAreaInset`/`setContentSafeAreaInset`).
 *
 * Unlike the old `@telegram-apps/sdk`-based version of this function, none
 * of this needs to be async — every call here is a fire-and-forget
 * `postMessage` to the host, not a round-trip promise — but it's kept
 * synchronous-and-void rather than renamed, so `void initTelegram()` in
 * `main.ts` keeps working unchanged.
 */
export function initTelegram(): void {
  markMiniAppReady()

  try {
    getWebApp()?.expand()
  } catch {
    // Already expanded / not supported — no-op.
  }

  disableSwipeToClose()

  try {
    const tg = getWebApp()
    if (tg && isMobilePlatform(tg.platform) && tg.isVersionAtLeast('8.0')) {
      tg.requestFullscreen()
    }
  } catch {
    // Not supported by this client / request rejected — the app still
    // works fine in the regular expanded (non-fullscreen) viewport.
  }
}

/**
 * True when there's real evidence this is actually running inside a
 * Telegram client — not just "the script loaded", since the official script
 * defines `window.Telegram.WebApp` unconditionally even in a plain browser,
 * with default/empty fields. Used to hide UI that would duplicate what
 * Telegram's own chrome already provides there — e.g. ProductDetailPage's
 * own "Назад" button, redundant next to the native Back Button
 * `showBackButton()` already puts in Telegram's header.
 */
export function isInsideTelegram(): boolean {
  const tg = getWebApp()
  if (!tg) return false
  return Boolean(tg.initData) || tg.platform !== 'unknown' || Boolean(readStartParam())
}

/**
 * True only on mobile Telegram clients (ios/android/android_x) — the same
 * check `initTelegram()` uses above to decide whether to request fullscreen.
 * Desktop/web Telegram clients never go fullscreen, so they never get the
 * floating native header that overlaps page content; pages that compensate
 * for that overlap (see ProductDetailPage.vue) need to know this *in
 * addition to* `isInsideTelegram()` — applying the same clearance on desktop
 * just pushes content down for no reason.
 */
export function isMobileTelegramPlatform(): boolean {
  const tg = getWebApp()
  return tg !== undefined && isMobilePlatform(tg.platform)
}

/**
 * Returns the raw Telegram WebApp init data string, or an empty string when
 * unavailable (e.g. running outside Telegram, or a Telegram Web Direct Link
 * that only carries a bare start param — see this file's header comment;
 * there's no signed init data to send the backend in that case either).
 */
export function getInitDataRaw(): string {
  return getWebApp()?.initData ?? ''
}

/**
 * Returns the current Telegram user from the launch params, or null when
 * unavailable (e.g. running outside Telegram, or the Telegram-Web-Direct-
 * Link case where only a bare start param is present).
 */
export function getTelegramUser(): TelegramWebAppUser | null {
  return getWebApp()?.initDataUnsafe?.user ?? null
}

/**
 * Returns the Mini App deep-link `start_param` (the `startapp=...` value
 * from the `https://t.me/<bot>?startapp=...` link that opened this app), or
 * null when absent / outside Telegram. Checked once at boot to detect an
 * invite or product link (`startapp` base64url-encodes the destination
 * app-relative path, e.g. `/invite/<token>`, `/product/<id>`) — see
 * `decodeStartPath()` in `app/router/index.ts`.
 */
export function getStartParam(): string | null {
  return readStartParam()
}

/**
 * Opens Telegram's native share sheet pre-filled with `url`/`text`, via the
 * same `https://t.me/share/url?...` universal link `@telegram-apps/sdk`'s
 * `shareURL()` used internally. Only meaningfully different from a plain
 * link on real Telegram clients — returns false when unsupported so the
 * caller can fall back to a plain copy-to-clipboard button instead.
 */
export function shareLink(url: string, text?: string): boolean {
  try {
    const tg = getWebApp()
    if (!tg) return false
    tg.openTelegramLink(
      `https://t.me/share/url?${new URLSearchParams({ url, text: text ?? '' }).toString()}`,
    )
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
    getWebApp()?.BackButton.show()
  } catch {
    // Not supported by this client — page just won't have a back button.
  }
}

/** Hides the native Back Button — used on each tab's root screen. */
export function hideBackButton(): void {
  try {
    getWebApp()?.BackButton.hide()
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
    const tg = getWebApp()
    if (tg) {
      tg.BackButton.onClick(fn)
      return () => tg.BackButton.offClick(fn)
    }
  } catch {
    // Not supported — listener just never gets attached.
  }
  return () => {}
}

/**
 * Prompts Telegram's native "add to home screen" dialog (Mini Apps v8.0+).
 * Returns false when unsupported so the caller can leave its own UI as-is.
 */
export function addToHomeScreen(): boolean {
  try {
    const tg = getWebApp()
    if (!tg?.isVersionAtLeast('8.0')) return false
    tg.addToHomeScreen()
    return true
  } catch {
    return false
  }
}

/**
 * Wraps the callback-based `WebApp.checkHomeScreenStatus()` in a promise.
 * Resolves to `'unsupported'` — one of Telegram's own documented status
 * values, reused here rather than invented — when this client's version
 * can't even be asked (< 8.0), so `HomePage.vue` can tell "definitely not
 * possible" apart from `'unknown'` (a real "can't tell yet" answer *from*
 * Telegram) and gate the "add to home screen" button correctly either way.
 */
export function checkHomeScreenStatus(): Promise<string> {
  return new Promise((resolve) => {
    try {
      const tg = getWebApp()
      if (!tg?.isVersionAtLeast('8.0')) {
        resolve('unsupported')
        return
      }
      tg.checkHomeScreenStatus(resolve)
    } catch {
      resolve('unsupported')
    }
  })
}
