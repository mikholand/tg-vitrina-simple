# Page Component Dependency Trees

Traced by following every `import` in each page's `<script setup>` recursively
(relative and `@`-alias imports), skipping `node_modules`/library imports (PrimeVue
auto-imported components, `vue`, `vue-router`, `zod`, etc.) and skipping pure-type
imports (`import type { X } from ...`). Non-`.vue` first-party imports that matter for
behavior (Pinia stores, `api.ts` functions, `shared/` composables) are listed inline
and annotated — they are not component files, so they don't recurse further, but they
are included because they explain what data a component tree actually renders.

9 pages traced (home, catalog, product, cart, favorites, orders, and 3 representative
seller/* pages), covering every shared UI primitive and every entity `ui/*.vue`
component in the app.

---

## / (Home Page)
Entry: `frontend/src/pages/home/HomePage.vue`
Dependencies:
- `frontend/src/shared/telegram/sdk.ts` — `addToHomeScreen`, `checkHomeScreenStatus` (composable functions, not components)
- `frontend/src/shared/ui/AppSpinner.vue`
- `frontend/src/entities/product/api.ts` — `getCatalogProducts` (API call)
- `frontend/src/entities/product/ui/ProductCard.vue`
  - `frontend/src/entities/product/labels.ts` — `availabilityChipClasses`, `availabilityLabels`, `formatPrice`
  - `frontend/src/entities/product/stock.ts` — `isOutOfStock`, `maxCartQuantity`, `shouldShowQuantity`
  - `frontend/src/entities/favorite/store.ts` — `useFavoriteStore` (Pinia)
  - `frontend/src/entities/cart/store.ts` — `useCartStore` (Pinia)
- `frontend/src/entities/store-info/store.ts` — `useStoreInfoStore` (Pinia)
- `frontend/src/entities/favorite/store.ts` — `useFavoriteStore` (Pinia, shared instance)
- `frontend/src/entities/banner/store.ts` — `useBannerStore` (Pinia)
- `frontend/src/entities/banner/ui/BannerCarousel.vue`
- `frontend/src/shared/seo/useSeoMeta.ts` — `toAbsoluteUrl`, `useSeoMeta` (composable)

---

## /catalog (Catalog Page)
Entry: `frontend/src/pages/catalog/CatalogPage.vue`
Dependencies:
- `frontend/src/shared/ui/AppSpinner.vue`
- `frontend/src/entities/product/api.ts` — `getCatalogProducts`
- `frontend/src/entities/product/ui/ProductCard.vue`
  - (same sub-tree as in Home Page above: `labels.ts`, `stock.ts`, `favorite/store.ts`, `cart/store.ts`)
- `frontend/src/entities/category/store.ts` — `useCategoryStore` (Pinia; exposes `categories` + `tree`)
- `frontend/src/entities/favorite/store.ts` — `useFavoriteStore` (Pinia)
- `frontend/src/entities/store-info/store.ts` — `useStoreInfoStore` (Pinia)
- `frontend/src/shared/seo/useSeoMeta.ts` — `useSeoMeta`

---

## /product/:id (Product Detail Page)
Entry: `frontend/src/pages/product/ProductDetailPage.vue`
Dependencies:
- `frontend/src/shared/ui/AppSpinner.vue`
- `frontend/src/entities/product/api.ts` — `getCatalogProduct`
- `frontend/src/entities/product/labels.ts` — `availabilityLabels`, `formatPrice`
- `frontend/src/entities/product/stock.ts` — `isOutOfStock`, `maxCartQuantity`, `shouldShowQuantity`
- `frontend/src/entities/product/ui/ProductGallery.vue` (leaf — no further first-party imports besides types)
- `frontend/src/entities/favorite/store.ts` — `useFavoriteStore` (Pinia)
- `frontend/src/entities/cart/store.ts` — `useCartStore` (Pinia)
- `frontend/src/entities/store-info/store.ts` — `useStoreInfoStore` (Pinia)
- `frontend/src/entities/category/store.ts` — `useCategoryStore` (Pinia)
- `frontend/src/entities/contact/api.ts` — `getCatalogContacts`
- `frontend/src/features/contact-picker/ContactPicker.vue`
  - `frontend/src/entities/contact/labels.ts` — `contactTypeIcons`
  - `frontend/src/shared/ui/AppModal.vue`
- `frontend/src/shared/telegram/sdk.ts` — `shareLink`, `isInsideTelegram`, `isMobileTelegramPlatform`
- `frontend/src/shared/seo/useSeoMeta.ts` — `toAbsoluteUrl`, `useJsonLd`, `useSeoMeta`

This is the one route App.vue renders `bare` (no shared header/footer/BottomNav
padding) — the page draws its own full-bleed gallery + fixed bottom action bar.

---

## /cart (Cart Page)
Entry: `frontend/src/pages/cart/CartPage.vue`
Dependencies:
- `frontend/src/entities/product/labels.ts` — `formatPrice`
- `frontend/src/entities/product/stock.ts` — `maxCartQuantity`
- `frontend/src/entities/cart/store.ts` — `useCartStore` (Pinia; `lines`, `products`, `total`, `fetchCartProducts`, `submitOrder`, `addItem`, `setQuantity`, `removeItem`)
- `frontend/src/entities/user/store.ts` — `useAuthStore` (Pinia; `token` gates the guest-contact fields)
- `frontend/src/shared/ui/AppSpinner.vue`
- PrimeVue (auto-imported, no explicit import): `InputText`, `Textarea`, `Message`, `Button`

No sub-component tree beyond `AppSpinner` — line items, totals, and the guest-contact
form are all rendered inline in this page's own template.

---

## /favorites (Favorites Page)
Entry: `frontend/src/pages/favorites/FavoritesPage.vue`
Dependencies:
- `frontend/src/entities/product/api.ts` — `getCatalogProduct` (used only for the anonymous/no-session fallback path — resolves favorited ids one by one)
- `frontend/src/shared/ui/AppSpinner.vue`
- `frontend/src/entities/product/ui/ProductCard.vue`
  - (same sub-tree as in Home Page above)
- `frontend/src/entities/favorite/store.ts` — `useFavoriteStore` (Pinia; `fetchFavorites`, `products`, `ids`)
- `frontend/src/entities/user/store.ts` — `useAuthStore` (Pinia; `token` decides anonymous-vs-logged-in favorites source)

---

## /orders (Orders Page — "Мои заказы")
Entry: `frontend/src/pages/orders/OrdersPage.vue`
Dependencies:
- `frontend/src/entities/cart/api.ts` — `getMyOrders`
- `frontend/src/entities/product/labels.ts` — `formatPrice`
- `frontend/src/entities/user/store.ts` — `useAuthStore` (Pinia; `token` gates the whole page — no session → login prompt)
- `frontend/src/shared/telegram/sdk.ts` — `isInsideTelegram`
- `frontend/src/shared/ui/AppSpinner.vue`
- `frontend/src/features/telegram-login/TelegramLoginButton.vue`
  - `frontend/src/entities/user/store.ts` — `useAuthStore` (Pinia, shared instance)
  - `frontend/src/entities/store-info/store.ts` — `useStoreInfoStore` (Pinia)
  - `frontend/src/shared/telegram/widget.ts` — `mountTelegramLoginWidget`, `TelegramWidgetAuthResult`

---

## /seller (Dashboard Page — "Главное")
Entry: `frontend/src/pages/seller/dashboard/DashboardPage.vue`
Dependencies:
- `frontend/src/entities/user/store.ts` — `useAuthStore` (Pinia; `role` decides whether the "Настройки" tile is shown)

Pure launcher grid — no sub-components, just `RouterLink` tiles rendered from a
computed array.

---

## /seller/products (Seller Products Page)
Entry: `frontend/src/pages/seller/products/SellerProductsPage.vue`
Dependencies:
- `frontend/src/shared/ui/AppSpinner.vue`
- `frontend/src/entities/product/api.ts` — `deleteProduct`, `getSellerProducts`, `hideProduct`, `publishProduct`
- `frontend/src/entities/product/labels.ts` — `productStatusChipClasses`, `productStatusLabels`
- `frontend/src/features/product-editor/ProductEditor.vue`
  - `frontend/src/entities/product/api.ts` — `createSellerProduct`, `updateSellerProduct`, `uploadProductPhoto`, `uploadProductVideo`, `MAX_PHOTO_BYTES`, `MAX_PHOTOS`, `MAX_VIDEO_BYTES`
  - `frontend/src/entities/category/store.ts` — `useCategoryStore` (Pinia; `tree`, `fetchCategories`)
  - `frontend/src/shared/ui/AppModal.vue`
  - `frontend/src/entities/category/ui/CategoryPickNode.vue` (self-recursive; see `components.md`)
  - PrimeVue (auto-imported): `InputText`, `Textarea`, `Select`, `InputNumber`, `ToggleSwitch`
- `frontend/src/features/product-delete/DeleteConfirm.vue`
  - `frontend/src/shared/ui/AppModal.vue`

---

## /seller/settings (Seller Settings Page)
Entry: `frontend/src/pages/seller/settings/SellerSettingsPage.vue`
Dependencies:
- `frontend/src/shared/ui/AppSpinner.vue`
- `frontend/src/entities/seller-settings/api.ts` — `getSellerSettings`, `updateSellerSettings`, `uploadStoreLogo`
- PrimeVue (auto-imported): `Avatar`, `InputText`, `Textarea`, `Message`, `Button`, `Tag`
- `RouterLink` to `seller-contacts` and `seller-team` (navigation only, no embedded components from those pages)

No custom sub-components — logo upload, name/description form, and the two
navigation links to Contacts/Team are all rendered inline in this page's own template.
