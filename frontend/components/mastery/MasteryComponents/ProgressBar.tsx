'use client'

import { LazyMotion, domAnimation, m } from 'framer-motion'

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

// ========================================
// getMasteryLevel - shared helper used by ProgressBar and all cards
// ========================================

export function getMasteryLevel(score: number) {
  if (score >= 95) {
    return {
      label: '精通',
      badgeColor: 'bg-green-100 dark:bg-green-900/30',
      textColor: 'text-green-700 dark:text-green-400',
      progressColor: 'bg-gradient-to-r from-green-500 to-emerald-400',
    }
  } else if (score >= 85) {
    return {
      label: '熟练',
      badgeColor: 'bg-blue-100 dark:bg-blue-900/30',
      textColor: 'text-blue-700 dark:text-blue-400',
      progressColor: 'bg-gradient-to-r from-blue-500 to-cyan-400',
    }
  } else if (score >= 70) {
    return {
      label: '练习',
      badgeColor: 'bg-yellow-100 dark:bg-yellow-900/30',
      textColor: 'text-yellow-700 dark:text-yellow-400',
      progressColor: 'bg-gradient-to-r from-yellow-500 to-amber-400',
    }
  } else if (score >= 50) {
    return {
      label: '学习',
      badgeColor: 'bg-orange-100 dark:bg-orange-900/30',
      textColor: 'text-orange-700 dark:text-orange-400',
      progressColor: 'bg-gradient-to-r from-orange-500 to-amber-400',
    }
  } else {
    return {
      label: '入门',
      badgeColor: 'bg-gray-100 dark:bg-gray-800',
      textColor: 'text-gray-600 dark:text-gray-400',
      progressColor: 'bg-gradient-to-r from-gray-400 to-gray-300',
    }
  }
}
