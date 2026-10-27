export interface StoreInfo {
  name: string
  description: string
  logo: string
  contact_tg: string
  /** Powers the Telegram Login Widget on the plain website — see
   * `shared/telegram/widget.ts` and `features/telegram-login`. */
  bot_username: string
}
