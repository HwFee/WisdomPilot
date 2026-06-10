'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { getStoredToken } from '@/lib/api'
import type { TierTransaction, TransactionListResponse } from '../lib/tier-utils'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const PAGE_SIZE = 20

export function useTierData() {
  const { push, back } = useRouter()
  const [loading, setLoading] = useState(true)
  const [transactions, setTransactions] = useState<TierTransaction[]>([])
  const pageRef = useRef(0)
  const [total, setTotal] = useState(0)
  const [loadingMore, setLoadingMore] = useState(false)

  const fetchData = useCallback(
    async (pageNum: number = 0, append: boolean = false) => {
      const token = getStoredToken()
      if (!token) {
        push('/login')
        return
      }

      if (append) {
        setLoadingMore(true)
      } else {
        setLoading(true)
      }

      try {
        const res = await fetch(
          `${API_URL}/api/tier/transactions?limit=${PAGE_SIZE}&offset=${pageNum * PAGE_SIZE}`,
          {
            headers: { Authorization: `Bearer ${token}` },
          },
        )
        if (res.ok) {
          const data: TransactionListResponse = await res.json()
          setTransactions((prev) =>
            append ? [...prev, ...data.transactions] : data.transactions,
          )
          setTotal(data.total)
          pageRef.current = pageNum
        }
      } catch (error) {
        console.error('Failed to fetch data:', error)
      } finally {
        setLoading(false)
        setLoadingMore(false)
      }
    },
    [push],
  )

  useEffect(() => {
    fetchData(0)
  }, [fetchData])

  const loadMore = useCallback(() => {
    if (!loadingMore && transactions.length < total) {
      fetchData(pageRef.current + 1, true)
    }
  }, [loadingMore, transactions.length, total, fetchData])

  return {
    transactions,
    total,
    loading,
    loadingMore,
    fetchData,
    loadMore,
    back,
    push,
  }
}
