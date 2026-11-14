// DEV-ONLY mock. Подключается только при import.meta.env.DEV && VITE_USE_MOCK=true.
// Не подменяет ошибки backend успешным результатом.
import { access } from './access'
import { ApiError } from './errors'
import type { Api, CaseData, ExtractedField } from './types'

const store = new Map<string, CaseData>()
const wait = (ms = 600) => new Promise((r) => setTimeout(r, ms))
const need = (id: string) => {
  const c = store.get(id)
  if (!c) throw new ApiError('not_found', '', 404)
  return c
}

const SAMPLE: ExtractedField[] = [
  { key: 'ticket_number', value: '0000000000', quality: 'ok', source_text: 'Summons No. 0000000000', page: 1 },
  { key: 'issuing_authority', value: 'NYC Department of Finance', quality: 'ok', source_text: 'Department of Finance', page: 1 },
  { key: 'city', value: 'New York', quality: 'ok', source_text: null, page: 1 },
  { key: 'violation_code', value: '14', quality: 'low_confidence', source_text: 'Viol Code: 14', page: 1 },
  { key: 'violation_description', value: null, quality: 'missing', source_text: null, page: null },
  { key: 'issue_date', value: '2026-03-04', quality: 'ok', source_text: '03/04/2026', page: 1 },
  { key: 'issue_time', value: '09:15', quality: 'ok', source_text: '09:15A', page: 1 },
  { key: 'location', value: 'Example St near 1st Ave', quality: 'low_confidence', source_text: 'Ex St / 1 Av', page: 1 },
  { key: 'fine_amount', value: '115.00', quality: 'ok', source_text: '$115.00', page: 1 },
  { key: 'license_plate', value: 'ABC1234', quality: 'ok', source_text: 'ABC1234', page: 1 },
  { key: 'plate_state', value: 'NY', quality: 'ok', source_text: 'NY', page: 1 },
]

export const mockApi: Api = {
  async getConfig() { return { allowed_types: ['application/pdf', 'image/jpeg', 'image/png'], max_file_bytes: 10 * 1024 * 1024 } },
  async createCase() {
    await wait(200)
    const id = crypto.randomUUID(); const secret = crypto.randomUUID()
    store.set(id, { id, fields: [], questions: [], answers: {}, analysis: null, draft: null })
    access.set(id, secret)
    return { id, access_secret: secret }
  },
  async uploadDocument(id) { await wait(); need(id) },
  async extract(id) { await wait(1200); const c = need(id); c.fields = structuredClone(SAMPLE); return structuredClone(c) },
  async updateCase(id, patch) {
    await wait(300); const c = need(id)
    for (const f of c.fields) {
      const v = patch.fields?.[f.key]
      if (v !== undefined) { f.value = v; f.quality = v ? 'ok' : 'missing' }
    }
    Object.assign(c.answers, patch.answers ?? {})
    return structuredClone(c)
  },
  async analyze() { throw new ApiError('unknown', 'Mock: analyze is not implemented yet.') },
  async createDraft() { throw new ApiError('unknown', 'Mock: draft is not implemented yet.') },
  async updateDraft() { throw new ApiError('unknown', 'Mock: draft is not implemented yet.') },
  async getCase(id) { await wait(200); return structuredClone(need(id)) },
  async exportPdf() { throw new ApiError('unknown', 'Mock: PDF export is not implemented.') },
  async deleteCase(id) { await wait(300); need(id); store.delete(id); access.clear(id) },
}
