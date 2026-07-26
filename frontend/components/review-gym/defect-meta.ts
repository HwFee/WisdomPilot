import type { DefectType } from '@/lib/api/deck/types'

export interface DefectMeta {
  type: DefectType
  label: string
  /** Tailwind 色class：文字/边框共用 */
  textClass: string
  dotClass: string
}

export const DEFECT_TYPES: DefectMeta[] = [
  { type: 'logic', label: '逻辑错误', textClass: 'text-signal', dotClass: 'bg-signal' },
  { type: 'boundary', label: '边界遗漏', textClass: 'text-amber', dotClass: 'bg-amber' },
  { type: 'performance', label: '性能陷阱', textClass: 'text-deck-red', dotClass: 'bg-deck-red' },
  { type: 'style', label: '坏味道', textClass: 'text-dim', dotClass: 'bg-dim' },
  { type: 'security', label: '安全风险', textClass: 'text-purple-400', dotClass: 'bg-purple-400' },
]

export function defectMeta(type: DefectType): DefectMeta {
  return DEFECT_TYPES.find((d) => d.type === type) ?? DEFECT_TYPES[0]
}
