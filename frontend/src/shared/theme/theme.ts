import { computed, ref } from 'vue'
import { getTelegramColorScheme, onTelegramThemeChanged, setTelegramChromeColor } from '@shared/telegram/sdk'

export type ThemeMode = 'light' | 'dark'

const STORAGE_KEY = 'sf-theme'

// Matches the hardcoded --sf-bg values in styles/main.css — duplicated
// here (not read from the CSS var) because Telegram's native chrome needs
// an explicit hex *before* the app's own stylesheet necessarily reflects
// the chosen theme (e.g. the very first paint, driven by index.html's
// inline bootstrap script rather than this module).
const CHROME_COLOR: Record<ThemeMode, string> = {
  light: '#ffffff',
  dark: '#121212',
}

function readStoredTheme(): ThemeMode | null {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    return stored === 'light' || stored === 'dark' ? stored : null
  } catch {
    // Storage unavailable (private mode, disabled cookies/storage) — no
    // stored preference, falls through to the system/Telegram default.
    return null
  }
}

function systemPrefersDark(): boolean {
  return typeof window !== 'undefined' && typeof window.matchMedia === 'function'
    ? window.matchMedia('(prefers-color-scheme: dark)').matches
    : false
}

/**
 * The theme to use absent an explicit user choice: Telegram's own client
 * setting first (so the Mini App matches whatever light/dark mode the
 * person already has Telegram in), then the OS/browser preference — the
 * guest-checkout website fallback (see CLAUDE.md "гостевой чекаут") has no
 * Telegram client to ask.
 */
function resolveSystemTheme(): ThemeMode {
  return getTelegramColorScheme() ?? (systemPrefersDark() ? 'dark' : 'light')
}

const theme = ref<ThemeMode>(readStoredTheme() ?? resolveSystemTheme())
// Once true, system/Telegram theme changes stop overriding `theme` —
// same "manual beats automatic" rule most light/dark toggles use.
const hasManualOverride = ref(readStoredTheme() !== null)

function applyToDocument(value: ThemeMode): void {
  // index.html's inline bootstrap script already set this attribute before
  // any CSS loaded, to avoid a flash of the wrong theme on first paint —
  // this keeps it in sync for every change after that (this module's
  // import is the single source of truth from here on).
  document.documentElement.dataset.theme = value
  setTelegramChromeColor(CHROME_COLOR[value])
}

applyToDocument(theme.value)

/** Explicitly picks a theme and persists it — from this point on, system/
 *  Telegram theme changes no longer override the user's choice. */
export function setTheme(value: ThemeMode): void {
  theme.value = value
  hasManualOverride.value = true
  try {
    localStorage.setItem(STORAGE_KEY, value)
  } catch {
    // Theme still applies for this session, just won't persist on reload.
  }
  applyToDocument(value)
}

export function toggleTheme(): void {
  setTheme(theme.value === 'dark' ? 'light' : 'dark')
}

export const currentTheme = computed(() => theme.value)

function followSystemTheme(): void {
  if (hasManualOverride.value) return
  theme.value = resolveSystemTheme()
  applyToDocument(theme.value)
}

onTelegramThemeChanged(followSystemTheme)

if (typeof window !== 'undefined' && typeof window.matchMedia === 'function') {
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', followSystemTheme)
}
