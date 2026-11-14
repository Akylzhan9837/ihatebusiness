// Даты и время — строки, без new Date() для календарных значений (нет сдвига дня из-за часового пояса).
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

export function formatDate(iso: string | null): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso ?? '')
  return m ? `${MONTHS[Number(m[2]) - 1]} ${Number(m[3])}, ${m[1]}` : (iso ?? '—')
}

export function formatTime(t: string | null): string {
  const m = /^(\d{2}):(\d{2})$/.exec(t ?? '')
  if (!m) return t ?? '—'
  const h = Number(m[1])
  return `${h % 12 || 12}:${m[2]} ${h < 12 ? 'AM' : 'PM'}`
}

/** 'YYYY-MM-DDTHH:MM' (местное время NYC) → 'Nov 2, 2026, 1:30 PM' */
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
  return Number.isNaN(d.getTime()) ? '' : d.toLocaleString('en-US', { dateStyle: 'medium', timeStyle: 'short' })
}
