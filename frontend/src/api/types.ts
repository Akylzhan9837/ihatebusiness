// ПРЕДВАРИТЕЛЬНЫЕ типы. Источник истины — docs/api-contract.md; при его появлении сверить и поправить здесь.

export type FieldKey =
  | 'ticket_number' | 'issuing_authority' | 'city'
  | 'violation_code' | 'violation_description'
  | 'issue_date' | 'issue_time' | 'location'
  | 'fine_amount' | 'license_plate' | 'plate_state'

export type FieldQuality = 'ok' | 'low_confidence' | 'missing'

export interface ExtractedField {
  key: FieldKey
  value: string | null          // даты — 'YYYY-MM-DD', время — 'HH:mm', сумма — строка '65.00' (без UTC-конвертаций)
  quality: FieldQuality
  source_text?: string | null
  page?: number | null
}

export type AnalysisStatus =
  | 'unsupported' | 'needs_information' | 'no_supported_ground_identified' | 'ready_for_draft'

export interface OfficialSource { title: string; url: string; note?: string }

export interface Finding {
  id: string
  title: string
  explanation: string
  supporting_facts: string[]
  sources: OfficialSource[]
  limitations: string[]
}

export interface Question {
  id: string
  text: string
  kind: 'text' | 'choice' | 'evidence'
  options?: string[]
  required?: boolean
}

export interface Analysis {
  status: AnalysisStatus
  summary?: string
  verified: string[]
  missing_information: string[]
  findings: Finding[]
  sources: OfficialSource[]
  next_steps: string[]
  draft_available: boolean
  unsupported_reason?: string
}

export interface Draft {
  text: string
  attachments: string[]
  submission_url?: string
  deadline_note?: { text: string; source_url?: string } | null
  updated_at?: string
}

export interface CaseData {
  id: string
  fields: ExtractedField[]
  questions: Question[]
  answers: Record<string, string>
  analysis: Analysis | null
  draft: Draft | null
}

export interface CreatedCase { id: string; access_secret: string }

export interface AppConfig {
  allowed_types?: string[]       // напр. ['application/pdf','image/jpeg','image/png']
  max_file_bytes?: number
  sample_case_available?: boolean
}

export interface Api {
  getConfig(): Promise<AppConfig>
  createCase(): Promise<CreatedCase>
  uploadDocument(id: string, file: File): Promise<void>
  extract(id: string): Promise<CaseData>
  updateCase(id: string, patch: { fields?: Partial<Record<FieldKey, string | null>>; answers?: Record<string, string> }): Promise<CaseData>
  analyze(id: string): Promise<CaseData>
  createDraft(id: string): Promise<CaseData>
  updateDraft(id: string, text: string): Promise<CaseData>
  getCase(id: string): Promise<CaseData>
  exportPdf(id: string): Promise<Blob>
  deleteCase(id: string): Promise<void>
}
