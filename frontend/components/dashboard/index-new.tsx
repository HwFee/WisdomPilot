'use client'

import { useEffect, useState, useRef, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import {
  getStoredUser,
  getStoredToken,
  logout,
  User,
  Activity,
  getProfile,
  getReviewStats,
  checkin,
  getCheckinStatus,
  getCheckinDetails,
  getFavoritesCount,
  getNotesCount,
  getUserCourseProgress,
  getTodayStats,
  CourseProgress,
  TodayStatsResponse,
  API_BASE_URL,
} from '@/lib/api'
import { Sparkles, Zap, Trophy, Gem } from 'lucide-react'
import type { ReviewStatsResponse } from '@/types/review'
import type { UserProfileResponse, CheckinDetailsResponse } from '@/types/api'
import { Logo } from '@/components/ui/logo'
import { PageContainer, SectionHeader, ContentGrid } from '@/components/layout'

// Dashboard components
import { WelcomeSection } from './WelcomeSection'
import { TodayStats } from './TodayStats'
import { SolutionBoard } from './SolutionBoard'
import { QuickTools } from './QuickTools'
import { RecentActivity } from './RecentActivity'
import { CurrentLearningPanel } from './CurrentLearningPanel'

// 自定义事件名称
const DASHBOARD_REFRESH_EVENT = 'dashboard:refresh'

export default function DashboardPage() {
  const { push } = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [profile, setProfile] = useState<UserProfileResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [lang, setLang] = useState<'zh' | 'en'>('zh')
  const hasFetched = useRef(false)

  // Course progress state
  const [coursesProgress, setCoursesProgress] = useState<CourseProgress[]>([])

  const [reviewStats, setReviewStats] = useState<ReviewStatsResponse | null>(null)
  const [activities, setActivities] = useState<Activity[]>([])
  const [isCheckedIn, setIsCheckedIn] = useState(false)
  const [favoritesCount, setFavoritesCount] = useState(0)
  const [notesCount, setNotesCount] = useState(0)

  // Check-in details state
  const [checkinDetails, setCheckinDetails] = useState<CheckinDetailsResponse | null>(null)

  // Today stats - now from real API
  const [todayStats, setTodayStats] = useState<TodayStatsResponse>({
    exercises: 0,
    correct: 0,
    accuracy: 0,
    time_minutes: 0,
  })

  // Trend data - default values
  const [trend] = useState({
    exercises: 0,
    accuracy: 0,
    time: 0,
  })

  const fetchData = useCallback(async (token: string) => {
    try {
      // Fetch user course progress (new API)
      const courseProgressData = await getUserCourseProgress(token)
      setCoursesProgress(courseProgressData.courses)

      // Fetch profile
      const profileResult = await getProfile(token).catch(() => null)
      setProfile(profileResult)

      // Fetch review stats
      const reviewResult = await getReviewStats(token).catch(() => null)
      if (reviewResult) setReviewStats(reviewResult)

      // Fetch activities
      let activitiesResponse
      try {
        const r = await fetch(`${API_BASE_URL}/api/users/me/activities?limit=10`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        if (r.ok) {
          activitiesResponse = await r.json()
        } else {
          console.error('[Dashboard] Activities fetch failed:', r.status)
          activitiesResponse = { activities: [] }
        }
      } catch (err) {
        console.error('[Dashboard] Activities fetch error:', err)
        activitiesResponse = { activities: [] }
      }
      setActivities(activitiesResponse.activities || [])

      // Check checkin status
      try {
        const checkinStatus = await getCheckinStatus(token)
        setIsCheckedIn(checkinStatus.checked_in_today)
      } catch { /* ignore */ }

      // Get checkin details (with lunar/solar term info)
      try {
        const details = await getCheckinDetails(token)
        setCheckinDetails(details)
      } catch { /* ignore */ }

      // Get favorites and notes count
      try {
        const [favCount, noteCount] = await Promise.all([
          getFavoritesCount(token).catch(() => ({ count: 0 })),
          getNotesCount(token).catch(() => ({ count: 0 })),
        ])
        setFavoritesCount(favCount.count)
        setNotesCount(noteCount.count)
      } catch { /* ignore */ }

      // Fetch today's stats (new API)
      try {
        const todayData = await getTodayStats(token)
        setTodayStats(todayData)
      } catch { /* ignore */ }

    } catch (err) {
      // 记录错误并展示给用户，避免无限 loading
      setIsLoading(false)
      console.error("[Dashboard] fetchData failed:", err)
    } finally {
      setIsLoading(false)
    }
  }, [])

  // Ref to avoid effect re-subscription
  const fetchDataRef = useRef(fetchData)
  fetchDataRef.current = fetchData

  useEffect(() => {
    if (hasFetched.current) return
    const token = getStoredToken()
    const storedUser = getStoredUser()
    let savedLang = 'zh'
    try { savedLang = localStorage.getItem('language') || 'zh' } catch { /* ignore */ }
    if (!token || !storedUser) { push('/login'); return }
    setUser(storedUser)
    setLang(savedLang as 'zh' | 'en')
    hasFetched.current = true
    fetchData(token)
  }, [push, fetchData])

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

  const handleLogout = () => { logout(); push('/login') }

  const toggleLanguage = () => {
    const newLang = lang === 'zh' ? 'en' : 'zh'
    setLang(newLang)
    try { localStorage.setItem('language', newLang) } catch { /* ignore */ }
  }

  const t = (zh: string, en: string) => lang === 'zh' ? zh : en

  // Handle check-in
  const handleCheckIn = async () => {
    const token = getStoredToken()
    if (!token) {
      console.error('Check-in failed: No token')
      return
    }

    try {
      const result = await checkin(token)
      setIsCheckedIn(true)

      // Update streak days on profile
      if (profile) {
        setProfile(prev => prev ? ({ ...prev, streak_days: result.streak_days }) : prev)
      }

      // Update checkin details so the progress bar and stats refresh immediately
      if (checkinDetails) {
        setCheckinDetails(prev => prev ? ({
          ...prev,
          streak_days: result.streak_days,
          total_checkin_days: result.total_checkin_days,
          checked_in_today: true,
        }) : prev)
      }
    } catch (error) {
      console.error('Check-in failed:', error)
    }
  }

  const todayDate = new Date().toLocaleDateString(lang === 'zh' ? 'zh-CN' : 'en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <div className="size-16 bg-primary/10 rounded-2xl flex items-center justify-center mx-auto mb-4 animate-pulse">
            <Sparkles className="size-8 text-primary" />
          </div>
          <p className="text-muted-foreground">{t('加载中...', 'Loading...')}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 glass border-b border-border/50">
        <PageContainer>
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3">
              <Logo className="text-blue-500" />
              <div>
                <h1 className="text-base font-semibold text-foreground">智码领航</h1>
                <p className="text-xs text-muted-foreground hidden sm:block">{t('基于生成式AI的实践教学系统', 'AI-Powered Learning')}</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="hidden sm:flex items-center gap-2">
                <div className="flex items-center gap-1.5 px-2.5 py-1 bg-purple-500/10 rounded-full">
                  <Gem className="size-3.5 text-purple-500" />
                  <span className="text-xs font-medium text-purple-600 dark:text-purple-400">{profile?.cores ?? 100}</span>
                </div>
              </div>

              <div className="flex items-center bg-muted rounded-full p-0.5">
                <button type="button" onClick={() => { if (lang !== 'zh') toggleLanguage() }}
                  className={`px-2 py-0.5 rounded-full text-xs font-medium transition-all ${lang === 'zh' ? 'bg-card text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}>
                  中
                </button>
                <button type="button" onClick={() => { if (lang !== 'en') toggleLanguage() }}
                  className={`px-2 py-0.5 rounded-full text-xs font-medium transition-all ${lang === 'en' ? 'bg-card text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}>
                  EN
                </button>
              </div>

              {/* Flow Icons - 智核流水、段位流水、经验流水 */}
              <div className="flex items-center gap-1 pl-2 border-l border-border">
                <button type="button"
                  onClick={() => push('/cores')}
                  className="p-2 text-purple-500 hover:text-purple-600 hover:bg-purple-500/10 rounded-lg transition-all"
                  title={t('智核流水', 'Core Transactions')}
                >
                  <Gem className="size-4" />
                </button>
                <button type="button"
                  onClick={() => push('/tier')}
                  className="p-2 text-amber-500 hover:text-amber-600 hover:bg-amber-500/10 rounded-lg transition-all"
                  title={t('段位流水', 'Tier Transactions')}
                >
                  <Trophy className="size-4" />
                </button>
                <button type="button"
                  onClick={() => push('/xp')}
                  className="p-2 text-blue-500 hover:text-blue-600 hover:bg-blue-500/10 rounded-lg transition-all"
                  title={t('经验流水', 'XP Transactions')}
                >
                  <Zap className="size-4" />
                </button>
                <span className="text-xs text-muted-foreground hidden lg:block ml-2">{user?.username}</span>
                <button type="button" onClick={handleLogout}
                  className="p-2 text-muted-foreground hover:text-red-500 hover:bg-red-500/10 rounded-lg transition-all"
                  title={t('退出登录', 'Logout')}
                  aria-label={t('退出登录', 'Logout')}>
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" x2="9" y1="12" y2="12"/></svg>
                </button>
              </div>
            </div>
          </div>
        </PageContainer>
      </header>

      {/* Main Content */}
      <main className="pt-24 pb-8">
        <PageContainer>
          {/* 问候区 */}
          <section className="mb-12">
            <WelcomeSection
              user={{ id: user?.id || '', username: user?.username || '' }}
              lang={lang}
              streakDays={profile?.streak_days ?? 0}
            />
          </section>

          {/* 统计区 */}
          <section className="mb-12">
            <SectionHeader title={t('今日数据', "Today's Stats")} date={todayDate} />
            <TodayStats
              stats={{
                exercisesToday: todayStats.exercises,
                accuracy: todayStats.accuracy,
                learningMinutes: Math.round(todayStats.time_minutes),
                streakDays: profile?.streak_days ?? 0,
              }}
              trend={trend}
              lang={lang}
              onExercisesClick={() => push('/dashboard/exercises')}
              onAccuracyClick={() => push('/dashboard/accuracy')}
              onTimeClick={() => push('/dashboard/time')}
            />
          </section>

          {/* 中部内容 */}
          <section className="mb-12">
            <ContentGrid>
              <CurrentLearningPanel
                courses={coursesProgress}
                lang={lang}
              />
              <QuickTools
                wrongCount={reviewStats?.wrong_count ?? 0}
                favoritesCount={favoritesCount}
                notesCount={notesCount}
                streakDays={profile?.streak_days ?? 0}
                totalCheckinDays={checkinDetails?.total_checkin_days ?? 0}
                isCheckedIn={isCheckedIn}
                onWrongClick={() => push('/review?type=wrong')}
                onFavoritesClick={() => push('/favorites')}
                onNotesClick={() => push('/notes')}
                onCheckIn={handleCheckIn}
                lang={lang}
                lunarStr={checkinDetails?.lunar_str}
                solarTerm={checkinDetails?.solar_term_str?.split(' (')[0]}
                holiday={checkinDetails?.holiday_str?.split(' (')[0]}
                streakMultiplier={checkinDetails?.streak_multiplier ?? 1.0}
              />
            </ContentGrid>
          </section>

          {/* 底部内容 */}
          <section>
            <ContentGrid>
              <RecentActivity
                activities={activities}
                onStartLearning={() => push('/courses')}
                lang={lang}
              />
              <SolutionBoard lang={lang} />
            </ContentGrid>
          </section>
        </PageContainer>
      </main>
    </div>
  )
}
