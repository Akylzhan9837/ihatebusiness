export const MAX_FILE_BYTES = 8 * 1024 * 1024
export const ACCEPT_TYPES = ['application/pdf', 'image/jpeg', 'image/png']
export const ACCEPT_ATTR = 'application/pdf,image/jpeg,image/png'

/** Клиентская проверка — только удобство; сервер проверяет заново (тип, размер, страницы, мегапиксели). */
export function checkFile(f: File): string {
  if (!ACCEPT_TYPES.includes(f.type)) return 'Use a PDF, JPG or PNG file.'
  if (f.size > MAX_FILE_BYTES) return 'This file is larger than 8 MB. Choose a smaller file.'
  if (f.size === 0) return 'This file is empty.'
  return ''
}
