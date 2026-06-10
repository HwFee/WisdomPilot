'use client'

import { useMemo } from 'react'
import { BEIJING_DAY_FORMATTER, normalizeDateStr } from '@/lib/formatters'
import type { TierTransaction } from '../lib/tier-utils'

export function useTierTodayStats(transactions: TierTransaction[]) {
  return useMemo(() => {
    const today = new Date()

    const todayTransactions = transactions.filter((t) => {
      const normalized = normalizeDateStr(t.created_at)
      const date = new Date(normalized)
      return (
        BEIJING_DAY_FORMATTER.format(date) === BEIJING_DAY_FORMATTER.format(today)
      )
    })

    const todayStarsGained = todayTransactions
      .filter((t) => t.stars_change > 0)
      .reduce((sum, t) => sum + t.stars_change, 0)

    const todayStarsLost = todayTransactions
      .filter((t) => t.stars_change < 0)
      .reduce((sum, t) => sum + Math.abs(t.stars_change), 0)

    const todayPromotions = todayTransactions.filter((t) => t.promoted).length
    const todayDemotions = todayTransactions.filter((t) => t.demoted).length

    return { todayStarsGained, todayStarsLost, todayPromotions, todayDemotions }
  }, [transactions])
}
