export const API_BASE_URL: string = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')
// Mock возможен ТОЛЬКО в dev-сборке. В production флаг вычисляется в false и mock-модуль вырезается.
export const USE_MOCK: boolean = import.meta.env.DEV && import.meta.env.VITE_USE_MOCK === 'true'

export const BRAND = 'Ticky'
