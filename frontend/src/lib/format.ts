// Даты и время — строки, без new Date() для календарных значений (нет сдвига дня из-за часового пояса).
// Везде показываем по-американски, независимо от локали устройства: 11/14/2026 и 1:20 PM.
import { isoToUsDate, isoToUsTime } from '@/lib/usdate'

export const formatDate = (iso: string | null): string => (iso ? isoToUsDate(iso) : '—')
export const formatTime = (t: string | null): string => (t ? isoToUsTime(t) : '—')

/** 'YYYY-MM-DDTHH:MM' (местное время) → '11/14/2026, 1:20 PM' */
export function formatLocalDateTime(v: string | null): string {
  const m = /^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2})$/.exec(v ?? '')
  return m ? `${formatDate(m[1])}, ${formatTime(m[2])}` : (v ?? '—')
}

export function formatMoney(v: string | null): string {
  const n = Number(v)
  return v && Number.isFinite(n) ? n.toLocaleString('en-US', { style: 'currency', currency: 'USD' }) : '—'
}

export function formatCents(cents: number, currency = 'USD'): string {
  return (cents / 100).toLocaleString('en-US', { style: 'currency', currency })
}

export function formatBytes(n: number): string {
  return n >= 1048576 ? `${(n / 1048576).toFixed(1).replace(/\.0$/, '')} MB` : `${Math.max(1, Math.round(n / 1024))} KB`
}

/** Момент времени (ISO с поясом) в часовом поясе пользователя. */
export function formatStamp(iso: string | null | undefined): string {
  if (!iso) return ''
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? '' : d.toLocaleString('en-US', { year: 'numeric', month: '2-digit', day: '2-digit', hour: 'numeric', minute: '2-digit', hour12: true })
}
