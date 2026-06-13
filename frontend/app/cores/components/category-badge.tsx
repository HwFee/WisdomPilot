'use client'

import { cn } from '@/lib/utils'
import { CATEGORY_LABELS } from '../lib/core-utils'

interface CategoryBadgeProps {
  category: string
  type: 'earn' | 'spend'
}

export function CategoryBadge({ category, type }: CategoryBadgeProps) {
  const label = CATEGORY_LABELS[category] || category
  const isEarn = type === 'earn'

  return (
    <span
      className={cn(
        'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border',
        isEarn
          ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
          : 'bg-rose-50 text-rose-700 border-rose-200',
      )}
    >
      {label}
    </span>
  )
}
