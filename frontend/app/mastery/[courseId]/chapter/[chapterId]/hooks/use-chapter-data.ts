'use client'

import { useState, useEffect, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import { getChapterSections } from '@/lib/api/sections'
import { getStoredToken } from '@/lib/api'
import type { SectionSummary } from '@/lib/api/sections'

interface ChapterInfo {
  id: number
  title: string
  course_id: number
  course_name: string
}

export function useChapterData(courseId: number, chapterId: number) {
  const { push } = useRouter()
  const [sections, setSections] = useState<SectionSummary[]>([])
  const [chapterInfo, setChapterInfo] = useState<ChapterInfo | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadSections = async () => {
      const token = getStoredToken()
      if (!token) {
        push('/login')
        return
      }

      try {
        setLoading(true)
        const response = await getChapterSections(chapterId, token)
        setSections(response.sections)

        const stored = localStorage.getItem('current_chapter_info:v1')
        if (stored) {
          setChapterInfo(JSON.parse(stored))
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : '加载失败')
      } finally {
        setLoading(false)
      }
    }

    loadSections()
  }, [chapterId, push])

  const completedCount = useMemo(
    () => sections.filter((s) => s.is_completed).length,
    [sections],
  )

  const progress = useMemo(
    () => (sections.length > 0 ? Math.round((completedCount / sections.length) * 100) : 0),
    [sections, completedCount],
  )

  const handleSelectSection = (sectionId: number) => {
    push(`/mastery/${courseId}/chapter/${chapterId}/section/${sectionId}`)
  }

  const handleBack = () => {
    push(`/mastery/${courseId}`)
  }

  return {
    sections,
    chapterInfo,
    loading,
    error,
    completedCount,
    progress,
    handleSelectSection,
    handleBack,
  }
}
