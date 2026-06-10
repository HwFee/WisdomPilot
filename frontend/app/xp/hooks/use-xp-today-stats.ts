'use client'

import { useMemo } from 'react'
import { BEIJING_DAY_FORMATTER, normalizeDateStr } from '@/lib/formatters'
import type { XpTransaction } from '../lib/xp-utils'

export function useXpTodayStats(transactions: XpTransaction[]) {
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

    const todayLevelUps = todayTransactions.filter((t) => t.level_up).length

    return { todayEarned, todayLevelUps }
  }, [transactions])
}
