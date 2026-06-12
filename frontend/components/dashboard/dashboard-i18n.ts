export type Language = 'zh' | 'en'

export function translate(zh: string, en: string, lang: Language): string {
  return lang === 'zh' ? zh : en
}
