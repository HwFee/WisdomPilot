import { CODE_LANGUAGE_TO_ID } from '@/lib/code-api'

export function getLanguageId(lang: string): number {
  const normalized = lang?.toLowerCase().trim() || 'python'
  return CODE_LANGUAGE_TO_ID[normalized] || 71
}
