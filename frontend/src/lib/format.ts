// Даты/время обрабатываем как строки — без new Date(), чтобы не сдвигать день из-за часового пояса.
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

export function formatMoney(v: string | null): string {
  const n = Number(v)
  return v && Number.isFinite(n) ? n.toLocaleString('en-US', { style: 'currency', currency: 'USD' }) : '—'
}

export function formatBytes(n: number): string {
  return n >= 1048576 ? `${(n / 1048576).toFixed(0)} MB` : `${Math.round(n / 1024)} KB`
}
