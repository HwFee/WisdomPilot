'use client'

/* 徽章图标：扁平 SVG 六边形 + lucide 中心图标（strokeWidth=1.5）
   视觉红线：无渐变 / 无模糊 / 无玻璃；颜色全部走设计令牌（currentColor + panel 填充） */

import type { BadgeTier } from '@/lib/api/deck/types'
import { BADGE_ICONS, DEFAULT_BADGE_ICON, TIER_TEXT_CLASS } from './badge-meta'

/** 六边形轮廓（viewBox 64×64，pathLength=100 供 stroke 描绘动画按百分比计算） */
const HEXAGON_PATH = 'M32 4 L56 18 L56 46 L32 60 L8 46 L8 18 Z'

export function BadgeIcon({
  id,
  tier,
  size = 40,
  locked = false,
  draw = false,
}: {
  id: string
  tier: BadgeTier
  size?: number
  /** 未解锁：整体降为 faint */
  locked?: boolean
  /** 解锁仪式：六边形 stroke 描绘入场（~600ms，reduced-motion 下静态呈现） */
  draw?: boolean
}) {
  const Icon = BADGE_ICONS[id] ?? DEFAULT_BADGE_ICON
  const colorClass = locked ? 'text-faint' : TIER_TEXT_CLASS[tier]
  const iconSize = Math.round(size * 0.375)

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      fill="none"
      aria-hidden="true"
      className={colorClass}
    >
      <path
        d={HEXAGON_PATH}
        pathLength={100}
        stroke="currentColor"
        strokeWidth={2.5}
        strokeLinejoin="round"
        fill="hsl(var(--panel))"
        className={draw ? 'badge-draw' : undefined}
      />
      <g transform={`translate(${32 - iconSize / 2} ${32 - iconSize / 2})`}>
        <Icon size={iconSize} strokeWidth={1.5} />
      </g>
    </svg>
  )
}
