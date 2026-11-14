// Секрет доступа к делу. Живёт только в sessionStorage вкладки (с запасным вариантом в памяти).
// Никогда не попадает в query, аналитику, логи; на сервер уходит только заголовком Authorization.
// Повторное открытие: ссылка /case/{id}#key={secret}. Фрагмент не отправляется на сервер;
// мы читаем его один раз и сразу убираем из адресной строки через history.replaceState.

const memory = new Map<string, string>()
const key = (id: string) => `tc:access:${id}`

export const access = {
  set(id: string, secret: string) {
    memory.set(id, secret)
    try { sessionStorage.setItem(key(id), secret) } catch { /* private mode */ }
  },
  get(id: string): string | null {
    try { const v = sessionStorage.getItem(key(id)); if (v) return v } catch { /* noop */ }
    return memory.get(id) ?? null
  },
  clear(id: string) {
    memory.delete(id)
    try { sessionStorage.removeItem(key(id)) } catch { /* noop */ }
  },
}

/** Ссылка для повторного открытия. Вызывать только по явному действию пользователя (копирование). */
export function privateLink(id: string): string | null {
  const secret = access.get(id)
  return secret ? `${window.location.origin}/case/${id}#key=${secret}` : null
}

/** Читает #key= из адреса, сохраняет и убирает фрагмент. Возвращает true, если ключ принят. */
export function consumeKeyFromLocation(): boolean {
  const path = /^\/case\/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})(?:\/|$)/i.exec(window.location.pathname)
  const hash = /^#key=([A-Za-z0-9_-]{16,128})$/.exec(window.location.hash)
  if (!path || !hash) return false
  access.set(path[1].toLowerCase(), hash[1])
  window.history.replaceState(window.history.state, '', window.location.pathname + window.location.search)
  return true
}
