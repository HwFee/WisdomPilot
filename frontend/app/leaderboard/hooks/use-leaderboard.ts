'use client'

import { useEffect, useState, useRef } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { getStoredToken, logout, getMasteryLeaderboard, getArenaLeaderboard } from '@/lib/api'
import { getUserCourseProgress } from '@/lib/api/courses'
import type { LeaderboardEntry } from '@/types/api'
import type { CourseProgress } from '@/lib/api/courses'

export type LeaderboardType = 'mastery' | 'arena'

interface UiState {
  activeTab: LeaderboardType
  offset: number
  loading: boolean
}

interface DataState {
  enrolledCourses: CourseProgress[]
  leaderboard: LeaderboardEntry[]
}

interface CurrentUserState {
  rank: number | null
  data: LeaderboardEntry | null
}

export function useLeaderboard() {
  const { push } = useRouter()
  const searchParams = useSearchParams()
  const [uiState, setUiState] = useState<UiState>({
    activeTab: (searchParams.get('tab') as LeaderboardType) || 'mastery',
    offset: 0,
    loading: true,
  })
  const courseIdRef = useRef<number>(1)
  const [dataState, setDataState] = useState<DataState>({
    enrolledCourses: [],
    leaderboard: [],
  })
  const currentUserIdRef = useRef<string | null>(null)
  const [currentUserState, setCurrentUserState] = useState<CurrentUserState>({ rank: null, data: null })
  const limit = 20
  const hasFetched = useRef(false)
  const hasFetchedCourses = useRef(false)

  const fetchData = async (token: string, tab: LeaderboardType, off: number = 0) => {
    try {
      setUiState(prev => ({ ...prev, loading: true }))
      const data = tab === 'mastery'
        ? await getMasteryLeaderboard(courseIdRef.current, token, limit, off)
        : await getArenaLeaderboard(courseIdRef.current, token, limit, off)

      if (off === 0) {
        setDataState(prev => ({ ...prev, leaderboard: data.entries }))
      } else {
        setDataState(prev => ({ ...prev, leaderboard: [...prev.leaderboard, ...data.entries] }))
      }
      setCurrentUserState(prev => ({ ...prev, rank: data.user_rank }))

      const userId = currentUserIdRef.current || (() => {
        try {
          const payload = JSON.parse(atob(token.split('.')[1]))
          return payload.sub
        } catch {
          return null
        }
      })()

      if (userId && data.entries) {
        const userEntry = data.entries.find((e: LeaderboardEntry) => e.user_id === userId)
        if (userEntry) {
          setCurrentUserState(prev => ({ ...prev, data: userEntry }))
        }
      }
    } catch (error) {
      console.error('[Leaderboard] Error:', error)
    } finally {
      setUiState(prev => ({ ...prev, loading: false }))
    }
  }

  useEffect(() => {
    if (hasFetchedCourses.current) return
    const token = getStoredToken()
    if (!token) {
      logout()
      push('/login')
      return
    }

    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      currentUserIdRef.current = payload.sub
    } catch {
      // Ignore parsing errors
    }

    getUserCourseProgress(token)
      .then((progress) => {
        const courses = progress.courses || []
        setDataState(prev => ({ ...prev, enrolledCourses: courses }))
        if (courses.length > 0) {
          const firstEnrolled = courses.find(c => c.progress !== null && c.progress > 0) || courses[0]
          courseIdRef.current = firstEnrolled.course_id
        }
        if (!hasFetched.current) {
          hasFetched.current = true
          fetchData(token, uiState.activeTab, 0)
        }
      })
      .catch((err) => {
        console.error('[Leaderboard] Failed to fetch course progress:', err)
      })
      .finally(() => {
        hasFetchedCourses.current = true
      })
  }, [push, uiState.activeTab])

  const handleTabChange = (tab: LeaderboardType) => {
    setUiState(prev => ({ ...prev, activeTab: tab, offset: 0 }))
    setCurrentUserState(prev => ({ ...prev, data: null }))
    const token = getStoredToken()
    if (token) {
      fetchData(token, tab, 0)
    }
    push(`/leaderboard?tab=${tab}`)
  }

  const handleLoadMore = () => {
    const newOffset = uiState.offset + limit
    setUiState(prev => ({ ...prev, offset: newOffset }))
    const token = getStoredToken()
    if (token) {
      fetchData(token, uiState.activeTab, newOffset)
    }
  }

  return {
    activeTab: uiState.activeTab,
    offset: uiState.offset,
    loading: uiState.loading,
    enrolledCourses: dataState.enrolledCourses,
    leaderboard: dataState.leaderboard,
    currentUserRank: currentUserState.rank,
    currentUserData: currentUserState.data,
    currentUserId: currentUserIdRef.current,
    limit,
    handleTabChange,
    handleLoadMore,
  }
}
