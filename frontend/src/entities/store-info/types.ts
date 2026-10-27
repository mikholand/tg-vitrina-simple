export interface StoreInfo {
  name: string
  description: string
  logo: string
  contact_tg: string
  /** Powers Telegram's Login Widget on the plain website (its OIDC
   * `client_id`, the bot's own numeric id) — see `shared/telegram/widget.ts`
   * and `features/telegram-login`. */
  bot_client_id: number
}
