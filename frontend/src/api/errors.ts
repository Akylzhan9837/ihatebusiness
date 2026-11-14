// Формат ошибок backend: {"error":{"code","message","retryable"}}.
// Локальные коды: 'network' (нет ответа), 'no_access' (в этой вкладке нет ключа).

export class ApiError extends Error {
  constructor(
    public code: string,
    message: string,
    public status: number,
    public retryable = false,
  ) { super(message) }
}

const BY_STATUS: Record<number, string> = {
  404: 'This case could not be opened. Check your private link.',
  409: 'That step is not available yet. Complete the previous step and try again.',
  413: 'That file is too large. The limit is 8 MB per file.',
  415: 'That file type is not supported. Use a PDF, JPG or PNG file.',
  422: 'Some details are invalid. Check the highlighted fields and try again.',
  429: 'Ticket reading is busy right now. Try again in a moment.',
  503: 'This part of the service is temporarily unavailable. Try again shortly.',
}

export function networkError() {
  return new ApiError('network', 'Could not reach the server. Check your connection and try again.', 0, true)
}
export function noAccessError() {
  return new ApiError('no_access', 'This case can only be opened with its private link.', 404)
}

export function fromBody(status: number, body: unknown): ApiError {
  const e = (body as { error?: { code?: unknown; message?: unknown; retryable?: unknown } } | null)?.error
  const code = typeof e?.code === 'string' ? e.code : 'request_failed'
  // 422: backend не отражает ввод, но текст всё равно берём из нашего словаря.
  const message = status === 422
    ? BY_STATUS[422]
    : typeof e?.message === 'string' && e.message ? e.message : (BY_STATUS[status] ?? 'Something went wrong. Please try again.')
  return new ApiError(code, message, status, e?.retryable === true)
}

export const isNotFound = (e: unknown) => e instanceof ApiError && e.status === 404
export const isRetryable = (e: unknown) => e instanceof ApiError && e.retryable

export function userMessage(e: unknown): string {
  return e instanceof ApiError ? e.message : 'Something went wrong. Please try again.'
}
