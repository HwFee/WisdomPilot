'use client'

import { useEffect, useState, useRef, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { getStoredToken, logout } from '@/lib/api'
import { getXpBalance, getXpTransactions, type XpTransaction } from '@/lib/api/xp'
import type { TransactionFilterOption } from '@/components/transactions/transaction-list'

export type XpFilterType = 'all' | 'earn'

const PAGE_SIZE = 20

const FILTER_OPTIONS: TransactionFilterOption[] = [
  { value: 'all', label: '全部' },
  { value: 'earn', label: '获得' },
]

interface XpDataState {
  balance: { balance: number; level: string } | null
  transactions: XpTransaction[]
  filter: XpFilterType
  isLoading: boolean
  isLoadingMore: boolean
  error: string | null
  hasMore: boolean
}

export function useXpData() {
  const { push } = useRouter()
  const [state, setState] = useState<XpDataState>({
    balance: null,
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

  const fetchBalance = useCallback(async () => {
    try {
      const data = await getXpBalance()
      setState((prev) => ({ ...prev, balance: data }))
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
    async (offset: number, reset: boolean, filter: XpFilterType) => {
      try {
        const data = await getXpTransactions(PAGE_SIZE, offset)
        const filtered =
          filter === 'all'
            ? data.transactions
            : data.transactions.filter((t) => t.type === 'earn')

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

    fetchBalance()
    fetchTransactions(0, true, 'all')
  }, [handleAuthError, fetchBalance, fetchTransactions])

  const setFilter = useCallback(
    (filter: XpFilterType) => {
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
