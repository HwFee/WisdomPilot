export function translate(lang: 'zh' | 'en', zh: string, en: string): string {
  return lang === 'zh' ? zh : en
}
