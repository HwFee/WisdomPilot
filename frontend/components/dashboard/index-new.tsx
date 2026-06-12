'use client'

import { useEffect, useRef, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { getStoredUser, getStoredToken } from '@/lib/api'
import { useDashboardData } from './useDashboardData'
import { PageContainer, SectionHeader, ContentGrid } from '@/components/layout'
import { type Language, translate } from './dashboard-i18n'

// Dashboard components
import { WelcomeSection } from './WelcomeSection'
import { TodayStats } from './TodayStats'
import { SolutionBoard } from './SolutionBoard'
import { QuickTools } from './QuickTools'
import { RecentActivity } from './RecentActivity'
import { CurrentLearningPanel } from './CurrentLearningPanel'
import { DashboardHeader } from './sections/DashboardHeader'
import { DashboardLoading } from './sections/DashboardLoading'

// 自定义事件名称
const DASHBOARD_REFRESH_EVENT = 'dashboard:refresh'

// Trend data - default values
const DEFAULT_TREND = {
  exercises: 0,
  accuracy: 0,
  time: 0,
}

export default function DashboardPage() {
  const { push } = useRouter()
  const hasFetched = useRef(false)
  const { state, initializeSession, setLanguage, fetchData, handleCheckIn } =
    useDashboardData()

  // Ref to avoid effect re-subscription
  const fetchDataRef = useRef(fetchData)
  fetchDataRef.current = fetchData

  const initializeSessionRef = useRef(initializeSession)
  initializeSessionRef.current = initializeSession

  useEffect(() => {
    if (hasFetched.current) return
    const token = getStoredToken()
    const storedUser = getStoredUser()
    let savedLang: Language = 'zh'
    try {
      const rawLang = localStorage.getItem('language')
      if (rawLang === 'zh' || rawLang === 'en') {
        savedLang = rawLang
      }
    } catch {
      /* ignore */
    }
    if (!token || !storedUser) {
      push('/login')
      return
    }
    initializeSessionRef.current(storedUser, savedLang)
    hasFetched.current = true
    fetchDataRef.current(token)
  }, [push])

  // 监听仪表盘刷新事件
  useEffect(() => {
    const handleRefresh = () => {
      const token = getStoredToken()
      if (token) {
        fetchDataRef.current(token)
      }
    }

    window.addEventListener(DASHBOARD_REFRESH_EVENT, handleRefresh)
    return () => window.removeEventListener(DASHBOARD_REFRESH_EVENT, handleRefresh)
  }, [])

  // 保底机制：页面可见时刷新数据（用户返回仪表盘时）
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        const token = getStoredToken()
        if (token) {
          fetchDataRef.current(token)
        }
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
  }, [])

  const handleLanguageChange = useCallback(
    (lang: Language) => {
      setLanguage(lang)
      try {
        localStorage.setItem('language', lang)
      } catch {
        /* ignore */
      }
    },
    [setLanguage]
  )

  const t = (zh: string, en: string) => translate(zh, en, state.lang)

  const todayDate = new Date().toLocaleDateString(
    state.lang === 'zh' ? 'zh-CN' : 'en-US',
    {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    }
  )

  if (state.isLoading) {
    return <DashboardLoading lang={state.lang} />
  }

  return (
    <div className="min-h-screen bg-background">
      <DashboardHeader
        user={state.user}
        profile={state.profile}
        lang={state.lang}
        onLanguageChange={handleLanguageChange}
      />

      {/* Main Content */}
      <main className="pt-24 pb-8">
        <PageContainer>
          {/* 问候区 */}
          <section className="mb-12">
            <WelcomeSection
              user={{
                id: state.user?.id || '',
                username: state.user?.username || '',
              }}
              lang={state.lang}
              streakDays={state.profile?.streak_days ?? 0}
            />
          </section>

          {/* 统计区 */}
          <section className="mb-12">
            <SectionHeader title={t('今日数据', "Today's Stats")} date={todayDate} />
            <TodayStats
              stats={{
                exercisesToday: state.todayStats.exercises,
                accuracy: state.todayStats.accuracy,
                learningMinutes: Math.round(state.todayStats.time_minutes),
                streakDays: state.profile?.streak_days ?? 0,
              }}
              trend={DEFAULT_TREND}
              lang={state.lang}
              onExercisesClick={() => push('/dashboard/exercises')}
              onAccuracyClick={() => push('/dashboard/accuracy')}
              onTimeClick={() => push('/dashboard/time')}
            />
          </section>

          {/* 中部内容 */}
          <section className="mb-12">
            <ContentGrid>
              <CurrentLearningPanel
                courses={state.coursesProgress}
                lang={state.lang}
              />
              <QuickTools
                wrongCount={state.reviewStats?.wrong_count ?? 0}
                favoritesCount={state.favoritesCount}
                notesCount={state.notesCount}
                streakDays={state.profile?.streak_days ?? 0}
                totalCheckinDays={state.checkinDetails?.total_checkin_days ?? 0}
                isCheckedIn={state.isCheckedIn}
                onWrongClick={() => push('/review?type=wrong')}
                onFavoritesClick={() => push('/favorites')}
                onNotesClick={() => push('/notes')}
                onCheckIn={handleCheckIn}
                lang={state.lang}
                lunarStr={state.checkinDetails?.lunar_str}
                solarTerm={state.checkinDetails?.solar_term_str?.split(' (')[0]}
                holiday={state.checkinDetails?.holiday_str?.split(' (')[0]}
                streakMultiplier={state.checkinDetails?.streak_multiplier ?? 1.0}
              />
            </ContentGrid>
          </section>

          {/* 底部内容 */}
          <section>
            <ContentGrid>
              <RecentActivity
                activities={state.activities}
                onStartLearning={() => push('/courses')}
                lang={state.lang}
              />
              <SolutionBoard lang={state.lang} />
            </ContentGrid>
          </section>
        </PageContainer>
      </main>
    </div>
  )
}
