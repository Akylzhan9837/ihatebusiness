// Секрет доступа к делу. Хранится ТОЛЬКО в sessionStorage (живёт до закрытия вкладки),
// не попадает в URL, логи и аналитику. Документы и ПДн в хранилище браузера не кладём.
// TODO(согласовать с backend): способ восстановления доступа после закрытия вкладки
// (например, одноразовая ссылка с секретом во фрагменте #, который не уходит на сервер).
const key = (id: string) => `tc:access:${id}`

export const access = {
  set(id: string, secret: string) { try { sessionStorage.setItem(key(id), secret) } catch { /* private mode */ } },
  get(id: string): string | null { try { return sessionStorage.getItem(key(id)) } catch { return null } },
  clear(id: string) { try { sessionStorage.removeItem(key(id)) } catch { /* noop */ } },
}
