# Design System — tg-vitrina-simple

## Product context

Self-hosted Telegram Mini App storefront for a **single** Telegram channel. Posts from
the channel become products in a catalog; customers browse/search/favorite/add to cart
inside Telegram (or a plain website fallback with guest checkout), and orders notify
the seller's Telegram chat. The same Mini App also hosts a seller cabinet
(`/seller/*`) for the shop owner/admin/moderator to manage products, categories,
banners, contacts, team and settings.

Key customer pages: Home (`/`), Catalog (`/catalog`), Product detail (`/product/:id`),
Cart (`/cart`), Favorites (`/favorites`), Orders (`/orders`).
Key seller pages: Dashboard (`/seller`), Products, Categories, Banners, Statistics,
Settings, Contacts, Team.

JTBD: a customer wants to quickly browse what's in stock and either buy it (in-app
checkout) or message the seller directly; the seller wants a low-effort way to turn
channel posts into a browsable catalog without maintaining a separate admin tool.

## Current branding & styling (the "faithful" baseline — see `.superdesign/init/theme.md` for full raw tokens)

- **Palette**: white storefront background (`#ffffff`), blue primary accent
  (`#2563eb`, `--sf-accent`), soft blue accent background (`#eff4ff`), cool slate
  neutrals for text/borders (`#0f172a` ink, `#64748b` muted, `#e2e8f0` line), standard
  semantic red/green/amber for danger/success/warning. Seller cabinet runs on a light
  gray page background (`#f3f4f6`) so white cards read as elevated; customer pages run
  on pure white.
- **Typography**: `Inter` is set as the font-family everywhere, but **no font file is
  ever actually loaded** (no Google Fonts link, no `@font-face`, no npm font package
  in `frontend/index.html` or `main.css`) — it silently falls back to the browser's
  generic `sans-serif`. No custom type scale; Tailwind defaults used directly in
  templates.
- **Shape language**: very rounded — `rounded-3xl`/`rounded-2xl` cards, fully pill
  (`rounded-full`) buttons and nav. PrimeVue forced to match via `definePreset`
  (pill buttons, 0.75rem form-field radius).
- **Elevation**: flat — thin 1px borders (`border-sf-line`) rather than shadows on
  most cards; the one shadow in regular use is a soft `shadow-sm`/`shadow-lg
  shadow-black/5` (bottom nav, cabinet dashboard tiles).
- **Layout**: mobile-first fixed max-width column (`max-w-web-app` = 28rem) that steps
  wider at `sm`/`md`/`lg`/`xl` breakpoints; 2→6 column product grids depending on
  breakpoint. Bottom tab bar navigation (floating pill for customers, flat bordered-top
  bar for seller cabinet) instead of a top nav.
- **No dark mode** — fixed light palette by design (ported verbatim from the original
  `tg-vitrina` project this is a rebuild of), deliberately not following Telegram's
  theme variables.
- **Motion**: minimal — CSS `transition-colors` on nav/chip active states, a
  `active:scale-95` tap feedback on seller dashboard tiles, smooth native scroll-snap
  on carousels/shelves. No page-transition or skeleton-loading animation; loading
  states are a single spinner (`AppSpinner.vue`).
- **Icons**: PrimeIcons (`pi pi-*`) throughout, no custom icon set.

## Real brand identity — "Alena Zhao" (adopted 2026-10-28, supersedes the generic blue placeholder below)

The user confirmed the shop is a real premium household-goods retailer ("Alena Zhao",
ТЦ «Дракон Сити» / ТК «Садовод») and selected the "refined current direction" canvas
draft as the structural base, but wants it restyled around the shop's real identity
instead of the generic blue placeholder. Source material: the shop's own logo (now a
Brand Asset, key `alena-zhao-logo`) and an offline pavilion banner photo the user
shared directly (upload of that photo failed with a transient 502 — not available as
`--reference-id` pixels this round, described here from direct visual inspection
instead). A reference-site extraction of `alenazhao.ru` also failed twice (SSL error,
then 502) — site DNA not available this round either.

- **Logo**: circular black badge, thin gold ring border, gold serif "A"/"Z" monogram
  stacked with a small gold dragon/phoenix emblem between them, gold "ZHAO" wordmark
  below. Reuse this exact Brand Asset (`alena-zhao-logo`) wherever the app currently
  shows a logo position (header, favicon fallback) — never substitute initials or a
  generic mark.
- **Palette**: near-black/charcoal backgrounds and surfaces (not pure black — warm
  dark brown-black, like espresso/graphite) as the dominant tone, gold/bronze
  (warm metallic gold, like `#c9a15a`–`#e8c477`) as the sole accent for CTAs, active
  states, icons, dividers and chip highlights. White/off-white for high-contrast body
  text on dark surfaces. This is a deliberate departure from the current `--sf-accent`
  blue — gold is the new accent role, charcoal/graphite is the new "card/surface" role.
- **Materials/mood**: dark marble or brushed-metal textures suggested through subtle
  gradients (not literal photo textures) behind hero/banner areas; soft warm gold
  rim-lighting glow behind product imagery; premium/boutique, not flashy neon-gold —
  think jewelry-store restraint, not casino.
- **Typography**: bold, slightly condensed display type for headlines/section titles
  (echoing the banner's heavy sans headline), paired with a clean, highly legible body
  sans for prices/descriptions/UI chrome — both must actually load (fixing the current
  Inter-never-loads defect still applies).
- **What must NOT change**: page structure (search → banner → shelf → grid), bottom
  pill tab-bar navigation with the same tabs/icons, the product-card pattern
  (image, name, price, availability, favorite+cart actions), mobile-first `~28rem`
  column. The product category itself (household goods/cleaning supplies) is NOT the
  storefront's product line — this app's own placeholder products stay generic, only
  the chrome/palette/typography adopt the brand.

## Visual-direction freedom for this review

The user has approved exploring a genuinely new visual direction, not just structural
tweaks to the current one. Treat the above as the **faithful-reproduction baseline**
(Step 3a and the "refined current direction" variation must match it exactly), but a
second "new direction" variation may deliberately diverge in palette, type, shape
language, and elevation — as long as it still reads as a trustworthy small-shop
storefront (not a generic SaaS landing page), stays mobile-first at the `max-w-web-app`
column width, and keeps the same information architecture (bottom tab nav with the
same 5 customer tabs / cabinet tabs).

## Specific constraints to keep in every variation

- Mobile-first Telegram Mini App column (28rem baseline), bottom tab-bar navigation.
- Russian-language UI copy only.
- Product grid + card pattern (image, name, price, availability chip, favorite/cart
  quick actions) stays recognizable as a product card, whatever its restyle.
- Checkout/contact flows and seller-cabinet information density are out of scope for
  pure visual redesign — focus on the storefront-facing presentation layer.
