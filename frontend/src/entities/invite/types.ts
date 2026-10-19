export interface Invite {
  token: string
  /** Telegram Mini App deep link — `https://t.me/<bot>?startapp=invite_<token>`. */
  url: string
  expires_at: string
}
