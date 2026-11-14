import type { AnswerKey, AnswerValue, CaseData, FieldKey, Question } from '@/api/types'

export const FIELD_LABELS: Record<FieldKey, string> = {
  jurisdiction_state: "State of issuance", ticket_type: "Ticket type",
  ticket_number: 'Ticket (summons) number', issuing_authority: 'Issuing authority', city: 'City',
  violation_code: 'Violation code', violation_description: 'Violation description',
  issue_date: 'Date of violation', issue_time: 'Time of violation (local time)', location: 'Location',
  amount: 'Fine amount (USD)', plate_number: 'Plate number', plate_state: 'Plate state',
}
// Обязательные для анализа поля (backend требует их до вызова правил).
export const REQUIRED_FIELDS: FieldKey[] = [
  'jurisdiction_state', 'ticket_type',
]

export const CANONICAL_CITY = 'NYC'
export const CANONICAL_AUTHORITY = 'NYC Department of Finance'
const NYC_ALIASES = new Set(['nyc', 'new york', 'new york city', 'new york, ny', 'city of new york', 'ny', 'manhattan', 'brooklyn', 'queens', 'bronx', 'the bronx', 'staten island'])
const DOF_ALIASES = new Set(['nyc department of finance', 'new york city department of finance', 'department of finance', 'nyc dof', 'dof', 'department of finance nyc'])

/** Приводит распознанные значения города/инстанции к каноническим значениям UI. */
export function normalizeExtracted(key: FieldKey, value: string | null): string {
  const v = (value ?? '').trim()
  if (!v) return ''
  const low = v.toLowerCase()
  if (key === 'city' && NYC_ALIASES.has(low)) return CANONICAL_CITY
  if (key === 'issuing_authority' && DOF_ALIASES.has(low)) return CANONICAL_AUTHORITY
  if (key === 'plate_state' || key === 'plate_number') return v.toUpperCase()
  if (key === 'amount') return v.replace(/^\$/, '')
  return v
}

const RX = {
  date: /^\d{4}-\d{2}-\d{2}$/, time: /^(?:[01]\d|2[0-3]):[0-5]\d$/,
  amount: /^\d{1,6}(?:\.\d{1,2})?$/, plate: /^[A-Za-z0-9 -]{1,12}$/, state: /^[A-Za-z]{2}$/,
  zone: /^\d{6}$/, dateTime: /^\d{4}-\d{2}-\d{2}T(?:[01]\d|2[0-3]):[0-5]\d$/,
}

const validDate = (s: string) => { const d = new Date(`${s}T00:00:00Z`); return !Number.isNaN(d.getTime()) && d.toISOString().startsWith(s) }

export function validateField(key: FieldKey, raw: string): string {
  const v = raw.trim()
  if (!v) return REQUIRED_FIELDS.includes(key) ? `${FIELD_LABELS[key]} is required.` : ''
  switch (key) {
    case 'ticket_number':
    case 'violation_code': return v.length <= 64 ? '' : 'Too long (max 64 characters).'
    case 'issue_date': return RX.date.test(v) && validDate(v) ? '' : 'Enter a valid date.'
    case 'issue_time': return RX.time.test(v) ? '' : 'Enter the time as HH:MM.'
    case 'amount': return RX.amount.test(v) ? '' : 'Enter an amount like 65.00.'
    case 'plate_number': return RX.plate.test(v) && /[A-Za-z0-9]/.test(v) ? '' : 'Use letters, digits, spaces or dashes (max 12).'
    case 'plate_state': return RX.state.test(v) ? '' : 'Use a 2-letter state code, e.g. NY.'
    default: return v.length <= 250 ? '' : 'Too long (max 250 characters).'
  }
}

export const ANSWER_LABELS: Record<AnswerKey, string> = {
  payment_method: 'Payment method', evidence_document_id: 'ParkNYC receipt file',
  session_start: 'Session start', session_end: 'Session end',
  session_plate_number: 'Plate on receipt', session_plate_state: 'Plate state on receipt',
  session_zone: 'ParkNYC zone', zone_matches_ticket_location: 'Zone matches ticket location',
  receipt_details_confirmed: 'Details checked against receipt',
}

export function validateAnswer(q: Question, value: AnswerValue, all: Record<string, AnswerValue>): string {
  const empty = value === null || value === undefined || (typeof value === 'string' && !value.trim())
  if (q.type === 'boolean') return value === true ? '' : 'Please confirm to continue.'
  if (empty) return 'This answer is required.'
  const v = String(value).trim()
  switch (q.id) {
    case 'session_zone': return RX.zone.test(v) ? '' : 'The ParkNYC zone is 6 digits.'
    case 'session_plate_state': return RX.state.test(v) ? '' : 'Use a 2-letter state code, e.g. NY.'
    case 'session_plate_number': return RX.plate.test(v) ? '' : 'Use letters, digits, spaces or dashes (max 12).'
    case 'session_start':
    case 'session_end': {
      if (!RX.dateTime.test(v)) return 'Enter a valid date and time.'
      const s = String(all.session_start ?? ''), e = String(all.session_end ?? '')
      if (q.id === 'session_end' && RX.dateTime.test(s) && RX.dateTime.test(e) && e <= s) return 'The end must be after the start.'
      return ''
    }
  }
  if (q.type === 'choice' && q.options.length && !q.options.some((o) => o.value === v)) return 'Choose one of the options.'
  return ''
}

/** Человекочитаемый факт по ID из findings: `confirmed_fields.<field>` или `answers.<field>`. */
export function describeFact(id: string, c: CaseData): { label: string; value: string } | null {
  const [scope, key] = id.split('.')
  if (scope === 'confirmed_fields' && key in FIELD_LABELS) {
    const v = c.confirmed_fields[key as FieldKey]
    return { label: FIELD_LABELS[key as FieldKey], value: v ?? 'not provided' }
  }
  if (scope === 'answers' && key in ANSWER_LABELS) {
    const v = c.answers[key as AnswerKey]
    if (key === 'evidence_document_id') return { label: ANSWER_LABELS[key], value: c.documents.find((d) => d.document_id === v)?.filename ?? 'not provided' }
    return { label: ANSWER_LABELS[key as AnswerKey], value: v === null ? 'not provided' : typeof v === 'boolean' ? (v ? 'Yes' : 'No') : String(v).replace('T', ' ') }
  }
  return null
}
