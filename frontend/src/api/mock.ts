// DEV-ONLY mock по контракту. Работает только при import.meta.env.DEV && VITE_USE_MOCK=true.
// Нужен, пока нет app.rules / app.export / AI-ключа. Состояние хранится в localStorage,
// поэтому «новый сеанс» (другая вкладка + ссылка с #key=) можно проверить и на mock.
import { access } from './access'
import { ApiError, noAccessError } from './errors'
import type { Analysis, Answers, Api, CaseData, Draft, Extraction, ExtractedField, FieldKey, PatchCase, Source } from './types'
import { isParkNYCCase, CANONICAL_AUTHORITY, CANONICAL_CITY } from '@/lib/validate'
import { FIELD_KEYS } from './types'

interface Stored { secret: string; data: CaseData }
const LS = 'tc:mock:cases'
const wait = (ms = 500) => new Promise((r) => setTimeout(r, ms))
const uuid = () => crypto.randomUUID()
const nowIso = () => new Date().toISOString()

function load(): Record<string, Stored> { try { return JSON.parse(localStorage.getItem(LS) ?? '{}') } catch { return {} } }
function save(all: Record<string, Stored>) { try { localStorage.setItem(LS, JSON.stringify(all)) } catch { /* noop */ } }
function open(id: string): { all: Record<string, Stored>; c: CaseData } {
  const all = load(); const s = all[id]; const secret = access.get(id)
  if (!secret) throw noAccessError()
  if (!s || s.secret !== secret) throw new ApiError('case_not_found', 'This case could not be opened. Check your private link.', 404)
  return { all, c: s.data }
}
const commit = (all: Record<string, Stored>, c: CaseData) => { c.updated_at = nowIso(); all[c.case_id].data = c; save(all) }

const SRC: Source[] = [
  { id: 'nyc-dof-code-38', title: 'NYC DOF violation codes', url: 'https://www.nyc.gov/site/finance/vehicles/services-violation-codes.page', jurisdiction: 'NYC', topic: 'Code 38', accessed_at: '2026-11-14', relevant_excerpt: 'Code 38: failure to display a receipt or muni-meter receipt.' },
  { id: 'nyc-dot-parknyc', title: 'NYC DOT: paying with ParkNYC', url: 'https://www.nyc.gov/html/dot/html/motorist/parking-rates.shtml', jurisdiction: 'NYC', topic: 'ParkNYC', accessed_at: '2026-11-14', relevant_excerpt: 'Payment can be made through ParkNYC.' },
  { id: 'nyc-dof-dispute', title: 'NYC DOF: Dispute a Ticket', url: 'https://www.nyc.gov/site/finance/vehicles/dispute-a-ticket.page', jurisdiction: 'NYC', topic: 'Filing', accessed_at: '2026-11-14', relevant_excerpt: 'You can dispute a ticket online, by mail or in person.' },
]
const STATE_DIRECTORY: Source = {
  id: 'us-state-agencies', title: 'State governments — USAGov', url: 'https://www.usa.gov/state-governments',
  jurisdiction: 'United States', topic: 'Official state agency directory', kind: 'directory',
  accessed_at: '2026-11-15', relevant_excerpt: 'Use the directory to locate the agency on your notice.',
}
const REQUIRED: FieldKey[] = ['ticket_number', 'issuing_authority', 'city', 'violation_code', 'issue_date', 'issue_time', 'location', 'plate_number', 'plate_state']
const norm = (s: string | null) => (s ?? '').replace(/[\s-]/g, '').toUpperCase()

