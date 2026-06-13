'use client'

import { useEffect, useState, useRef, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { getStoredToken, logout } from '@/lib/api'
import { getGlobalTierInfo, getTierTransactions, type TierTransaction } from '@/lib/api/tier'
import type { TierInfo } from '@/types/api'
import type { TransactionFilterOption } from '@/components/transactions/transaction-list'

export type TierFilterType = 'all' | 'gain' | 'loss'

const PAGE_SIZE = 20

const FILTER_OPTIONS: TransactionFilterOption[] = [
  { value: 'all', label: '全部' },
  { value: 'gain', label: '获得' },
  { value: 'loss', label: '失去' },
]

interface TierDataState {
  tierInfo: TierInfo | null
  transactions: TierTransaction[]
  filter: TierFilterType
  isLoading: boolean
  isLoadingMore: boolean
  error: string | null
  hasMore: boolean
}

export function useTierData() {
  const { push } = useRouter()
  const [state, setState] = useState<TierDataState>({
    tierInfo: null,
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

  const fetchTierInfo = useCallback(async () => {
    try {
      const data = await getGlobalTierInfo()
      setState((prev) => ({ ...prev, tierInfo: data }))
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
    async (offset: number, reset: boolean, filter: TierFilterType) => {
      try {
        const data = await getTierTransactions(undefined, PAGE_SIZE, offset)
        const filtered = data.transactions.filter((t) => {
          if (filter === 'all') return true
          return filter === 'gain' ? t.stars_change >= 0 : t.stars_change < 0
        })

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

    fetchTierInfo()
    fetchTransactions(0, true, 'all')
  }, [handleAuthError, fetchTierInfo, fetchTransactions])

  const setFilter = useCallback(
    (filter: TierFilterType) => {
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
