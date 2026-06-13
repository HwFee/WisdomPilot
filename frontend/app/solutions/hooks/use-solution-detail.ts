'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { useConfirm } from '@/hooks/use-confirm'
import { getSolution, deleteSolution, updateSolution } from '@/lib/api/solutions'
import { getStoredToken } from '@/lib/api/auth'
import type { SolutionResponse, SolutionUpdate } from '@/lib/api/solutions'
import { useSolutionsAuth } from './use-solutions-auth'

export function useSolutionDetail(solutionId: number) {
  const { push } = useRouter()
  const { currentUser, isAdmin, lang } = useSolutionsAuth()
  const [solution, setSolution] = useState<SolutionResponse | null>(null)
  const [initialized, setInitialized] = useState(false)
  const [editMode, setEditMode] = useState(false)
  const loading = !initialized
  const { confirm, dialog } = useConfirm()

  const fetchSolution = useCallback(async (token: string) => {
    try {
      const data = await getSolution(token, solutionId)
      // react-doctor-disable-next-line no-derived-state — solution is fetched from the API, not derivable from props/state
      setSolution(data)
    } catch (error) {
      console.error('Failed to fetch solution:', error)
      push('/solutions')
    } finally {
      setInitialized(true)
    }
  }, [solutionId, push])

  useEffect(() => {
    const token = getStoredToken()
    if (!token) return
    fetchSolution(token)
  }, [solutionId, fetchSolution])

  const handleDelete = useCallback(
    async (_confirmText?: string) => {
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
        await deleteSolution(token, solutionId)
        push('/solutions')
      } catch (error) {
        console.error('Failed to delete:', error)
      }
    },
    [solutionId, push, confirm],
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
    dialog,
  }
}
