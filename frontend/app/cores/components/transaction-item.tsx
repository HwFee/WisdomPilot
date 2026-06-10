import { Clock } from 'lucide-react'
import { formatDate, getCategoryColor, getCategoryName } from '../lib/cores-utils'
import type { CoreTransaction } from '../lib/cores-utils'

interface CoreTransactionItemProps {
  tx: CoreTransaction
}

export function CoreTransactionItem({ tx }: CoreTransactionItemProps) {
  return (
    <div className="p-4 hover:bg-muted/30 transition-colors">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={`px-2 py-0.5 rounded text-xs font-medium ${getCategoryColor(tx.category)}`}>
              {getCategoryName(tx.category)}
            </span>
          </div>
          {tx.description && (
            <p className="text-sm text-muted-foreground truncate">{tx.description}</p>
          )}
          <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
            <Clock className="size-3" />
            {formatDate(tx.created_at)}
          </div>
        </div>
        <div className="text-right flex-shrink-0">
          <div className={`text-lg font-bold ${tx.type === 'earn' ? 'text-green-500' : 'text-red-500'}`}>
            {tx.type === 'earn' ? '+' : '-'}{tx.amount}
          </div>
          <div className="text-xs text-muted-foreground">余额: {tx.balance_after}</div>
        </div>
      </div>
    </div>
  )
}
