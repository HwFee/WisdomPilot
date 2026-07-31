import type { DefectType } from '@/lib/api/deck/types'

export interface DefectMeta {
  type: DefectType
  label: string
  /** 一句话解释：什么样、怎么判断（图例面板展示） */
  description: string
  /** Tailwind 色class：文字/边框共用 */
  textClass: string
  dotClass: string
}

export const DEFECT_TYPES: DefectMeta[] = [
  {
    type: 'logic',
    label: '逻辑错误',
    description: '代码能跑但结果不对——条件写反、计算错误、用错变量',
    textClass: 'text-signal',
    dotClass: 'bg-signal',
  },
  {
    type: 'boundary',
    label: '边界遗漏',
    description: '没处理特殊情况——空输入、越界、首尾元素、除零',
    textClass: 'text-amber',
    dotClass: 'bg-amber',
  },
  {
    type: 'performance',
    label: '性能陷阱',
    description: '功能对但慢——循环里重复计算、不必要的拷贝、该缓存没缓存',
    textClass: 'text-deck-red',
    dotClass: 'bg-deck-red',
  },
  {
    type: 'style',
    label: '风格问题',
    description: '不影响正确性但难读难维护——命名含糊、重复代码、格式混乱',
    textClass: 'text-dim',
    dotClass: 'bg-dim',
  },
  {
    type: 'security',
    label: '安全风险',
    description: '可能被恶意输入利用——注入、敏感信息泄露、未校验的外部输入',
    textClass: 'text-purple-400',
    dotClass: 'bg-purple-400',
  },
]

export function defectMeta(type: DefectType): DefectMeta {
  return DEFECT_TYPES.find((d) => d.type === type) ?? DEFECT_TYPES[0]
}
