# Extractable Design-Tool Components

Catalog of components worth modeling as reusable design-tool components, grouped by
Layout (appear on most/all pages) and Basic (reused across several pages but not
every page). No full source here — see `components.md` / `layouts.md` for that; this
file is props/variants only.

Many "components" below are not literally extracted `.vue` files in the source (the
app repeats inline Tailwind markup instead of a shared atom in several places — e.g.
there is no `Button.vue` or `Badge.vue`) — those are marked **(inline pattern)** and
point at the first representative call site.

---

## Layout

### BottomNav
- Source: `frontend/src/widgets/nav/BottomNav.vue`
- Category: layout
- Description: Fixed bottom navigation; renders a floating pill (customer) or a flat
  bordered tab bar (seller/admin/moderator) depending on section.
- Extractable props: `variant` ("customer" | "seller" | "moderator" — selects which
  item set and visual style to show), `activePath` (which tab is highlighted),
  `cartBadgeCount` (number shown on the Корзина tab, customer variant only).
- Hardcoded: all 5 customer labels/icons/paths (Витрина/Каталог/Избранное/Корзина/
  Заказы, `pi-home`/`pi-th-large`/`pi-heart`/`pi-shopping-cart`/`pi-receipt`), all 5
  seller labels/icons/paths (Главное/Товары/Категории/Статистика/Настройки), the
  `--sf-*` color classes, pill vs. flat-bar CSS shape.

### AppHeader (customer variant)
- Source: inline in `frontend/src/app/App.vue` (first `<header v-if="!isInAdminSection...">` block)
- Category: layout
- Description: Logo/initial avatar + shop name on the left; briefcase link (staff
  only) or login/profile block (website visitors) on the right.
- Extractable props: `storeName`, `storeLogoUrl` (nullable → falls back to initial
  avatar), `isStaff` (shows briefcase link), `isOutsideTelegram` (shows login/profile
  block instead of nothing), `currentUserName`, `currentUserPhotoUrl` (nullable).
- Hardcoded: `pi-briefcase`/`pi-sign-out`/`pi-user` icons, "Админка"/"Выйти" labels,
  avatar size (`size-9`/`size-7`), `--sf-accent` initial-avatar background.

### AppHeader (seller/admin variant)
- Source: inline in `frontend/src/app/App.vue` (second `<header v-if="isInAdminSection...">` block)
- Category: layout
- Description: Shop name (links to dashboard) on the left; store↔admin switcher +
  settings gear (owner only) on the right.
- Extractable props: `storeName`, `isOwner` (shows settings gear).
- Hardcoded: `pi-shop`/`pi-briefcase`/`pi-cog` icons, "Магазин"/"Админка"/"Настройки"
  aria-labels, no logo/avatar (seller header never shows one, unlike customer header).

### AppShell / App root
- Source: `frontend/src/app/App.vue` (whole file)
- Category: layout
- Description: The single page wrapper — safe-area padding, header switch, router
  view, footer, BottomNav. Everything else in the app renders inside this.
- Extractable props: `bare` (true only for product-detail — suppresses
  header/footer/BottomNav spacing), `section` ("customer" | "admin" — drives
  background color `--sf-bg` vs `--sf-surface` and which header renders).
- Hardcoded: the "Разработано Polki Tech" agency-credit footer text + link, the
  `max-w-web-app sm:max-w-2xl md:max-w-4xl lg:max-w-6xl xl:max-w-7xl` responsive
  width ladder, Telegram safe-area CSS var names.

---

## Basic

### ProductCard
- Source: `frontend/src/entities/product/ui/ProductCard.vue`
- Category: basic
- Description: Storefront product tile — image/initial, favorite toggle, add-to-cart
  with badge, name, price, availability chip. Used on Home, Catalog, Favorites.
