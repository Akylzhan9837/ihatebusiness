// Типы строго по docs/api-contract.md (v1).

export const FIELD_KEYS = [
  'jurisdiction_state', 'ticket_type', 'ticket_number', 'issuing_authority', 'city', 'violation_code', 'violation_description',
  'issue_date', 'issue_time', 'location', 'amount', 'plate_number', 'plate_state',
] as const
export type FieldKey = (typeof FIELD_KEYS)[number]

export type ConfirmedFields = Record<FieldKey, string | null>
export type DocumentKind = 'ticket' | 'evidence'

export interface DocumentInfo {
  document_id: string
  kind: DocumentKind
  filename: string
  media_type: 'application/pdf' | 'image/jpeg' | 'image/png'
  size_bytes: number
}

export interface ExtractedField {
  value: string | null
  source_document_id: string
  page: number | null
  source_text: string | null
  needs_confirmation: true
}
export interface Extraction {
  fields: Partial<Record<FieldKey, ExtractedField>>
  warnings: string[]
}

export type PaymentMethod = 'parknyc' | 'other' | 'none' | 'unknown'
export const ANSWER_KEYS = [
  'payment_method', 'evidence_document_id', 'session_start', 'session_end',
  'session_plate_number', 'session_plate_state', 'session_zone',
  'zone_matches_ticket_location', 'receipt_details_confirmed',
] as const
export type AnswerKey = (typeof ANSWER_KEYS)[number]
export interface Answers {
  payment_method: PaymentMethod | null
  evidence_document_id: string | null
  session_start: string | null
  session_end: string | null
  session_plate_number: string | null
  session_plate_state: string | null
  session_zone: string | null
  zone_matches_ticket_location: boolean | null
  receipt_details_confirmed: boolean | null
}
export type AnswerValue = string | boolean | null

export type Outcome = 'submitted' | 'dismissed' | 'upheld' | 'other'

export type AnalysisStatus = 'unsupported' | 'needs_information' | 'no_supported_ground_identified' | 'ready_for_draft'
export interface QuestionOption { value: string; label: string }
export interface Question {
  id: string
  prompt: string
  type: 'choice' | 'text' | 'datetime' | 'boolean' | 'evidence'
  options: QuestionOption[]
}
export interface Source {
  id: string; title: string; url: string; jurisdiction: string; topic: string
  accessed_at: string; relevant_excerpt: string
  kind?: 'instruction' | 'directory' | null
}
export interface Finding {
  id: string; title: string; explanation: string
  supporting_fact_ids: string[]; source_ids: string[]
  limitations: string[]; suggested_next_step: string
}
export interface Analysis {
  status: AnalysisStatus
  summary: string
  findings: Finding[]
  missing_information: string[]
  questions: Question[]
  next_steps: string[]
  sources: Source[]
  draft_available: boolean
  draft_kind?: "factual" | null
}

export interface Attachment { document_id: string; filename: string }
export interface SubmissionStep { text: string; url: string }
export interface Draft {
  text: string
  attachments: Attachment[]
  submission_steps: SubmissionStep[]
  stale: boolean
  updated_at: string
}
export interface Offer { price_cents: 1900; currency: 'USD'; mode: 'demo' | 'unavailable'; charge: false }

export interface CaseData {
  case_id: string
  documents: DocumentInfo[]
  extraction: Extraction | null
  confirmed_fields: ConfirmedFields
  circumstances: string | null
  answers: Answers
  outcome: Outcome | null
  analysis: Analysis | null
  draft: Draft | null
  offer: Offer
  created_at: string
  updated_at: string
}

export interface CreatedCase { case_id: string; access_secret: string }

export interface PatchCase {
  confirmed_fields?: Partial<Record<FieldKey, string | null>>
  circumstances?: string | null
  answers?: Partial<Answers>
  outcome?: Outcome | null
}

export interface Api {
  createCase(state: string): Promise<CreatedCase>
  getCase(id: string): Promise<CaseData>
  uploadDocument(id: string, kind: DocumentKind, file: File, onProgress?: (percent: number) => void): Promise<DocumentInfo>
  extract(id: string): Promise<Extraction>
  patchCase(id: string, patch: PatchCase): Promise<CaseData>
  analyze(id: string): Promise<Analysis>
  createDraft(id: string): Promise<Draft>
  patchDraft(id: string, text: string): Promise<Draft>
  exportPdf(id: string): Promise<Blob>
  deleteCase(id: string): Promise<void>
}
