export const API_BASE_URL: string = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')
// Mock возможен ТОЛЬКО в dev-сборке. В production флаг вычисляется в false и mock-модуль вырезается.
export const USE_MOCK: boolean = import.meta.env.DEV && import.meta.env.VITE_USE_MOCK === 'true'

// Название бренда. Меняется в одном месте.
export const BRAND = 'ticky'

// Цены подписки (USD). Меняются в одном месте.
export const PRICE_YEARLY = 199
export const PRICE_MONTHLY = 20
export const YEARLY_SAVING = PRICE_MONTHLY * 12 - PRICE_YEARLY
