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
  getCheckinStats,
  getFavoritesCount,
  getNotesCount,
  getMasteryLeaderboard,
  getArenaLeaderboard,
  getUserCourseProgress,
  getTodayStats,
  getMasteryOverview,
  getLearningStatistics,
  CourseProgress,
  TodayStatsResponse,
  API_BASE_URL,
} from '@/lib/api'
import {
  Sparkles, Zap, Trophy, Clock, Target, Star,
  BookOpen, Code2, Swords, Gem,
} from 'lucide-react'
import type { ReviewStatsResponse } from '@/types/review'
import type { UserProfileResponse, LeaderboardEntry, CheckinDetailsResponse, CheckinStatsResponse, Tier } from '@/types/api'
import { getRecentArenaExercises, RecentArenaExercise, TIER_NAMES } from '@/lib/api/learning-path'
import { getTierConfig } from '@/lib/icons/tier-icons'
import { Logo } from '@/components/ui/logo'

// Dashboard components
import { WelcomeSection } from './WelcomeSection'
import { TodayStats } from './TodayStats'
import { SolutionBoard } from './SolutionBoard'
import { QuickTools } from './QuickTools'
import { RecentActivity } from './RecentActivity'
import { CurrentLearningPanel } from './CurrentLearningPanel'

interface KnowledgePoint {
  name: string
  mastery: number
  courseId?: number
}

// 最近练习记录接口（挑战之路）
interface RecentExercise {
  stageName: string
  isCorrect: boolean
  time?: string
}

