/* 徽章 UI 元数据：图标映射 + tier 视觉令牌（跨模块共享，故下沉 deck）
   徽章业务定义以后端 / mock badges.ts 为准，这里只放呈现层映射 */

import type { LucideIcon } from 'lucide-react'
import {
  Award,
  CalendarCheck,
  Compass,
  Crosshair,
  Crown,
  FileSearch,
  Flame,
  GraduationCap,
  HeartPulse,
  Layers,
  Medal,
  Moon,
  Mountain,
  Sparkles,
  Star,
  Swords,
  Target,
  Trophy,
} from 'lucide-react'
import type { BadgeTier } from '@/lib/api/deck/types'

/** badge id → lucide 中心图标 */
export const BADGE_ICONS: Record<string, LucideIcon> = {
  'placement-done': Compass,
  'first-cert': Award,
  'review-first': FileSearch,
  'arena-first-win': Trophy,
  'feynman-first': GraduationCap,
  'streak-3': Flame,
  'night-owl': Moon,
  'cert-adept': Star,
  'cert-multi-topic': Layers,
  'review-perfect': Crosshair,
  'arena-streak-3': Swords,
  'feynman-star': Sparkles,
  'streak-7': CalendarCheck,
  'perfect-score': Target,
  'cert-master': Crown,
  'topic-ascend': Mountain,
  comeback: HeartPulse,
}

export const DEFAULT_BADGE_ICON = Medal

/** 隐藏（彩蛋）徽章 id：解锁仪式里先 ??? 后解码 */
export const HIDDEN_BADGE_IDS: ReadonlySet<string> = new Set([
  'night-owl',
  'perfect-score',
  'comeback',
])

/** tier → 文本色 class（驱动 SVG currentColor）：铜 amber / 银 line-bright / 金 signal */
export const TIER_TEXT_CLASS: Record<BadgeTier, string> = {
  bronze: 'text-amber',
  silver: 'text-line-bright',
  gold: 'text-signal',
}

/** tier → 完整颜色值（供 CSS 自定义属性 --badge-color 用，如边框脉冲、粒子） */
export const TIER_COLOR: Record<BadgeTier, string> = {
  bronze: 'hsl(var(--amber))',
  silver: 'hsl(var(--line-bright))',
  gold: 'hsl(var(--signal))',
}

/** tier → 分组标签 */
export const TIER_LABEL: Record<BadgeTier, string> = {
  bronze: '铜 · BRONZE',
  silver: '银 · SILVER',
  gold: '金 · GOLD',
}

export const TIER_ORDER: BadgeTier[] = ['bronze', 'silver', 'gold']
