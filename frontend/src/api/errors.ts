export type ApiErrorKind =
  | 'network' | 'access_denied' | 'not_found' | 'invalid_file' | 'ai_unavailable'
  | 'validation' | 'unsupported' | 'unknown'

export class ApiError extends Error {
  constructor(
    public kind: ApiErrorKind,
    message: string,
    public status?: number,
    public fieldErrors?: Record<string, string>,
  ) { super(message) }
}

const TEXT: Record<ApiErrorKind, string> = {
  network: 'Could not reach the server. Check your connection and try again.',
  access_denied: 'Access denied. This case can only be opened from the browser or link that created it.',
  not_found: 'This case was not found. It may have been deleted.',
  invalid_file: 'This file cannot be used. Check the format and size, then try another file.',
  ai_unavailable: 'Automatic reading is temporarily unavailable. You can try again or enter details manually.',
  validation: 'Some details need attention.',
  unsupported: 'This ticket is outside what the demo supports.',
  unknown: 'Something went wrong. Please try again.',
}

export function userMessage(e: unknown): string {
  if (e instanceof ApiError) return e.message || TEXT[e.kind]
  return TEXT.unknown
}

// TODO(contract): подогнать под реальный формат ошибок backend ({code, message, fields}).
export async function fromResponse(res: Response): Promise<ApiError> {
  let body: any = null
  try { body = await res.json() } catch { /* не JSON */ }
  const msg: string | undefined = body?.message ?? body?.detail
  const fields = body?.fields as Record<string, string> | undefined
  const code: string | undefined = body?.code
  if (res.status === 401 || res.status === 403) return new ApiError('access_denied', TEXT.access_denied, res.status)
  if (res.status === 404 || res.status === 410) return new ApiError('not_found', TEXT.not_found, res.status)
  if (res.status === 413 || res.status === 415 || code === 'invalid_file') return new ApiError('invalid_file', msg ?? TEXT.invalid_file, res.status)
  if (res.status === 503 || code === 'ai_unavailable') return new ApiError('ai_unavailable', TEXT.ai_unavailable, res.status)
  if (res.status === 422 || res.status === 400) return new ApiError('validation', msg ?? TEXT.validation, res.status, fields)
  return new ApiError('unknown', msg ?? TEXT.unknown, res.status)
}