// 最近学习信息接口
interface RecentLearning {
  lastStageName?: string
  lastExerciseTitle?: string
  lastLearnTime?: string
}

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
  const [currentCourseId, setCurrentCourseId] = useState<number | null>(null)

  const [reviewStats, setReviewStats] = useState<ReviewStatsResponse | null>(null)
  const [activities, setActivities] = useState<Activity[]>([])
  const [isCheckedIn, setIsCheckedIn] = useState(false)
  const [favoritesCount, setFavoritesCount] = useState(0)
  const [notesCount, setNotesCount] = useState(0)

  // Enhanced check-in details state
  const [checkinDetails, setCheckinDetails] = useState<CheckinDetailsResponse | null>(null)
  const [checkinStats, setCheckinStats] = useState<CheckinStatsResponse | null>(null)

  // Dual leaderboard state (for current course)
  const [masteryLeaderboard, setMasteryLeaderboard] = useState<LeaderboardEntry[]>([])
  const [arenaLeaderboard, setArenaLeaderboard] = useState<LeaderboardEntry[]>([])
  const [userMasteryRank, setUserMasteryRank] = useState<number | null>(null)
  const [userArenaRank, setUserArenaRank] = useState<number | null>(null)

  // Today stats - now from real API
  const [todayStats, setTodayStats] = useState<TodayStatsResponse>({
    exercises: 0,
    correct: 0,
    accuracy: 0,
    time_minutes: 0,
  })

  // Knowledge points - now from real API
  const knowledgePointsRef = useRef<KnowledgePoint[]>([])

  // 最近学习信息
  const [recentLearning, setRecentLearning] = useState<RecentLearning | null>(null)

  // 最近练习记录（用于精进之路卡片显示）
  const [recentExercises, setRecentExercises] = useState<RecentExercise[]>([])

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

      // Load saved course from localStorage or set default
      const savedCourseId = localStorage.getItem('currentCourseId')
      let initialCourseId: number | null = null

      if (savedCourseId) {
        // Check if saved course exists in the list
        const savedCourse = courseProgressData.courses.find((c: CourseProgress) => c.course_id === parseInt(savedCourseId))
        if (savedCourse) {
          initialCourseId = savedCourse.course_id
        }
      }

      // If no saved course or saved course not found, use first course
      if (!initialCourseId && courseProgressData.courses.length > 0) {
        initialCourseId = courseProgressData.courses[0].course_id
        // Save to localStorage
        localStorage.setItem('currentCourseId', String(initialCourseId))
      }

      setCurrentCourseId(initialCourseId)

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

      // Get checkin stats (with next tier info)
      try {
        const stats = await getCheckinStats(token)
        setCheckinStats(stats)
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

  // Fetch leaderboards when current course changes
  const fetchLeaderboards = useCallback(async (courseId: number, token: string) => {
    try {
      const [masteryData, arenaData] = await Promise.all([
        getMasteryLeaderboard(courseId, token, 5).catch(() => null),
        getArenaLeaderboard(courseId, token, 5).catch(() => null),
      ])
      if (masteryData) {
        setMasteryLeaderboard(masteryData.entries)
        setUserMasteryRank(masteryData.user_rank)
      }
      if (arenaData) {
        setArenaLeaderboard(arenaData.entries)
        setUserArenaRank(arenaData.user_rank)
      }
    } catch { /* ignore */ }
  }, [])

  // Fetch recent arena exercises for challenge path
  const fetchRecentArenaExercises = useCallback(async (token: string) => {
    try {
      const recentExercises = await getRecentArenaExercises(token, 3)
      // 转换为组件需要的格式
      const formatted: RecentExercise[] = recentExercises.map(ex => ({
        stageName: ex.title,
        isCorrect: ex.is_correct,
      }))
      setRecentExercises(formatted)
    } catch {
      setRecentExercises([])
    }
  }, [])

  // Fetch knowledge points for current course
  const fetchKnowledgePoints = useCallback(async (courseId: number, token: string) => {
    try {
      const masteryData = await getMasteryOverview(courseId, token)
      if (masteryData.chapters && masteryData.chapters.length > 0) {
        // Convert chapter mastery to knowledge points
        const kps = masteryData.chapters.slice(0, 5).map(ch => ({
          name: ch.title || `章节 ${ch.chapter_id}`,
          mastery: ch.mastery_score || 0,
          courseId: courseId,
        }))
        knowledgePointsRef.current = kps
      } else {
        knowledgePointsRef.current = []
      }
    } catch {
      knowledgePointsRef.current = []
    }
  }, [])

  // Refs to avoid effect re-subscription
  const fetchDataRef = useRef(fetchData)
  fetchDataRef.current = fetchData
  const fetchLeaderboardsRef = useRef(fetchLeaderboards)
  fetchLeaderboardsRef.current = fetchLeaderboards
  const fetchKnowledgePointsRef = useRef(fetchKnowledgePoints)
  fetchKnowledgePointsRef.current = fetchKnowledgePoints
  const fetchRecentArenaExercisesRef = useRef(fetchRecentArenaExercises)
  fetchRecentArenaExercisesRef.current = fetchRecentArenaExercises
  const currentCourseIdRef = useRef(currentCourseId)
  currentCourseIdRef.current = currentCourseId

  // Fetch leaderboards and knowledge when course changes
  useEffect(() => {
    const token = getStoredToken()
    if (currentCourseId && token) {
      fetchLeaderboards(currentCourseId, token)
      fetchKnowledgePoints(currentCourseId, token)
      fetchRecentArenaExercises(token)
    }
  }, [currentCourseId, fetchLeaderboards, fetchKnowledgePoints, fetchRecentArenaExercises])

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
        // 同时刷新排行榜、知识点和最近练习
        if (currentCourseIdRef.current) {
          fetchLeaderboardsRef.current(currentCourseIdRef.current, token)
          fetchKnowledgePointsRef.current(currentCourseIdRef.current, token)
          fetchRecentArenaExercisesRef.current(token)
        }
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
          if (currentCourseIdRef.current) {
            fetchLeaderboardsRef.current(currentCourseIdRef.current, token)
            fetchKnowledgePointsRef.current(currentCourseIdRef.current, token)
            fetchRecentArenaExercisesRef.current(token)
          }
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

  // Get current course for welcome section
  const currentCourse = coursesProgress.find(c => c.course_id === currentCourseId)

  // Handle continue learning
  const handleContinueLearning = () => {
    if (currentCourseId) {
      push(`/courses/${currentCourseId}`)
    } else {
      push('/courses')
    }
  }

  // Handle course switch - persist to localStorage
  const handleSwitchCourse = (courseId: number) => {
    setCurrentCourseId(courseId)
    localStorage.setItem('currentCourseId', String(courseId))
  }

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

      // Update checkin stats (next tier days etc.)
      if (checkinStats) {
        // Recalculate next_tier_days based on new streak
        let next_tier: number | null = null
        if (result.streak_days < 7) {
          next_tier = 7 - result.streak_days
        } else if (result.streak_days < 14) {
          next_tier = 14 - result.streak_days
        } else if (result.streak_days < 30) {
          next_tier = 30 - result.streak_days
        } else if (result.streak_days < 100) {
          next_tier = 100 - result.streak_days
        }
        setCheckinStats(prev => prev ? ({
          ...prev,
          streak_days: result.streak_days,
          total_checkin_days: result.total_checkin_days,
          streak_multiplier: result.streak_multiplier,
          checked_in_today: true,
          next_tier_days: next_tier,
        }) : prev)
      }
    } catch (error) {
      console.error('Check-in failed:', error)
      // Handle error silently but log it
    }
  }

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
        <div className="max-w-[1280px] mx-auto px-4 sm:px-6">
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
                  title={t('退出登录', 'Logout')}>
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" x2="9" y1="12" y2="12"/></svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content - max-width 1280px, centered, responsive padding */}
      <main className="max-w-[1280px] mx-auto px-4 sm:px-6 pt-24 pb-8">
        {/* 第1行：问候语（简化版） */}
        <section className="mb-4">
          <WelcomeSection
            user={{ id: user?.id || '', username: user?.username || '' }}
            lang={lang}
          />
        </section>

        {/* 第2行：高频功能区（4模块横向并排） */}
        <section className="mb-4">
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
        </section>

        {/* 第3行：数据概览卡（4卡片等宽等高） */}
        <section className="mb-4">
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

        {/* 第4行：核心内容双栏区（左右高度对齐） */}
        <section className="mb-4">
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
            {/* 左栏 60%：正在学习 + 双排行榜 */}
            <div className="lg:col-span-3 flex flex-col gap-6 lg:h-[500px]">
              {/* 正在学习 - 新的双路径卡片 */}
              <div className="flex-[6] min-h-0">
                <CurrentLearningPanel
                  courses={coursesProgress}
                  lang={lang}
                />
              </div>
              {/* 双排行榜预览 - 占40%高度 */}
              <div className="flex-[4] min-h-0">
                <DualLeaderboardPreview
                  masteryEntries={masteryLeaderboard}
                  arenaEntries={arenaLeaderboard}
                  userMasteryRank={userMasteryRank}
                  userArenaRank={userArenaRank}
                  currentUserId={user?.id}
                  onViewAll={() => push('/leaderboard')}
                  lang={lang}
                />
              </div>
            </div>

            {/* 右栏 40%：题解广场 + 最近动态 */}
            <div className="lg:col-span-2 flex flex-col gap-6 lg:h-[500px]">
              {/* 题解广场 */}
              <div className="flex-1 min-h-0">
                <SolutionBoard
                  lang={lang}
                />
              </div>
              {/* 最近动态 */}
              <div>
                <RecentActivity
                  activities={activities}
                  onStartLearning={() => push('/courses')}
                  lang={lang}
                  compact
                />
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}

