'use client'

import { useEffect, useState, useRef, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { getStoredToken, logout } from '@/lib/api'
import {
  getCoreBalance,
  getDailyCoreSummary,
  getCoreTransactions,
  type CoreTransaction,
} from '@/lib/api/core'
import { TransactionList } from '@/components/transactions/transaction-list'
import type { TransactionFilterOption } from '@/components/transactions/transaction-list'

export type CoreFilterType = 'all' | 'earn' | 'spend'

const PAGE_SIZE = 20

const FILTER_OPTIONS: TransactionFilterOption[] = [
  { value: 'all', label: '全部' },
  { value: 'earn', label: '收入' },
  { value: 'spend', label: '支出' },
]

interface CoreDataState {
  balance: { balance: number; total_earned: number; total_spent: number } | null
  summary: { earned_today: number; spent_today: number } | null
  transactions: CoreTransaction[]
  filter: CoreFilterType
  isLoading: boolean
  isLoadingMore: boolean
  error: string | null
  hasMore: boolean
}

export function useCoreData() {
  const { push } = useRouter()
  const [state, setState] = useState<CoreDataState>({
    balance: null,
    summary: null,
    transactions: [],
    filter: 'all',
    isLoading: true,
    isLoadingMore: false,
    error: null,
    hasMore: true,
  })
  const hasFetched = useRef(false)

  const handleAuthError = useCallback(() => {
    logout()
    push('/login')
  }, [push])

  const fetchOverview = useCallback(async () => {
    try {
      const [balanceData, summaryData] = await Promise.all([
        getCoreBalance(),
        getDailyCoreSummary(),
      ])
      setState((prev) => ({ ...prev, balance: balanceData, summary: summaryData }))
    } catch (err) {
      const message = err instanceof Error ? err.message : '加载失败'
      if (message.includes('登录')) {
        handleAuthError()
        return
      }
      setState((prev) => ({ ...prev, error: message, isLoading: false }))
    }
  }, [handleAuthError])

  const fetchTransactions = useCallback(
    async (offset: number, reset: boolean, filter: CoreFilterType) => {
      try {
        const data = await getCoreTransactions(PAGE_SIZE, offset)
        const filtered =
          filter === 'all'
            ? data.transactions
            : data.transactions.filter((t) => t.type === filter)

        setState((prev) => ({
          ...prev,
          transactions: reset ? filtered : [...prev.transactions, ...filtered],
          hasMore: data.transactions.length === PAGE_SIZE,
          isLoading: offset === 0 ? false : prev.isLoading,
          isLoadingMore: false,
        }))
      } catch (err) {
        const message = err instanceof Error ? err.message : '加载失败'
        if (message.includes('登录')) {
          handleAuthError()
          return
        }
        setState((prev) => ({
          ...prev,
          error: message,
          isLoading: false,
          isLoadingMore: false,
        }))
      }
    },
    [handleAuthError],
  )

  useEffect(() => {
    if (hasFetched.current) return
    hasFetched.current = true

    const token = getStoredToken()
    if (!token) {
      handleAuthError()
      return
    }

    fetchOverview()
    fetchTransactions(0, true, 'all')
  }, [handleAuthError, fetchOverview, fetchTransactions])

  const setFilter = useCallback(
    (filter: CoreFilterType) => {
      setState((prev) => ({
        ...prev,
        filter,
        transactions: [],
        hasMore: true,
        isLoading: true,
      }))
      fetchTransactions(0, true, filter)
    },
    [fetchTransactions],
  )

  const loadMore = useCallback(() => {
    if (state.isLoadingMore || !state.hasMore) return
    setState((prev) => ({ ...prev, isLoadingMore: true }))
    fetchTransactions(state.transactions.length, false, state.filter)
  }, [state.isLoadingMore, state.hasMore, state.transactions.length, state.filter, fetchTransactions])

  return {
    ...state,
    filterOptions: FILTER_OPTIONS,
    setFilter,
    loadMore,
  }
}