function evaluate(c: CaseData): Analysis {
  const f = c.confirmed_fields; const a: Answers = c.answers
  const base = { findings: [], missing_information: [], questions: [], next_steps: [], sources: [], draft_available: false }
  if (!isParkNYCCase(f)) {
    const source = f.jurisdiction_state === 'NY' && f.city === CANONICAL_CITY
      && f.issuing_authority === CANONICAL_AUTHORITY && (f.ticket_type === 'camera' || f.ticket_type === 'parking')
      ? SRC[2] : STATE_DIRECTORY
    const missing = [
      !f.jurisdiction_state && 'State where the ticket was issued',
      !f.ticket_number && 'Ticket or notice number',
      !f.issuing_authority && 'Issuing authority',
      (!f.ticket_type || f.ticket_type === 'unknown') && 'Civil ticket type',
      !c.circumstances && 'Your account of what happened',
    ].filter((item): item is string => !!item)
    if (missing.length) return {
      ...base, status: 'needs_information', missing_information: missing, sources: [source],
      summary: 'Add these details to prepare a factual statement.',
    }
    return { ...base, status: 'ready_for_draft', draft_available: true, draft_kind: 'factual',
      summary: 'Prepare a statement using your confirmed details and your account.', sources: [source] }
  }
  const missing = REQUIRED.filter((k) => !f[k])
  if (missing.length) return { ...base, status: 'needs_information', summary: 'Confirm the ticket details first.', missing_information: missing }
  if (a.payment_method !== 'parknyc')
    return { ...base, status: 'no_supported_ground_identified', summary: 'Without a ParkNYC payment, this demo cannot identify a supported ground.', sources: [SRC[1], SRC[2]], next_steps: ['Review the official dispute options yourself.'] }
  const need: Analysis['questions'] = []
  const ask = (id: string, prompt: string, type: Analysis['questions'][number]['type']) => need.push({ id, prompt, type, options: [] })
  if (!a.evidence_document_id) ask('evidence_document_id', 'Upload your ParkNYC receipt', 'evidence')
  if (!a.session_start) ask('session_start', 'Parking session start (NYC local time)', 'datetime')
  if (!a.session_end) ask('session_end', 'Parking session end (NYC local time)', 'datetime')
  if (!a.session_plate_number) ask('session_plate_number', 'Plate number on the receipt', 'text')
  if (!a.session_plate_state) ask('session_plate_state', 'Plate state on the receipt', 'text')
  if (!a.session_zone) ask('session_zone', 'ParkNYC zone number (6 digits)', 'text')
  if (!a.zone_matches_ticket_location) ask('zone_matches_ticket_location', 'I checked that the zone matches the ticket location.', 'boolean')
  if (!a.receipt_details_confirmed) ask('receipt_details_confirmed', 'I checked these details against the receipt file.', 'boolean')
  if (need.length) return { ...base, status: 'needs_information', summary: 'We need the ParkNYC receipt details.', missing_information: need.map((q) => q.prompt), questions: need, sources: [SRC[1]] }
  const t = `${f.issue_date}T${f.issue_time}`
  const ok = norm(f.plate_number) === norm(a.session_plate_number) && (f.plate_state ?? '').toUpperCase() === (a.session_plate_state ?? '').toUpperCase() && a.session_start! <= t && t < a.session_end!
  if (!ok) return { ...base, status: 'no_supported_ground_identified', summary: 'The receipt details you entered do not match the ticket.', sources: [SRC[0], SRC[1], SRC[2]], next_steps: ['Re-check the plate, state and times against the receipt.'] }
  return {
    ...base, status: 'ready_for_draft', draft_available: true,
    summary: 'The ParkNYC session you entered covers the ticket time and plate.',
    findings: [{
      id: 'parknyc-session-covers-ticket', title: 'Paid ParkNYC session matches the ticket',
      explanation: 'The plate, state and time on the ticket fall inside the ParkNYC session you entered from your receipt.',
      supporting_fact_ids: ['confirmed_fields.plate_number', 'confirmed_fields.issue_date', 'confirmed_fields.issue_time', 'answers.session_start', 'answers.session_end', 'answers.session_zone'],
      source_ids: ['nyc-dof-code-38', 'nyc-dot-parknyc'],
      limitations: ['Based on details you typed from your receipt. Verify them against the original file.'],
      suggested_next_step: 'Prepare a draft and submit it yourself on the NYC DOF page.',
    }],
    sources: SRC, next_steps: ['Prepare the draft', 'Attach the ParkNYC receipt', 'Submit it yourself on the NYC DOF page'],
  }
}

function draftFor(c: CaseData): Draft {
  const f = c.confirmed_fields; const a = c.answers
  if (c.analysis?.draft_kind === 'factual') {
    return {
      text: `To ${f.issuing_authority}:\n\nI request a review of notice ${f.ticket_number}.\n\n${c.circumstances}`,
      attachments: [],
      submission_steps: [{ text: 'Confirm filing instructions with the issuing authority.', url: c.analysis.sources[0].url }],
      stale: false, updated_at: nowIso(),
    }
  }
  const ev = c.documents.find((d) => d.document_id === a.evidence_document_id)
  return {
    text: `To the NYC Department of Finance:\n\nI request a hearing to contest parking violation ${f.ticket_number} (code ${f.violation_code}). The ticket records ${f.issue_date} at ${f.issue_time} at ${f.location}, for plate ${f.plate_number} (${f.plate_state}).\n\nI paid through ParkNYC in zone ${a.session_zone}, session ${a.session_start?.replace('T', ' ')} to ${a.session_end?.replace('T', ' ')} local time. Please review the attached receipt.`,
    attachments: ev ? [{ document_id: ev.document_id, filename: ev.filename }] : [],
    submission_steps: [
      { text: 'Open the NYC DOF dispute page and choose a hearing method.', url: SRC[2].url },
      { text: 'Provide the ticket details and submit the draft and receipt yourself.', url: SRC[2].url },
    ],
    stale: false, updated_at: nowIso(),
  }
}

function demoExtraction(docId: string): Extraction {
  const f = (value: string | null, source_text: string | null): ExtractedField => ({ value, source_document_id: docId, page: value ? 1 : null, source_text, needs_confirmation: true })
  const v: Record<FieldKey, ExtractedField> = {
    jurisdiction_state: f(null, null), ticket_type: f(null, null),
    ticket_number: f('0000000038', 'Summons No. 0000000038'), issuing_authority: f('NYC Department of Finance', 'Department of Finance'),
    city: f('New York', null), violation_code: f('38', 'Viol Code 38'), violation_description: f(null, null),
    issue_date: f('2026-11-02', '11/02/2026'), issue_time: f('13:30', '1:30P'), location: f('100 Example Ave', 'Ex Ave'),
    amount: f('65.00', '$65.00'), plate_number: f('DEMO123', 'DEMO123'), plate_state: f('NY', 'NY'),
  }
  return { fields: v, warnings: ['Violation description could not be read.'] }
}

