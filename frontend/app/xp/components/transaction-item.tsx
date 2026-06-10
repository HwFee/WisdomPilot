import { Clock, PartyPopper } from 'lucide-react'
import { formatDate } from '@/lib/formatters'
import { getCategoryName, getCategoryColor, getLevelColor } from '../lib/xp-utils'
import type { XpTransaction } from '../lib/xp-utils'

interface XpTransactionItemProps {
  tx: XpTransaction
}

export function XpTransactionItem({ tx }: XpTransactionItemProps) {
  return (
    <div className="p-4 hover:bg-muted/30 transition-colors">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            {tx.level_up && (
              <span className="px-2 py-0.5 rounded text-xs font-medium text-amber-600 bg-amber-100 flex items-center gap-1">
                <PartyPopper className="size-3" />
                升级
              </span>
            )}
            <span className={`px-2 py-0.5 rounded text-xs font-medium ${getCategoryColor(tx.category)}`}>
              {getCategoryName(tx.category)}
            </span>
          </div>
          {tx.level_before !== tx.level_after && (
            <div className="flex items-center gap-2 text-sm mb-1">
              <span className={`px-2 py-0.5 rounded text-xs ${getLevelColor(tx.level_before)}`}>
                {tx.level_before}
              </span>
              <span className="text-muted-foreground">→</span>
              <span className={`px-2 py-0.5 rounded text-xs ${getLevelColor(tx.level_after)}`}>
                {tx.level_after}
              </span>
            </div>
          )}
          {tx.description && (
            <p className="text-sm text-muted-foreground truncate">{tx.description}</p>
          )}
          <div className="flex items-center gap-2 mt-2 text-xs text-muted-foreground">
            <Clock className="size-3" />
            {formatDate(tx.created_at)}
          </div>
        </div>
        <div className="text-right flex-shrink-0">
          <div className="text-lg font-bold text-green-500 flex items-center gap-1">
            +{tx.amount}
          </div>
          <div className="text-xs text-muted-foreground">累计: {tx.balance_after}</div>
        </div>
      </div>
    </div>
  )
}
