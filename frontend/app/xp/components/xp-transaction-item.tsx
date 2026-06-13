'use client'

import { Sparkles } from 'lucide-react'
import { XP_CATEGORY_LABELS, formatDateTime, formatNumber } from '../lib/xp-utils'
import type { XpTransaction } from '@/lib/api/xp'

interface XpTransactionItemProps {
  transaction: XpTransaction
}

export function XpTransactionItem({ transaction }: XpTransactionItemProps) {
  const categoryLabel = XP_CATEGORY_LABELS[transaction.category] || transaction.category

  return (
    <div className="flex items-center justify-between p-4 gap-4">
      <div className="flex items-center gap-3 min-w-0">
        <div className="size-10 rounded-lg flex items-center justify-center shrink-0 border bg-primary/10 border-primary/20 text-primary">
          <Sparkles className="size-5" strokeWidth={1.5} />
        </div>
        <div className="min-w-0">
          <p className="font-medium truncate">
            {transaction.description || categoryLabel}
          </p>
          <div className="flex items-center gap-2 mt-1 flex-wrap">
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border bg-blue-50 text-blue-700 border-blue-200">
              {categoryLabel}
            </span>
            <span className="text-xs text-muted-foreground">
              {formatDateTime(transaction.created_at)}
            </span>
          </div>
        </div>
      </div>

      <div className="text-right shrink-0">
        <p className="text-lg font-bold text-emerald-600">
          +{formatNumber(transaction.amount)}
        </p>
        <p className="text-xs text-muted-foreground">
          经验 {formatNumber(transaction.balance_after)}
        </p>
        {transaction.level_up && (
          <p className="text-xs text-primary font-medium mt-0.5">
            {transaction.level_before} → {transaction.level_after}
          </p>
        )}
      </div>
    </div>
  )
}
