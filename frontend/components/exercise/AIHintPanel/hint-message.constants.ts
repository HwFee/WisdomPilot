import { Lightbulb, Sparkles, BookOpen } from 'lucide-react'

/**
 * 提示级别与对应的展示样式 / 成本配置。
 *
 * 该模块与 HintMessage 组件解耦，便于在气泡、历史记录、
 * 配置面板等多处复用同一份配置。保持纯数据 + 类型，不依赖 React。
 */

export type HintLevel = 'light' | 'medium' | 'deep'

export interface HintLevelConfig {
  icon: typeof Lightbulb
  label: string
  description: string
  cost: number
  color: string
  bgColor: string
  borderColor: string
  hoverColor: string
}

export const HINT_CONFIG: Record<HintLevel, HintLevelConfig> = {
  light: {
    icon: Lightbulb,
    label: '轻度提示',
    description: '思路方向',
    cost: 1,
    color: 'text-yellow-500',
    bgColor: 'bg-yellow-500/10',
    borderColor: 'border-yellow-500/30',
    hoverColor: 'hover:bg-yellow-500/20',
  },
  medium: {
    icon: Sparkles,
    label: '中度提示',
    description: '关键步骤',
    cost: 3,
    color: 'text-purple-500',
    bgColor: 'bg-purple-500/10',
    borderColor: 'border-purple-500/30',
    hoverColor: 'hover:bg-purple-500/20',
  },
  deep: {
    icon: BookOpen,
    label: '深度解析',
    description: '完整解答',
    cost: 5,
    color: 'text-blue-600',
    bgColor: 'bg-blue-500/10',
    borderColor: 'border-blue-500/30',
    hoverColor: 'hover:bg-blue-500/20',
  },
}
