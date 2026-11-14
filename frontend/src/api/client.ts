import { API_BASE_URL, USE_MOCK } from '@/config'
import { access } from './access'
import { ApiError, fromResponse } from './errors'
import type { Api, AppConfig, CaseData, CreatedCase } from './types'

// Единственное место, где используется fetch.
async function request<T>(path: string, init: RequestInit = {}, caseId?: string, raw = false): Promise<T> {
  const headers = new Headers(init.headers)
  if (caseId) {
    const secret = access.get(caseId)
    if (!secret) throw new ApiError('access_denied', 'No access to this case in this browser session.', 401)
    // TODO(contract): уточнить схему (Authorization: Bearer / X-Case-Secret). Никогда не query string.
    headers.set('Authorization', `Bearer ${secret}`)
  }
  if (init.body && !(init.body instanceof FormData)) headers.set('Content-Type', 'application/json')
  let res: Response
  try { res = await fetch(`${API_BASE_URL}${path}`, { ...init, headers }) }
  catch { throw new ApiError('network', '') }
  if (!res.ok) throw await fromResponse(res)
  if (raw) return (await res.blob()) as unknown as T
  if (res.status === 204) return undefined as T
  return (await res.json()) as T
}

const json = (b: unknown) => JSON.stringify(b)

const httpApi: Api = {
  getConfig: () => request<AppConfig>('/api/config'),
  async createCase() {
    const c = await request<CreatedCase>('/api/cases', { method: 'POST' })
    access.set(c.id, c.access_secret)
    return c
  },
  async uploadDocument(id, file) {
    const fd = new FormData(); fd.append('file', file)
    await request<void>(`/api/cases/${id}/documents`, { method: 'POST', body: fd }, id)
  },
  extract: (id) => request<CaseData>(`/api/cases/${id}/extract`, { method: 'POST' }, id),
  updateCase: (id, patch) => request<CaseData>(`/api/cases/${id}`, { method: 'PATCH', body: json(patch) }, id),
  analyze: (id) => request<CaseData>(`/api/cases/${id}/analyze`, { method: 'POST' }, id),
  createDraft: (id) => request<CaseData>(`/api/cases/${id}/draft`, { method: 'POST' }, id),
  updateDraft: (id, text) => request<CaseData>(`/api/cases/${id}/draft`, { method: 'PATCH', body: json({ text }) }, id),
  getCase: (id) => request<CaseData>(`/api/cases/${id}`, {}, id),
  exportPdf: (id) => request<Blob>(`/api/cases/${id}/export`, {}, id, true),
  async deleteCase(id) {
    await request<void>(`/api/cases/${id}`, { method: 'DELETE' }, id)
    access.clear(id)
  },
}

let cached: Api | null = null
export async function getApi(): Promise<Api> {
  if (cached) return cached
  if (USE_MOCK) cached = (await import('./mock')).mockApi   // в production эта ветка вырезается
  else cached = httpApi
  return cached
}
