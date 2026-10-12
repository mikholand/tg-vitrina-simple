const VISITOR_KEY_STORAGE_KEY = 'visitor_key'

/**
 * Returns a persistent random UUID identifying this anonymous visitor.
 * Generated once and stored in localStorage; sent as the `X-Visitor-Key`
 * header on unauthenticated requests so the backend can dedupe anonymous
 * view/visit counts.
 */
export function getVisitorKey(): string {
  let key = localStorage.getItem(VISITOR_KEY_STORAGE_KEY)
  if (!key) {
    key = crypto.randomUUID()
    localStorage.setItem(VISITOR_KEY_STORAGE_KEY, key)
  }
  return key
}
