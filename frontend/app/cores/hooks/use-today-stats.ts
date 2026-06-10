'use client'

import { useMemo } from 'react'
import { BEIJING_DAY_FORMATTER } from '@/lib/formatters'
import { normalizeDateStr } from '../lib/cores-utils'
import type { CoreTransaction } from '../lib/cores-utils'

export function useTodayStats(transactions: CoreTransaction[]) {
  return useMemo(() => {
    const today = new Date()

    const todayTransactions = transactions.filter((t) => {
      const normalized = normalizeDateStr(t.created_at)
      const date = new Date(normalized)
      return (
        BEIJING_DAY_FORMATTER.format(date) === BEIJING_DAY_FORMATTER.format(today)
      )
    })

    const todayEarned = todayTransactions
      .filter((t) => t.type === 'earn')
      .reduce((sum, t) => sum + t.amount, 0)

    const todaySpent = todayTransactions
      .filter((t) => t.type === 'spend')
      .reduce((sum, t) => sum + t.amount, 0)

    return { todayEarned, todaySpent }
  }, [transactions])
}
