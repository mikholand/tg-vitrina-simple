import type { TelegramWidgetAuthData } from '@entities/user/types'

let callbackCounter = 0

/**
 * Embeds Telegram's official Login Widget into `container` — the
 * website-only counterpart to the Mini App's own init_data login (see
 * `getInitDataRaw()` in `./sdk.ts`). Unlike most third-party embeds,
 * Telegram's widget *is* the `<script>` tag itself: the browser replaces
 * it with an `<iframe>` the moment it executes, so this appends a fresh
 * one rather than calling some separate "render" function off a pre-loaded
 * library (see https://core.telegram.org/widgets/login).
 *
 * `onAuth` fires with the signed user payload once someone actually
 * completes the Telegram-side login flow — sent to the backend as-is
 * (`POST /auth/telegram/widget`), which re-derives the hash itself, so
 * nothing from this callback is trusted before that round trip.
 */
export function mountTelegramLoginWidget(
  container: HTMLElement,
  botUsername: string,
  onAuth: (user: TelegramWidgetAuthData) => void,
): void {
  const callbackName = `tgLoginCallback_${callbackCounter++}`
  ;(window as unknown as Record<string, (user: TelegramWidgetAuthData) => void>)[callbackName] =
    onAuth

  container.innerHTML = ''
  const script = document.createElement('script')
  script.async = true
  script.src = 'https://telegram.org/js/telegram-widget.js?22'
  script.setAttribute('data-telegram-login', botUsername)
  script.setAttribute('data-size', 'large')
  script.setAttribute('data-radius', '8')
  script.setAttribute('data-userpic', 'false')
  script.setAttribute('data-onauth', `${callbackName}(user)`)
  container.appendChild(script)
}
