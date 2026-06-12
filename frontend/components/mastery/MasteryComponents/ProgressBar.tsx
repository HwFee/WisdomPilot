'use client'

import { LazyMotion, domAnimation, m } from 'framer-motion'
import { getMasteryLevel } from './mastery-level'

// ========================================
// MasteryProgressBar - animated progress bar with level color
// ========================================

interface MasteryProgressBarProps {
  /** 掌握度 0-100 */
  score: number
  /** 是否显示百分比标签 */
  showLabel?: boolean
  /** 尺寸 */
  size?: 'sm' | 'md' | 'lg'
  /** 是否显示动画 */
  animated?: boolean
}

const HEIGHT_MAP = {
  sm: 'h-1.5',
  md: 'h-2.5',
  lg: 'h-4',
} as const

export function MasteryProgressBar({
  score,
  showLabel = true,
  size = 'md',
  animated = true,
}: MasteryProgressBarProps) {
  const normalizedScore = Math.min(100, Math.max(0, score))
  const { textColor, label, progressColor } = getMasteryLevel(normalizedScore)

  return (
    <LazyMotion features={domAnimation}>
      <div className="w-full">
        <div className={`w-full bg-gray-200 dark:bg-gray-700 rounded-full ${HEIGHT_MAP[size]} overflow-hidden`}>
          <m.div
            className={`${HEIGHT_MAP[size]} rounded-full ${progressColor}`}
            initial={animated ? { width: 0 } : { width: `${normalizedScore}%` }}
            animate={{ width: `${normalizedScore}%` }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
          />
        </div>
        {showLabel && (
          <div className="flex justify-between items-center mt-1">
            <span className={`text-xs font-medium ${textColor}`}>{label}</span>
            <span className="text-xs text-gray-500">{normalizedScore.toFixed(0)}%</span>
          </div>
        )}
      </div>
    </LazyMotion>
  )
}