// Dual Leaderboard Preview Component
function DualLeaderboardPreview({
  masteryEntries,
  arenaEntries,
  userMasteryRank,
  userArenaRank,
  currentUserId,
  onViewAll,
  lang = 'zh',
}: {
  masteryEntries: LeaderboardEntry[]
  arenaEntries: LeaderboardEntry[]
  userMasteryRank: number | null
  userArenaRank: number | null
  currentUserId?: string
  onViewAll?: () => void
  lang?: 'zh' | 'en'
}) {
  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)
  const [activeTab, setActiveTab] = useState<'mastery' | 'arena'>('mastery')

  const entries = activeTab === 'mastery' ? masteryEntries : arenaEntries
  const userRank = activeTab === 'mastery' ? userMasteryRank : userArenaRank

  const getRankStyle = (rank: number) => {
    if (rank === 1) return 'text-yellow-500'
    if (rank === 2) return 'text-gray-400'
    if (rank === 3) return 'text-amber-600'
    return 'text-muted-foreground'
  }

  return (
    <div className="bg-card rounded-2xl border border-border p-4 h-full flex flex-col">
      {/* Tabs */}
      <div className="flex gap-2 mb-3 flex-shrink-0">
        <button type="button"
          onClick={() => setActiveTab('mastery')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
            activeTab === 'mastery'
              ? 'bg-amber-500/20 text-amber-600 dark:text-amber-400'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          <Trophy className="size-3.5" />
          {t('精进榜', 'Mastery')}
        </button>
        <button type="button"
          onClick={() => setActiveTab('arena')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
            activeTab === 'arena'
              ? 'bg-blue-500/20 text-blue-600 dark:text-blue-400'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          <Swords className="size-3.5" />
          {t('竞技榜', 'Arena')}
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto">
        {entries.length === 0 ? (
          <div className="text-center py-4 text-muted-foreground text-sm">
            {t('暂无排名数据', 'No ranking data')}
          </div>
        ) : (
          <div className="flex flex-col gap-y-1.5">
            {entries.slice(0, 5).map((entry) => (
              <div
                key={entry.user_id}
                className={`flex items-center gap-2 p-2 rounded-lg transition-colors ${
                  entry.user_id === currentUserId
                    ? 'bg-primary/10 border border-primary/30'
                    : 'hover:bg-muted/50'
                }`}
              >
                <span className={`size-5 flex items-center justify-center text-xs font-bold ${getRankStyle(entry.rank)}`}>
                  {entry.rank}
                </span>
                <div className="size-6 rounded-full bg-gradient-to-br from-primary to-primary-600 flex items-center justify-center text-primary-foreground text-xs font-medium">
                  {entry.username.charAt(0)}
                </div>
                <span className="flex-1 text-sm text-foreground truncate">
                  {entry.username}
                  {entry.user_id === currentUserId && (
                    <span className="text-xs text-primary ml-1">({t('你', 'You')})</span>
                  )}
                </span>
                {activeTab === 'mastery' ? (
                  <span className="text-sm font-medium text-foreground">
                    {entry.mastery_xp ?? 0}
                  </span>
                ) : (
                  <div className="flex items-center gap-1 text-sm flex-shrink-0">
                    <span className="size-4 flex items-center justify-center">
                      {getTierConfig(entry.tier as string)?.icon}
                    </span>
                    <span className="font-medium">{TIER_NAMES[entry.tier as Tier] || entry.tier}</span>
                    {entry.sub_tier && (
                      <span>{['I','II','III','IV','V'][entry.sub_tier - 1]}</span>
                    )}
                    <span className="ml-1 flex items-center gap-0.5">
                      <Star className="size-3 text-amber-500 fill-amber-500" />
                      {entry.stars ?? 0}
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* User rank & View all */}
      <div className="flex items-center justify-between mt-3 pt-3 border-t border-border flex-shrink-0">
        {userRank && userRank > 5 ? (
          <span className="text-xs text-muted-foreground">
            {t('你的排名', 'Your rank')}: <span className="font-bold text-primary">#{userRank}</span>
          </span>
        ) : (
          <span className="text-xs text-muted-foreground">
            {activeTab === 'mastery' ? t('精进经验排名', 'Mastery XP ranking') : t('挑战之星排名', 'Challenge stars ranking')}
          </span>
        )}
        {onViewAll && (
          <button type="button"
            onClick={onViewAll}
            className="text-xs text-primary hover:text-primary/80 transition-colors"
          >
            {t('查看全部', 'View all')} →
          </button>
        )}
      </div>
    </div>
  )
}
