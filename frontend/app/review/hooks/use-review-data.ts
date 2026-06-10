'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import {
  getWrongQuestions,
  deleteWrongQuestion,
} from '@/lib/api/review'
import type { WrongQuestionResponse as WrongQuestion } from '@/lib/api/review'

export function useReviewData() {
  const { push } = useRouter()
  const [wrongQuestions, setWrongQuestions] = useState<WrongQuestion[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

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
      setLoading(true)
      const wrongData = await getWrongQuestions(token).catch(() => ({
        wrong_questions: [],
        total: 0,
        unresolved_count: 0,
      }))
      setWrongQuestions(wrongData.wrong_questions || [])
    } catch {
      setError('获取错题数据失败')
    } finally {
      setLoading(false)
    }
  }, [getToken, push])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const handleDelete = useCallback(
    async (wrongQuestionId: string) => {
      if (!confirm('确定要删除这条错题记录吗？')) return

      const token = getToken()
      if (!token) return

      try {
        await deleteWrongQuestion(wrongQuestionId, token)
        setWrongQuestions((prev) => prev.filter((wq) => wq.id !== wrongQuestionId))
      } catch {
        alert('删除失败，请稍后重试')
      }
    },
    [getToken],
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
  }
}