- Extractable props: `imageUrl` (nullable), `name`, `price` (formatted), `isFavorite`,
  `cartQuantity`, `availabilityLabel` (nullable — hidden when `unknown`),
  `availabilityVariant` ("in_stock" | "on_order" | "out_of_stock"), `outOfStock`
  (hides add-to-cart button).
- Hardcoded: the 5-color tint palette keyed by product id, `pi-heart`/`pi-heart-fill`/
  `pi-shopping-cart` icons, card radius (`rounded-3xl`)/aspect ratio (`aspect-square`).

### ProductGallery
- Source: `frontend/src/entities/product/ui/ProductGallery.vue`
- Category: basic
- Description: Swipeable photo/video gallery with position dots and an `overlay`
  slot. Used only on Product Detail, but is a clear reusable design-tool pattern
  (media carousel).
- Extractable props: `photos` (array of URLs), `video` (nullable URL), `alt` text.
- Hardcoded: dot size/active-width (`size-1.5` / `w-4`), `aspect-[4/5]` ratio,
  rounded-bottom-only shape (`rounded-b-[2rem]`).

### BannerCarousel
- Source: `frontend/src/entities/banner/ui/BannerCarousel.vue`
- Category: basic
- Description: Full-bleed promo banner carousel on Home, with mobile/desktop crop
  pairs and step arrows.
- Extractable props: `banners` (array of `{ imageUrlMobile, imageUrlDesktop?,
  linkUrl? }`), `showArrows` (derived from `banners.length > 1`).
- Hardcoded: `aspect-[16/9]` mobile / `aspect-[3/1]` desktop crop ratios, blur/scale
  background-image treatment, arrow icon size/position.

### CategoryTile / CategoryChip
- Source: inline in `frontend/src/pages/catalog/CatalogPage.vue` (`tiles` grid +
  `chips` row) **(inline pattern)**
- Category: basic
- Description: Two related but distinct pieces on the catalog page — a square root-
  category tile grid ("Все" + each root) and a horizontal pill-chip row for child
  categories of the selected root.
- Extractable props (tile): `label`, `letterInitial`, `tint`, `active`. (chip):
  `label`, `active`.
