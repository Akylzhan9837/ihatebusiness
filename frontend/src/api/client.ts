import { API_BASE_URL, USE_MOCK } from '@/config'
import { access } from './access'
import { ApiError, fromBody, networkError, noAccessError } from './errors'
import type { Api, Analysis, CaseData, CreatedCase, Draft, DocumentInfo, Extraction } from './types'

// Единственное место с fetch/XHR. Ключ идёт только в заголовке Authorization: Bearer.
function authHeaders(caseId?: string): Headers {
  const headers = new Headers()
  if (caseId) {
    const secret = access.get(caseId)
    if (!secret) throw noAccessError()
    headers.set('Authorization', `Bearer ${secret}`)
  }
  return headers
}

async function request<T>(path: string, init: { method?: string; body?: unknown } = {}, caseId?: string): Promise<T> {
  const headers = authHeaders(caseId)
  let body: BodyInit | undefined
  if (init.body !== undefined) { headers.set('Content-Type', 'application/json'); body = JSON.stringify(init.body) }
  let res: Response
  try { res = await fetch(`${API_BASE_URL}${path}`, { method: init.method ?? 'GET', headers, body, cache: 'no-store', credentials: 'omit' }) }
  catch { throw networkError() }
  if (!res.ok) {
    let payload: unknown = null
    try { payload = await res.json() } catch { /* не JSON */ }
    throw fromBody(res.status, payload)
  }
  if (res.status === 204) return undefined as T
  return (await res.json()) as T
}

function upload(id: string, kind: string, file: File, onProgress?: (p: number) => void): Promise<DocumentInfo> {
  return new Promise((resolve, reject) => {
    let headers: Headers
    try { headers = authHeaders(id) } catch (e) { reject(e); return }
    const xhr = new XMLHttpRequest()
    xhr.open('POST', `${API_BASE_URL}/api/cases/${id}/documents`)
    headers.forEach((v, k) => xhr.setRequestHeader(k, v))
    xhr.responseType = 'json'
    xhr.upload.onprogress = (e) => { if (e.lengthComputable) onProgress?.(Math.round((e.loaded / e.total) * 100)) }
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) { onProgress?.(100); resolve(xhr.response as DocumentInfo) }
      else reject(fromBody(xhr.status, xhr.response))
    }
    xhr.onerror = () => reject(networkError())
    xhr.onabort = () => reject(networkError())
    const fd = new FormData()
    fd.append('kind', kind)
    fd.append('file', file)
    xhr.send(fd)
  })
}

const httpApi: Api = {
  async createCase(state) {
    const c = await request<CreatedCase>('/api/cases', { method: 'POST', body: { synthetic_only: true, jurisdiction_state: state } })
    access.set(c.case_id, c.access_secret)
    return c
  },
  getCase: (id) => request<CaseData>(`/api/cases/${id}`, {}, id),
  uploadDocument: (id, kind, file, onProgress) => upload(id, kind, file, onProgress),
  extract: (id) => request<Extraction>(`/api/cases/${id}/extract`, { method: 'POST' }, id),
  patchCase: (id, patch) => request<CaseData>(`/api/cases/${id}`, { method: 'PATCH', body: patch }, id),
  analyze: (id) => request<Analysis>(`/api/cases/${id}/analyze`, { method: 'POST' }, id),
  createDraft: (id) => request<Draft>(`/api/cases/${id}/draft`, { method: 'POST', body: { demo_access: true } }, id),
  patchDraft: (id, text) => request<Draft>(`/api/cases/${id}/draft`, { method: 'PATCH', body: { text } }, id),
  async exportPdf(id) {
    let res: Response
    try { res = await fetch(`${API_BASE_URL}/api/cases/${id}/export`, { headers: authHeaders(id), cache: 'no-store', credentials: 'omit' }) }
    catch { throw networkError() }
    if (!res.ok) {
      let payload: unknown = null
      try { payload = await res.json() } catch { /* не JSON */ }
      throw fromBody(res.status, payload)
    }
    return await res.blob()
  },
  async deleteCase(id) {
    await request<void>(`/api/cases/${id}`, { method: 'DELETE' }, id)
    access.clear(id)
  },
}

let cached: Api | null = null
export async function getApi(): Promise<Api> {
  if (cached) return cached
  // USE_MOCK == false в production → ветка и модуль mock вырезаются из сборки.
  cached = USE_MOCK ? (await import('./mock')).mockApi : httpApi
  return cached
}

export { ApiError }
