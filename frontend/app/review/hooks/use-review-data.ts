'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { useConfirm } from '@/hooks/use-confirm'
import {
  getWrongQuestions,
  deleteWrongQuestion,
} from '@/lib/api/review'
import type { WrongQuestionResponse as WrongQuestion } from '@/lib/api/review'

export function useReviewData() {
  const { push } = useRouter()
  const [wrongQuestions, setWrongQuestions] = useState<WrongQuestion[]>([])
  const [initialized, setInitialized] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const loading = !initialized && !error
  const { confirm, dialog } = useConfirm()

  const getToken = useCallback(() => {
    if (typeof window === 'undefined') return null
    return localStorage.getItem('token:v1')
  }, [])

  const fetchData = useCallback(async () => {
    const token = getToken()
    if (!token) {
      push('/login')
      return
    }

    try {
      const wrongData = await getWrongQuestions(token).catch(() => ({
        wrong_questions: [],
        total: 0,
        unresolved_count: 0,
      }))
      // react-doctor-disable-next-line no-derived-state — wrongQuestions are fetched from the API, not derivable from props/state
      setWrongQuestions(wrongData.wrong_questions || [])
    } catch {
      setError('获取错题数据失败')
    } finally {
      setInitialized(true)
    }
  }, [getToken, push])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const handleDelete = useCallback(
    async (wrongQuestionId: string) => {
      const confirmed = await confirm({
        title: '删除错题',
        description: '确定要删除这条错题记录吗？此操作无法撤销。',
        confirmLabel: '删除',
        cancelLabel: '取消',
        variant: 'danger',
      })
      if (!confirmed) return

      const token = getToken()
      if (!token) return

      try {
        await deleteWrongQuestion(wrongQuestionId, token)
        setWrongQuestions((prev) => prev.filter((wq) => wq.id !== wrongQuestionId))
      } catch {
        alert('删除失败，请稍后重试')
      }
    },
    [getToken, confirm],
  )

  const clearError = useCallback(() => {
    setError(null)
  }, [])

  return {
    wrongQuestions,
    loading,
    error,
    fetchData,
    handleDelete,
    clearError,
    push,
    dialog,
  }
}
