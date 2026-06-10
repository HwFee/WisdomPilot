'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { getSolution, deleteSolution, updateSolution } from '@/lib/api/solutions'
import { getStoredToken } from '@/lib/api/auth'
import type { SolutionResponse, SolutionUpdate } from '@/lib/api/solutions'
import { useSolutionsAuth } from './use-solutions-auth'

export function useSolutionDetail(solutionId: number) {
  const { push } = useRouter()
  const { currentUser, isAdmin, lang } = useSolutionsAuth()
  const [solution, setSolution] = useState<SolutionResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [editMode, setEditMode] = useState(false)

  const fetchSolution = useCallback(async (token: string) => {
    try {
      setLoading(true)
      const data = await getSolution(token, solutionId)
      setSolution(data)
    } catch (error) {
      console.error('Failed to fetch solution:', error)
      push('/solutions')
    } finally {
      setLoading(false)
    }
  }, [solutionId, push])

  useEffect(() => {
    const token = getStoredToken()
    if (!token) return
    fetchSolution(token)
  }, [solutionId, fetchSolution])

  const handleDelete = useCallback(
    async (confirmText: string) => {
      if (!confirm(confirmText)) return

      const token = getStoredToken()
      if (!token) return

      try {
        await deleteSolution(token, solutionId)
        push('/solutions')
      } catch (error) {
        console.error('Failed to delete:', error)
      }
    },
    [solutionId, push],
  )

  const handleEditSave = useCallback(
    async (data: SolutionUpdate & { is_announcement?: boolean }) => {
      const token = getStoredToken()
      if (!token) return

      try {
        await updateSolution(token, solutionId, data)
        setEditMode(false)
        fetchSolution(token)
      } catch (error) {
        console.error('Failed to update:', error)
      }
    },
    [solutionId, fetchSolution],
  )

  return {
    solution,
    loading,
    editMode,
    setEditMode,
    currentUser,
    isAdmin,
    lang,
    handleDelete,
    handleEditSave,
    push,
  }
}
