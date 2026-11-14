/** Плавно прокручивает страницу к секции с данным id с учётом липкой шапки. */
export function scrollToSection(id: string): void {
  const el = document.getElementById(id)
  if (!el) return
  const nav = document.querySelector<HTMLElement>('.nav')
  const offset = (nav?.offsetHeight ?? 0) + 8
  const top = el.getBoundingClientRect().top + window.scrollY - offset
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  window.scrollTo({ top: Math.max(0, top), behavior: reduce ? 'auto' : 'smooth' })
  // Сохраняем history.state роутера, меняем только якорь.
  history.replaceState(history.state, '', `#${id}`)
}
