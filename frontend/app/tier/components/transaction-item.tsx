import { Clock, PartyPopper, TrendingUp, TrendingDown, Shield, Star } from 'lucide-react'
import { formatDate } from '@/lib/formatters'
import { getTierDisplay, TIER_COLORS } from '../lib/tier-utils'
import type { TierTransaction } from '../lib/tier-utils'

interface TierTransactionItemProps {
  tx: TierTransaction
}

export function TierTransactionItem({ tx }: TierTransactionItemProps) {
  return (
    <div className="p-4 hover:bg-muted/30 transition-colors">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            {tx.promoted && (
              <span className="px-2 py-0.5 rounded text-xs font-medium text-green-600 bg-green-100 flex items-center gap-1">
                <PartyPopper className="size-3" />
                晋级
              </span>
            )}
            {tx.demoted && (
              <span className="px-2 py-0.5 rounded text-xs font-medium text-red-600 bg-red-100 flex items-center gap-1">
                <TrendingDown className="size-3" />
                降级
              </span>
            )}
            {tx.used_protection && (
              <span className="px-2 py-0.5 rounded text-xs font-medium text-blue-600 bg-blue-100 flex items-center gap-1">
                <Shield className="size-3" />
                段位保护
              </span>
            )}
            {!tx.promoted && !tx.demoted && !tx.used_protection && (
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${TIER_COLORS[tx.tier_after] || 'text-gray-600 bg-gray-100'}`}>
                {getTierDisplay(tx.tier_after, tx.sub_tier_after)}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2 text-sm">
            <span className={`${TIER_COLORS[tx.tier_before] || 'text-gray-600'} flex items-center gap-0.5`}>
              {getTierDisplay(tx.tier_before, tx.sub_tier_before)} <Star className="size-3.5 fill-current" />{tx.stars_before}
            </span>
            <span className="text-muted-foreground">→</span>
            <span className={`${TIER_COLORS[tx.tier_after] || 'text-gray-600'} flex items-center gap-0.5`}>
              {getTierDisplay(tx.tier_after, tx.sub_tier_after)} <Star className="size-3.5 fill-current" />{tx.stars_after}
            </span>
          </div>
          {tx.description && (
            <p className="text-sm text-muted-foreground mt-1">{tx.description}</p>
          )}
          <div className="flex items-center gap-2 mt-2 text-xs text-muted-foreground">
            <Clock className="size-3" />
            {formatDate(tx.created_at)}
          </div>
        </div>
        <div className="text-right flex-shrink-0">
          <div className={`text-lg font-bold flex items-center gap-1 ${tx.stars_change > 0 ? 'text-green-500' : 'text-red-500'}`}>
            {tx.stars_change > 0 ? (
              <><TrendingUp className="size-4" />+{tx.stars_change}</>
            ) : (
              <><TrendingDown className="size-4" />{tx.stars_change}</>
            )}
            <Star className="size-4 fill-current" />
          </div>
        </div>
      </div>
    </div>
  )
}
