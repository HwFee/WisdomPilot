'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { useConfirm } from '@/hooks/use-confirm'
import {
  getSolutionSummary,
  deleteSolution,
  likeSolution,
  createSolution,
} from '@/lib/api/solutions'
import { getStoredToken } from '@/lib/api/auth'
import type { SolutionSummary, SolutionCreate, SolutionUpdate } from '@/lib/api/solutions'
import { useSolutionsAuth } from './use-solutions-auth'

export function useSolutionsData() {
  const { currentUser, isAdmin, lang, push } = useSolutionsAuth()
  const [solutions, setSolutions] = useState<SolutionSummary[]>([])
  const [loading, setLoading] = useState(true)
  const hasFetched = useRef(false)
  const { confirm, dialog } = useConfirm()

  const fetchSolutions = useCallback(async (token: string) => {
    try {
      setLoading(true)
      const data = await getSolutionSummary(token, 50)
      setSolutions(data)
    } catch (error) {
      console.error('Failed to fetch solutions:', error)
    } finally {
      setLoading(false)
    }
  }, [])

  // Initial load
  useEffect(() => {
    if (hasFetched.current) return
    const token = getStoredToken()
    if (!token) {
      setLoading(false)
      return
    }
    hasFetched.current = true
    fetchSolutions(token)
  }, [fetchSolutions])

  const handleDelete = useCallback(
    async (id: number, _confirmText?: string) => {
      const confirmed = await confirm({
        title: '删除题解',
        description: '确定要删除这篇题解吗？此操作无法撤销。',
        confirmLabel: '删除',
        cancelLabel: '取消',
        variant: 'danger',
      })
      if (!confirmed) return

      const token = getStoredToken()
      if (!token) return

      try {
        await deleteSolution(token, id)
        fetchSolutions(token)
      } catch (error) {
        console.error('Failed to delete:', error)
      }
    },
    [fetchSolutions, confirm],
  )

  const handleLike = useCallback(async (id: number) => {
    const token = getStoredToken()
    if (!token) return

    try {
      const updated = await likeSolution(token, id)
      setSolutions((prev) =>
        prev.map((s) => (s.id === id ? { ...s, like_count: updated.like_count } : s)),
      )
    } catch (error) {
      console.error('Failed to like:', error)
    }
  }, [])

  const handleSave = useCallback(
    async (data: SolutionCreate | SolutionUpdate, onSuccess: () => void) => {
      const token = getStoredToken()
      if (!token) return

      try {
        await createSolution(token, data as SolutionCreate)
        onSuccess()
        fetchSolutions(token)
      } catch (error) {
        console.error('Failed to save:', error)
        const message = error instanceof Error ? error.message : '保存失败'
        alert(message)
      }
    },
    [fetchSolutions],
  )

  return {
    solutions,
    setSolutions,
    loading,
    fetchSolutions,
    userState: { currentUser, isAdmin, lang },
    handleDelete,
    handleLike,
    handleSave,
    push,
    dialog,
  }
}
