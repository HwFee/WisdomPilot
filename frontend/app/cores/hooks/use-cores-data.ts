'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { getStoredToken } from '@/lib/api'
import type {
  CoreBalance,
  CoreTransaction,
  TransactionListResponse,
} from '../lib/cores-utils'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const PAGE_SIZE = 20

export function useCoresData() {
  const { push, back } = useRouter()
  const [balance, setBalance] = useState<CoreBalance | null>(null)
  const [transactions, setTransactions] = useState<CoreTransaction[]>([])
  const pageRef = useRef(0)
  const [total, setTotal] = useState(0)
  const [loadingState, setLoadingState] = useState({ main: true, more: false })

  const fetchData = useCallback(
    async (pageNum: number = 0, append: boolean = false) => {
      const token = getStoredToken()
      if (!token) {
        push('/login')
        return
      }

      setLoadingState((prev) => ({
        ...prev,
        [append ? 'more' : 'main']: true,
      }))

      try {
        const [balanceRes, transactionsRes] = await Promise.all([
          fetch(`${API_URL}/api/cores/balance`, {
            headers: { Authorization: `Bearer ${token}` },
          }),
          fetch(
            `${API_URL}/api/cores/transactions?limit=${PAGE_SIZE}&offset=${pageNum * PAGE_SIZE}`,
            { headers: { Authorization: `Bearer ${token}` } },
          ),
        ])

        if (balanceRes.ok) {
          setBalance(await balanceRes.json())
        }

        if (transactionsRes.ok) {
          const data: TransactionListResponse = await transactionsRes.json()
          setTransactions((prev) =>
            append ? [...prev, ...data.transactions] : data.transactions,
          )
          setTotal(data.total)
          pageRef.current = pageNum
        }
      } catch (error) {
        console.error('Failed to fetch data:', error)
      } finally {
        setLoadingState({ main: false, more: false })
      }
    },
    [push],
  )

  useEffect(() => {
    fetchData(0)
  }, [fetchData])

  const loadMore = useCallback(() => {
    if (!loadingState.more && transactions.length < total) {
      fetchData(pageRef.current + 1, true)
    }
  }, [loadingState.more, transactions.length, total, fetchData])

  return {
    balance,
    transactions,
    total,
    loadingState,
    fetchData,
    loadMore,
    back,
    push,
  }
}
