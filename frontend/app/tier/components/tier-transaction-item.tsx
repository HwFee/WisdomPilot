'use client'

import { Star, ArrowUp, ArrowDown, Shield } from 'lucide-react'
import { getFullTierName, TIER_SOURCE_LABELS, formatDateTime, formatNumber } from '../lib/tier-utils'
import type { TierTransaction } from '@/lib/api/tier'

interface TierTransactionItemProps {
  transaction: TierTransaction
}

export function TierTransactionItem({ transaction }: TierTransactionItemProps) {
  const isGain = transaction.stars_change >= 0
  const Icon = transaction.promoted
    ? ArrowUp
    : transaction.demoted
      ? ArrowDown
      : isGain
        ? Star
        : Shield
  const afterFullName = getFullTierName(transaction.tier_after, transaction.sub_tier_after)

  const badgeClass = transaction.promoted
    ? 'bg-amber-50 text-amber-700 border-amber-200'
    : transaction.demoted
      ? 'bg-red-50 text-red-700 border-red-200'
      : transaction.used_protection
        ? 'bg-blue-50 text-blue-700 border-blue-200'
        : isGain
          ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
          : 'bg-rose-50 text-rose-700 border-rose-200'

  const sourceLabel = TIER_SOURCE_LABELS[transaction.source] || transaction.source

  return (
    <div className="flex items-center justify-between p-4 gap-4">
      <div className="flex items-center gap-3 min-w-0">
        <div className={`size-10 rounded-lg flex items-center justify-center shrink-0 border ${badgeClass}`}>
          <Icon className="size-5" strokeWidth={1.5} />
        </div>
        <div className="min-w-0">
          <p className="font-medium truncate">
            {transaction.description || `${sourceLabel} · ${afterFullName}`}
          </p>
          <div className="flex items-center gap-2 mt-1 flex-wrap">
            <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${badgeClass}`}>
              {transaction.promoted ? '晋级' : transaction.demoted ? '降级' : transaction.used_protection ? '保护' : isGain ? '加星' : '扣星'}
            </span>
            <span className="text-xs text-muted-foreground">
              {formatDateTime(transaction.created_at)}
            </span>
          </div>
        </div>
      </div>

      <div className="text-right shrink-0">
        <p className={isGain ? 'text-lg font-bold text-emerald-600' : 'text-lg font-bold text-rose-600'}>
          {isGain ? '+' : ''}
          {formatNumber(transaction.stars_change)} 星
        </p>
        <p className="text-xs text-muted-foreground">
          {getFullTierName(transaction.tier_before, transaction.sub_tier_before)} → {afterFullName}
        </p>
      </div>
    </div>
  )
}
