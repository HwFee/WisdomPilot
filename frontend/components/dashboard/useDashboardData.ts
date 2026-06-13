'use client'

import { useCallback, useReducer } from 'react'
import {
  getProfile,
  getReviewStats,
  checkin,
  getCheckinStatus,
  getCheckinDetails,
  getFavoritesCount,
  getNotesCount,
  getUserCourseProgress,
  getTodayStats,
  getGlobalTierInfo,
  getStoredToken,
  API_BASE_URL,
  type Activity,
  type CourseProgress,
  type TodayStatsResponse,
  type User,
} from '@/lib/api'
import type { ReviewStatsResponse } from '@/types/review'
import type { UserProfileResponse, CheckinDetailsResponse, TierInfo } from '@/types/api'

type Language = 'zh' | 'en'

type DashboardState = {
  user: User | null
  lang: Language
  isLoading: boolean
  profile: UserProfileResponse | null
  coursesProgress: CourseProgress[]
  reviewStats: ReviewStatsResponse | null
  activities: Activity[]
  isCheckedIn: boolean
  favoritesCount: number
  notesCount: number
  checkinDetails: CheckinDetailsResponse | null
  todayStats: TodayStatsResponse
  tierInfo: TierInfo | null
}

const initialState: DashboardState = {
  user: null,
  lang: 'zh',
  isLoading: true,
  profile: null,
  coursesProgress: [],
  reviewStats: null,
  activities: [],
  isCheckedIn: false,
  favoritesCount: 0,
  notesCount: 0,
  checkinDetails: null,
  todayStats: {
    exercises: 0,
    correct: 0,
    accuracy: 0,
    time_minutes: 0,
  },
  tierInfo: null,
}

type DashboardAction =
  | {
      type: 'INITIALIZE_SESSION'
      payload: { user: User; lang: Language }
    }
  | { type: 'SET_LANGUAGE'; payload: Language }
  | { type: 'FETCH_SUCCESS'; payload: Partial<DashboardState> }
  | { type: 'FETCH_ERROR' }
  | {
      type: 'CHECKIN_SUCCESS'
      payload: { streak_days: number; total_checkin_days: number }
    }

function dashboardReducer(
  state: DashboardState,
  action: DashboardAction
): DashboardState {
  switch (action.type) {
    case 'INITIALIZE_SESSION':
      return { ...state, user: action.payload.user, lang: action.payload.lang }
    case 'SET_LANGUAGE':
      return { ...state, lang: action.payload }
    case 'FETCH_SUCCESS':
      return { ...state, isLoading: false, ...action.payload }
    case 'FETCH_ERROR':
      return { ...state, isLoading: false }
    case 'CHECKIN_SUCCESS': {
      const { streak_days, total_checkin_days } = action.payload
      return {
        ...state,
        isCheckedIn: true,
        profile: state.profile
          ? { ...state.profile, streak_days }
          : state.profile,
        checkinDetails: state.checkinDetails
          ? {
              ...state.checkinDetails,
              streak_days,
              total_checkin_days,
              checked_in_today: true,
            }
          : state.checkinDetails,
      }
    }
    default:
      return state
  }
}

export type UseDashboardReturn = {
  state: DashboardState
  initializeSession: (user: User, lang: Language) => void
  setLanguage: (lang: Language) => void
  fetchData: (token: string) => Promise<void>
  handleCheckIn: () => Promise<void>
}

export function useDashboardData(): UseDashboardReturn {
  const [state, dispatch] = useReducer(dashboardReducer, initialState)

  const initializeSession = useCallback((user: User, lang: Language) => {
    dispatch({ type: 'INITIALIZE_SESSION', payload: { user, lang } })
  }, [])

  const setLanguage = useCallback((lang: Language) => {
    dispatch({ type: 'SET_LANGUAGE', payload: lang })
  }, [])

  const fetchData = useCallback(async (token: string) => {
    try {
      const courseProgressData = await getUserCourseProgress(token)

      const profileResult = await getProfile(token).catch(() => null)

      const reviewResult = await getReviewStats(token).catch(() => null)

      let activitiesResponse
      try {
        const response = await fetch(
          `${API_BASE_URL}/api/users/me/activities?limit=10`,
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        )
        if (response.ok) {
          activitiesResponse = await response.json()
        } else {
          console.error('[Dashboard] Activities fetch failed:', response.status)
          activitiesResponse = { activities: [] }
        }
      } catch (err) {
        console.error('[Dashboard] Activities fetch error:', err)
        activitiesResponse = { activities: [] }
      }

      let checkedInToday = false
      try {
        const checkinStatus = await getCheckinStatus(token)
        checkedInToday = checkinStatus.checked_in_today
      } catch {
        /* ignore */
      }

      let details: CheckinDetailsResponse | null = null
      try {
        details = await getCheckinDetails(token)
      } catch {
        /* ignore */
      }

      let favorites = 0
      let notes = 0
      try {
        const [favCount, noteCount] = await Promise.all([
          getFavoritesCount(token).catch(() => ({ count: 0 })),
          getNotesCount(token).catch(() => ({ count: 0 })),
        ])
        favorites = favCount.count
        notes = noteCount.count
      } catch {
        /* ignore */
      }

      let todayData: TodayStatsResponse = initialState.todayStats
      try {
        todayData = await getTodayStats(token)
      } catch {
        /* ignore */
      }

      let tierData: TierInfo | null = null
      try {
        tierData = await getGlobalTierInfo()
      } catch {
        /* ignore */
      }

      dispatch({
        type: 'FETCH_SUCCESS',
        payload: {
          coursesProgress: courseProgressData.courses,
          profile: profileResult,
          reviewStats: reviewResult ?? null,
          activities: activitiesResponse.activities || [],
          isCheckedIn: checkedInToday,
          favoritesCount: favorites,
          notesCount: notes,
          checkinDetails: details,
          todayStats: todayData,
          tierInfo: tierData,
        },
      })
    } catch (err) {
      console.error('[Dashboard] fetchData failed:', err)
      dispatch({ type: 'FETCH_ERROR' })
    }
  }, [])

  const handleCheckIn = useCallback(async () => {
    const token = getStoredToken()
    if (!token) {
      console.error('Check-in failed: No token')
      return
    }

    try {
      const result = await checkin(token)
      dispatch({
        type: 'CHECKIN_SUCCESS',
        payload: {
          streak_days: result.streak_days,
          total_checkin_days: result.total_checkin_days,
        },
      })
    } catch (error) {
      console.error('Check-in failed:', error)
    }
  }, [])

  return { state, initializeSession, setLanguage, fetchData, handleCheckIn }
}