- Hardcoded: the 5-color tint palette (shared with ProductCard's), tile min-height
  (`min-h-[6.25rem]`), chip/tile active-state color swap to solid `--sf-accent`.

### StatusChip / AvailabilityChip
- Source: `frontend/src/entities/product/labels.ts` (`availabilityChipClasses`,
  `productStatusChipClasses`) consumed in `ProductCard.vue` and
  `SellerProductsPage.vue` **(inline pattern — a class-lookup table, not a component)**
- Category: basic
- Description: Small rounded pill showing product availability (в наличии/на заказ/
  нет в наличии) or seller product status (draft/published/hidden).
- Extractable props: `label`, `variant` (maps to one of `--sf-success`/`--sf-warning`/
  `--sf-danger`/neutral soft-background pairs).
- Hardcoded: `rounded-full px-2 py-0.5 text-[0.65rem]` sizing, the exact
  variant→color mapping.

### CategoryNode (seller category tree)
- Source: `frontend/src/entities/category/ui/CategoryNode.vue`
- Category: basic
- Description: Recursive expandable tree row with visibility-toggle and delete
  actions, used on `SellerCategoriesPage.vue`.
- Extractable props: `label`, `childCount`, `expanded`, `hidden`, `isFallback` (hides
  delete action), `togglingBusy`, `deletingBusy`.
- Hardcoded: `pi-chevron-down`/`pi-chevron-right`/`pi-eye`/`pi-eye-slash`/`pi-trash`
  icons, indentation (`ml-4 border-l`), default-expanded behavior.

### CategoryPickNode (checkbox tree)
- Source: `frontend/src/entities/category/ui/CategoryPickNode.vue`
- Category: basic
- Description: Recursive checkbox tree for multi-selecting categories inside
  `ProductEditor`.
- Extractable props: `label`, `checked`, `childCount` (shown when collapsed and >0
  descendants are checked).
- Hardcoded: default-collapsed behavior (opposite of `CategoryNode`), checkbox size
  (`size-4`).

### AppModal (bottom sheet)
- Source: `frontend/src/shared/ui/AppModal.vue`
- Category: basic
- Description: The one shared modal shell — slides up from the bottom, capped width,
  sticky header with title + close button, scrollable body slot. Backs
  `ContactPicker`, `DeleteConfirm`, and `ProductEditor`.
- Extractable props: `visible`, `title`.
- Hardcoded: `rounded-t-2xl`, `max-h-[90vh]`, `max-w-web-app`, fade transition timing
  (`0.2s`).

### AppSpinner
- Source: `frontend/src/shared/ui/AppSpinner.vue`
- Category: basic
- Description: The one shared loading indicator, used on essentially every page with
  async data.
- Extractable props: `compact` (smaller inline variant vs. full-page).
- Hardcoded: border-spin construction, `--sf-line`/`--sf-accent` colors, the two
  fixed sizes (`h-5 w-5` / `h-10 w-10`).

### ContactPicker
- Source: `frontend/src/features/contact-picker/ContactPicker.vue`
- Category: basic
- Description: Bottom-sheet list of a shop's public contacts (built on AppModal),
  shown on Product Detail only when there's more than one contact.
- Extractable props: `contacts` (array of `{ icon, label, value }`), `visible`.
- Hardcoded: `pi-chevron-right` row affordance, icon-badge size (`size-10`).

### DeleteConfirm
- Source: `frontend/src/features/product-delete/DeleteConfirm.vue`
- Category: basic
- Description: Irreversible-delete confirmation sheet (built on AppModal) for the
  seller product list.
- Extractable props: `itemName` (interpolated into the warning text), `busy`,
  `visible`.
- Hardcoded: the Russian warning copy, Cancel/Confirm button split
  (`border-sf-line` vs `bg-sf-danger`).

### TelegramLoginButton
- Source: `frontend/src/features/telegram-login/TelegramLoginButton.vue`
- Category: basic
- Description: "Войти" text-link that opens a centered (not bottom-sheet) modal
  embedding Telegram's official Login Widget. Shown on the customer header (outside
  Telegram) and on Orders page's empty state.
- Extractable props: none meaningful to extract as instance data — it's fully
  self-contained (drives its own visibility + auth store calls); only `visible`
  (internal) could be lifted if the design tool wants to show the open modal state.
- Hardcoded: "Войти"/"Вход через Telegram" copy, centered-modal shape (distinct from
  AppModal's bottom sheet — intentional, see code comment), `pi-user` icon.

### Pill search input
- Source: inline, repeated identically in `frontend/src/pages/home/HomePage.vue`,
  `frontend/src/pages/catalog/CatalogPage.vue`, and (styled variant) in
  `ProductEditor.vue`'s category search **(inline pattern)**
- Category: basic
- Description: Rounded full-width search input with placeholder, used at the top of
  Home and Catalog.
- Extractable props: `placeholder`, `value`.
- Hardcoded: `rounded-full border border-sf-line bg-sf-card px-4 py-2.5` styling,
  `pi` icon absence (no leading search icon in this app's version).

### Primary pill button
- Source: inline, repeated across nearly every page's main CTA (e.g. "Продолжить
  покупки" in `CartPage.vue`, "На главную" in `ProductDetailPage.vue`, "Опубликовать"
  in `SellerProductsPage.vue`) **(inline pattern)** — plus PrimeVue `<Button>` (themed
  to the same pill shape via the preset) used in `CartPage.vue`/`SellerSettingsPage.vue`
- Category: basic
- Description: The one recurring primary-action visual — solid `--sf-accent`
  background, white text, full pill radius.
- Extractable props: `label`, `loading`, `disabled`.
- Hardcoded: `rounded-full bg-sf-accent ... text-white`, disabled opacity (`50%`).
