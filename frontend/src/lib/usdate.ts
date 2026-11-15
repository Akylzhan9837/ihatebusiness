// Американский ввод даты и времени. Поля — обычный текст, поэтому формат не зависит от локали устройства.
// API остаётся на ISO: дата 2026-11-14, время 13:20, дата+время 2026-11-14T13:20 (NYC local time, без перевода в UTC).

export const DATE_PLACEHOLDER = 'MM/DD/YYYY'
export const TIME_PLACEHOLDER = 'h:mm AM/PM'
export const DATE_EXAMPLE = '11/14/2026'
export const TIME_EXAMPLE = '1:20 PM'

const pad = (n: number) => String(n).padStart(2, '0')

/** Реальная календарная дата (учитывает 30/31 день и високосные годы). */
export function isRealDate(y: number, m: number, d: number): boolean {
  if (!Number.isInteger(y) || y < 1 || y > 9999 || m < 1 || m > 12 || d < 1) return false
  const dt = new Date(0)
  dt.setUTCFullYear(y, m - 1, d)
  return dt.getUTCFullYear() === y && dt.getUTCMonth() === m - 1 && dt.getUTCDate() === d
}

/** '11/14/2026' → '2026-11-14'. null, если формат неверный или даты не существует. */
export function parseUsDate(input: string): string | null {
  const m = /^\s*(\d{1,2})\/(\d{1,2})\/(\d{4})\s*$/.exec(input)
  if (!m) return null
  const [mo, d, y] = [Number(m[1]), Number(m[2]), Number(m[3])]
  return isRealDate(y, mo, d) ? `${m[3]}-${pad(mo)}-${pad(d)}` : null
}

/** '2026-11-14' → '11/14/2026'. Некорректный ввод возвращается как есть. */
export function isoToUsDate(iso: string | null | undefined): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso ?? '')
  return m ? `${m[2]}/${m[3]}/${m[1]}` : (iso ?? '')
}

/**
 * '1:20 PM' → '13:20'. Принимает 1:20pm, 1:20 p.m., 01:20 PM.
 * 12:00 AM → 00:00, 12:00 PM → 12:00, 12:30 AM → 00:30. Часы 1–12, минуты 00–59.
 */
export function parseUsTime(input: string): string | null {
  const m = /^\s*(\d{1,2}):(\d{2})\s*([AaPp])\.?\s*[Mm]\.?\s*$/.exec(input)
  if (!m) return null
  const h = Number(m[1]), min = Number(m[2])
  if (h < 1 || h > 12 || min > 59) return null
  const pm = m[3].toLowerCase() === 'p'
  return `${pad(h % 12 + (pm ? 12 : 0))}:${pad(min)}`
}

/** '13:20' → '1:20 PM'; '00:05' → '12:05 AM'. */
export function isoToUsTime(t: string | null | undefined): string {
  const m = /^([01]\d|2[0-3]):([0-5]\d)$/.exec(t ?? '')
  if (!m) return t ?? ''
  const h = Number(m[1])
  return `${h % 12 || 12}:${m[2]} ${h < 12 ? 'AM' : 'PM'}`
}

/** '2026-11-14T13:20' → { date: '11/14/2026', time: '1:20 PM' }. */
export function splitIsoDateTime(v: string | null | undefined): { date: string; time: string } {
  const m = /^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2})$/.exec(v ?? '')
  return m ? { date: isoToUsDate(m[1]), time: isoToUsTime(m[2]) } : { date: '', time: '' }
}

/** Пара полей → '2026-11-14T13:20' или null, если хоть одна часть неверна. */
export function joinIsoDateTime(date: string, time: string): string | null {
  const d = parseUsDate(date), t = parseUsTime(time)
  return d && t ? `${d}T${t}` : null
}

/** Сообщение об ошибке для одной даты; '' если всё верно. */
export function dateError(input: string, label = 'date'): string {
  if (!input.trim()) return `Enter the ${label} as ${DATE_PLACEHOLDER}, for example ${DATE_EXAMPLE}.`
  if (!/^\s*\d{1,2}\/\d{1,2}\/\d{4}\s*$/.test(input)) return `Use ${DATE_PLACEHOLDER}, for example ${DATE_EXAMPLE}.`
  return parseUsDate(input) ? '' : `${input.trim()} is not a real calendar date. Check the month, day and year.`
}

/** Сообщение об ошибке для одного времени; '' если всё верно. */
export function timeError(input: string, label = 'time'): string {
  if (!input.trim()) return `Enter the ${label} with AM or PM, for example ${TIME_EXAMPLE}.`
  if (!/^\s*\d{1,2}:\d{2}\s*[AaPp]\.?\s*[Mm]\.?\s*$/.test(input)) return `Use h:mm AM or PM, for example ${TIME_EXAMPLE}.`
  return parseUsTime(input) ? '' : 'Hours run from 1 to 12 and minutes from 00 to 59.'
}