const emptyFields = () => Object.fromEntries(FIELD_KEYS.map((k) => [k, null])) as CaseData['confirmed_fields']
const emptyAnswers = (): Answers => ({ payment_method: null, evidence_document_id: null, session_start: null, session_end: null, session_plate_number: null, session_plate_state: null, session_zone: null, zone_matches_ticket_location: null, receipt_details_confirmed: null })

export const mockApi: Api = {
  async createCase(state) {
    await wait(200)
    const all = load(); const id = uuid(); const secret = btoa(uuid() + uuid()).replace(/[^A-Za-z0-9]/g, '').slice(0, 43)
    all[id] = { secret, data: { case_id: id, documents: [], extraction: null, confirmed_fields: { ...emptyFields(), jurisdiction_state: state }, circumstances: null, answers: emptyAnswers(), outcome: null, analysis: null, draft: null, offer: { price_cents: 1900, currency: 'USD', mode: 'demo', charge: false }, created_at: nowIso(), updated_at: nowIso() } }
    save(all); access.set(id, secret)
    return { case_id: id, access_secret: secret }
  },
  async getCase(id) { await wait(200); return structuredClone(open(id).c) },
  async uploadDocument(id, kind, file, onProgress) {
    const { all, c } = open(id)
    const limit = kind === 'ticket' ? 1 : 4
    if (c.documents.filter((d) => d.kind === kind).length >= limit) throw new ApiError('document_limit', 'This case already has the maximum number of files of that type.', 409)
    if (!['application/pdf', 'image/jpeg', 'image/png'].includes(file.type)) throw new ApiError('unsupported_media', 'That file type is not supported.', 415)
    for (let p = 0; p <= 100; p += 20) { onProgress?.(p); await wait(120) }
    const doc = { document_id: uuid(), kind, filename: `${kind}-${c.documents.length + 1}.${file.type === 'application/pdf' ? 'pdf' : file.type === 'image/png' ? 'png' : 'jpg'}`, media_type: file.type as 'application/pdf', size_bytes: file.size }
    c.documents.push(doc); c.analysis = null; if (c.draft) c.draft.stale = true
    commit(all, c); return doc
  },
  async extract(id) {
    await wait(1200); const { all, c } = open(id)
    if (c.extraction) return c.extraction
    const t = c.documents.find((d) => d.kind === 'ticket')
    if (!t) throw new ApiError('ticket_required', 'Upload a ticket before reading it.', 409)
    c.extraction = demoExtraction(t.document_id); commit(all, c); return c.extraction
  },
  async patchCase(id, p: PatchCase) {
    await wait(250); const { all, c } = open(id)
    const before = JSON.stringify([c.confirmed_fields, c.circumstances, c.answers])
    if (p.confirmed_fields) Object.assign(c.confirmed_fields, p.confirmed_fields)
    if (p.answers) Object.assign(c.answers, p.answers)
    if ('circumstances' in p) c.circumstances = p.circumstances ?? null
    if ('outcome' in p) c.outcome = p.outcome ?? null
    if (before !== JSON.stringify([c.confirmed_fields, c.circumstances, c.answers])) { c.analysis = null; if (c.draft) c.draft.stale = true }
    commit(all, c); return structuredClone(c)
  },
  async analyze(id) {
    await wait(900); const { all, c } = open(id)
    const a = evaluate(c); if (c.draft) c.draft.stale = true
    c.analysis = a; commit(all, c); return a
  },
  async createDraft(id) {
    await wait(700); const { all, c } = open(id)
    if (!c.analysis?.draft_available) throw new ApiError('draft_not_ready', 'Complete the case review before preparing a draft.', 409)
    if (c.draft && !c.draft.stale) return c.draft
    c.draft = draftFor(c); commit(all, c); return c.draft
  },
  async patchDraft(id, text) {
    await wait(300); const { all, c } = open(id)
    if (!c.draft || c.draft.stale) throw new ApiError('draft_not_ready', 'Prepare a current draft before continuing.', 409)
    c.draft.text = text; c.draft.updated_at = nowIso(); commit(all, c); return c.draft
  },
  async exportPdf(id) {
    await wait(500); const { c } = open(id)
    if (!c.draft || c.draft.stale) throw new ApiError('draft_not_ready', 'Prepare a current draft before continuing.', 409)
    return new Blob(['%PDF-1.1\n% mock export, not a real PDF\n'], { type: 'application/pdf' })
  },
  async deleteCase(id) { await wait(250); const { all } = open(id); delete all[id]; save(all); access.clear(id) },
}
