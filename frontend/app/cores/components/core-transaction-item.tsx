'use client'

import { Plus, Minus } from 'lucide-react'
import { CategoryBadge } from './category-badge'
import { formatDateTime, formatNumber } from '../lib/core-utils'
import type { CoreTransaction } from '@/lib/api/core'

interface CoreTransactionItemProps {
  transaction: CoreTransaction
}

export function CoreTransactionItem({ transaction }: CoreTransactionItemProps) {
  const isEarn = transaction.type === 'earn'
  const Icon = isEarn ? Plus : Minus
  const amountPrefix = isEarn ? '+' : '-'

  return (
    <div className="flex items-center justify-between p-4 gap-4">
      <div className="flex items-center gap-3 min-w-0">
        <div
          className={[
            'size-10 rounded-lg flex items-center justify-center shrink-0 border',
            isEarn
              ? 'bg-emerald-50 border-emerald-200 text-emerald-700'
              : 'bg-rose-50 border-rose-200 text-rose-700',
          ].join(' ')}
        >
          <Icon className="size-5" strokeWidth={1.5} />
        </div>
        <div className="min-w-0">
          <p className="font-medium truncate">
            {transaction.description || transaction.category}
          </p>
          <div className="flex items-center gap-2 mt-1 flex-wrap">
            <CategoryBadge category={transaction.category} type={transaction.type} />
            <span className="text-xs text-muted-foreground">
              {formatDateTime(transaction.created_at)}
            </span>
          </div>
        </div>
      </div>

      <div className="text-right shrink-0">
        <p className={isEarn ? 'text-lg font-bold text-emerald-600' : 'text-lg font-bold text-rose-600'}>
          {amountPrefix}
          {formatNumber(transaction.amount)}
        </p>
        <p className="text-xs text-muted-foreground">
          余额 {formatNumber(transaction.balance_after)}
        </p>
      </div>
    </div>
  )
}
