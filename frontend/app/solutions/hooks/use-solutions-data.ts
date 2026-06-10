'use client'

import { useState, useEffect, useCallback } from 'react'
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

  const handleDelete = useCallback(
    async (id: number, confirmText: string) => {
      if (!confirm(confirmText)) return

      const token = getStoredToken()
      if (!token) return

      try {
        await deleteSolution(token, id)
        fetchSolutions(token)
      } catch (error) {
        console.error('Failed to delete:', error)
      }
    },
    [fetchSolutions],
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
  }
}
