export interface Invite {
  token: string
  /** Telegram Mini App deep link — `https://t.me/<bot>/<short>?startapp=<encoded>`,
   *  where `<encoded>` is `/invite/<token>` base64url-encoded. */
  url: string
  expires_at: string
}
