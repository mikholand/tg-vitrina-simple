/**
 * Hand-rolled head-tag management — no `@vueuse/head`/`@unhead/vue`
 * dependency for what amounts to a handful of `<meta>`/`<link>` writes.
 * Mirrors the existing pattern in `App.vue` (it sets `document.title`
 * directly off `storeInfoStore.storeInfo.name` as the site-wide fallback);
 * `useSeoMeta` below is the per-page override on top of that fallback —
 * `HomePage`/`CatalogPage`/`ProductDetailPage` call it with a getter that
 * composes the store name in too, so the final title stays correct however
 * `storeInfo` and the page's own data happen to resolve relative to each
 * other.
 *
 * This app is a client-rendered SPA with no SSR/prerendering, so none of
 * this is visible to a crawler that doesn't execute JS — acceptable here
 * since the target is Google (which does render JS for indexing), not
 * Telegram's own link-unfurler (which doesn't; that's a separate, harder
 * problem this composable does not attempt to solve).
 */

interface SeoMetaInput {
  title: string
  description?: string | null
  image?: string | null
}

function upsertMeta(attr: 'name' | 'property', key: string, content: string | null | undefined): void {
  const selector = `meta[${attr}="${key}"]`
  let el = document.head.querySelector<HTMLMetaElement>(selector)
  if (!content) {
    el?.remove()
    return
  }
  if (!el) {
    el = document.createElement('meta')
    el.setAttribute(attr, key)
    document.head.appendChild(el)
  }
  el.setAttribute('content', content)
}

function upsertCanonical(path: string): void {
  let link = document.head.querySelector<HTMLLinkElement>('link[rel="canonical"]')
  if (!link) {
    link = document.createElement('link')
    link.setAttribute('rel', 'canonical')
    document.head.appendChild(link)
  }
  link.href = new URL(path, window.location.origin).toString()
}

/** Photo/logo URLs coming off the API are host-relative (`/media/...`, see
 * backend `media_url()`) — og:image/schema.org `image` need an absolute
 * URL per spec, so this resolves against the current origin. */
export function toAbsoluteUrl(path: string): string {
  return new URL(path, window.location.origin).toString()
}

/**
 * Sets document.title + description/Open Graph meta + a canonical link for
 * the current page. `getter` is read inside a `watchEffect`, so call this
 * once per page component with a function (not a resolved object) — it
 * re-runs automatically whenever whatever reactive state it reads (route
 * params, a loaded product, the store name) changes.
 */
export function useSeoMeta(getter: () => SeoMetaInput): void {
  const route = useRoute()
  watchEffect(() => {
    const { title, description, image } = getter()
    document.title = title
    upsertMeta('name', 'description', description)
    upsertMeta('property', 'og:title', title)
    upsertMeta('property', 'og:description', description)
    upsertMeta('property', 'og:image', image)
    upsertMeta('property', 'og:type', 'website')
    upsertCanonical(route.path)
  })
}

/**
 * Injects/replaces a `<script type="application/ld+json">` structured-data
 * block, keyed by `id` so multiple independent callers don't clobber each
 * other's tag. `getter` returning `null` removes the tag (e.g. while a
 * product is still loading).
 */
export function useJsonLd(id: string, getter: () => Record<string, unknown> | null): void {
  watchEffect(() => {
    const data = getter()
    let el = document.head.querySelector<HTMLScriptElement>(`script[data-seo-jsonld="${id}"]`)
    if (!data) {
      el?.remove()
      return
    }
    if (!el) {
      el = document.createElement('script')
      el.type = 'application/ld+json'
      el.dataset.seoJsonld = id
      document.head.appendChild(el)
    }
    el.textContent = JSON.stringify(data)
  })
}
