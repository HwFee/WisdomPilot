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
} from '@/lib/api'
import {
  Sparkles, Zap, Trophy, Clock, Target,
  BookOpen, Code2, Swords,
} from 'lucide-react'
import type { ReviewStatsResponse } from '@/types/review'
import type { UserProfileResponse, LeaderboardEntry } from '@/types/api'

// Dashboard components
import { WelcomeSection } from './WelcomeSection'
import { TodayStats } from './TodayStats'
import { KnowledgeMastery } from './KnowledgeMastery'
import { QuickTools } from './QuickTools'
import { RecentActivity } from './RecentActivity'
import { CurrentLearningPanel } from './CurrentLearningPanel'

interface KnowledgePoint {
  name: string
  mastery: number
  courseId?: number
}

// 最近练习记录接口
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
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [profile, setProfile] = useState<UserProfileResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [lang, setLang] = useState<'zh' | 'en'>('zh')
  const hasFetched = useRef(false)
  const isMounted = useRef(true)

  // Course progress state
  const [coursesProgress, setCoursesProgress] = useState<CourseProgress[]>([])
  const [currentCourseId, setCurrentCourseId] = useState<number | null>(null)

  const [reviewStats, setReviewStats] = useState<ReviewStatsResponse | null>(null)
  const [activities, setActivities] = useState<Activity[]>([])
  const [isCheckedIn, setIsCheckedIn] = useState(false)
  const [favoritesCount, setFavoritesCount] = useState(0)
  const [notesCount, setNotesCount] = useState(0)

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
  const [knowledgePoints, setKnowledgePoints] = useState<KnowledgePoint[]>([])

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

  useEffect(() => {
    isMounted.current = true
    return () => { isMounted.current = false }
  }, [])

  const fetchData = useCallback(async (token: string) => {
    try {
      // Fetch user course progress (new API)
      const courseProgressData = await getUserCourseProgress(token)
      if (!isMounted.current) return
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
      if (!isMounted.current) return
      setProfile(profileResult)

      // Fetch review stats
      const reviewResult = await getReviewStats(token).catch(() => null)
      if (reviewResult) setReviewStats(reviewResult)

      // Fetch activities
      const activitiesResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/users/me/activities?limit=10`, {
        headers: { 'Authorization': `Bearer ${token}` }
      }).then(r => r.ok ? r.json() : { activities: [] }).catch(() => ({ activities: [] }))
      if (!isMounted.current) return
      setActivities(activitiesResponse.activities || [])

      // Check checkin status
      try {
        const checkinStatus = await getCheckinStatus(token)
        setIsCheckedIn(checkinStatus.checked_in_today)
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

      // 从活动记录中提取最近练习记录（用于精进之路卡片显示）
      if (activitiesResponse.activities && activitiesResponse.activities.length > 0) {
        // 提取最近练习记录
        const exerciseActivities = activitiesResponse.activities
          .filter((a: any) => a.type === 'exercise_complete' || a.activity_type === 'exercise_complete')
          .slice(0, 5) // 取最近5条

        const recentExList: RecentExercise[] = exerciseActivities.map((a: any) => {
          const details = a.details || a.extra_data || {}
          return {
            // 优先显示具体练习题名称，其次显示关卡名称
            stageName: details.exercise_title || details.stage_name || '练习',
            isCorrect: details.is_correct === true,
            time: a.timestamp || a.created_at,
          }
        })
        setRecentExercises(recentExList)
      } else {
        setRecentExercises([])
      }

    } catch { /* ignore */ }
    finally { if (!isMounted.current) return; setIsLoading(false) }
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
        setKnowledgePoints(kps)
      } else {
        setKnowledgePoints([])
      }
    } catch {
      setKnowledgePoints([])
    }
  }, [])

  // Fetch leaderboards and knowledge when course changes
  useEffect(() => {
    const token = getStoredToken()
    if (currentCourseId && token) {
      fetchLeaderboards(currentCourseId, token)
      fetchKnowledgePoints(currentCourseId, token)
    }
  }, [currentCourseId, fetchLeaderboards, fetchKnowledgePoints])

  useEffect(() => {
    if (hasFetched.current) return
    const token = getStoredToken()
    const storedUser = getStoredUser()
    let savedLang = 'zh'
    try { savedLang = localStorage.getItem('language') || 'zh' } catch { /* ignore */ }
    if (!token || !storedUser) { router.push('/login'); return }
    setUser(storedUser)
    setLang(savedLang as 'zh' | 'en')
    hasFetched.current = true
    fetchData(token)
  }, [router, fetchData])

  // 监听仪表盘刷新事件
  useEffect(() => {
    const handleRefresh = () => {
      console.log('Dashboard refresh event received')
      const token = getStoredToken()
      if (token) {
        fetchData(token)
        // 同时刷新排行榜和知识点
        if (currentCourseId) {
          fetchLeaderboards(currentCourseId, token)
          fetchKnowledgePoints(currentCourseId, token)
        }
      }
    }

    window.addEventListener(DASHBOARD_REFRESH_EVENT, handleRefresh)
    return () => window.removeEventListener(DASHBOARD_REFRESH_EVENT, handleRefresh)
  }, [fetchData, currentCourseId, fetchLeaderboards, fetchKnowledgePoints])

  // 保底机制：页面可见时刷新数据（用户返回仪表盘时）
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        console.log('Page became visible, refreshing data...')
        const token = getStoredToken()
        if (token) {
          fetchData(token)
          if (currentCourseId) {
            fetchLeaderboards(currentCourseId, token)
            fetchKnowledgePoints(currentCourseId, token)
          }
        }
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
  }, [fetchData, currentCourseId, fetchLeaderboards, fetchKnowledgePoints])

  const handleLogout = () => { logout(); router.push('/login') }

  const toggleLanguage = () => {
    const newLang = lang === 'zh' ? 'en' : 'zh'
    setLang(newLang)
    try { localStorage.setItem('language', newLang) } catch { /* ignore */ }
  }

  const t = (zh: string, en: string) => lang === 'zh' ? zh : en

  // Get current course for welcome section
  const currentCourse = coursesProgress.find(c => c.course_id === currentCourseId)

  // Handle continue learning - go directly to mastery
  const handleContinueLearning = () => {
    if (currentCourseId) {
      router.push(`/mastery/${currentCourseId}`)
    } else {
      router.push('/courses')
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
      console.log('Attempting check-in...')
      const result = await checkin(token)
      console.log('Check-in result:', result)
      setIsCheckedIn(true)
      // Update streak days
      if (profile) {
        setProfile({ ...profile, streak_days: result.streak_days })
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
          <div className="w-16 h-16 bg-primary/10 rounded-2xl flex items-center justify-center mx-auto mb-4 animate-pulse">
            <Sparkles className="w-8 h-8 text-primary" />
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
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-primary-600 flex items-center justify-center shadow-lg shadow-primary/25">
                <Sparkles className="w-5 h-5 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-base font-bold text-foreground">GAI 编程教学平台</h1>
                <p className="text-xs text-muted-foreground hidden sm:block">{t('基于生成式AI的实践教学系统', 'AI-Powered Learning')}</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="hidden sm:flex items-center gap-2">
                <div className="flex items-center gap-1.5 px-2.5 py-1 bg-blue-500/10 rounded-full">
                  <Zap className="w-3.5 h-3.5 text-blue-500" />
                  <span className="text-xs font-medium text-blue-600 dark:text-blue-400">{profile?.ai_quota ?? 50}</span>
                </div>
                <div className="flex items-center gap-1.5 px-2.5 py-1 bg-yellow-500/10 rounded-full">
                  <Trophy className="w-3.5 h-3.5 text-yellow-500" />
                  <span className="text-xs font-medium text-yellow-600 dark:text-yellow-400">{profile?.xp ?? 0} XP</span>
                </div>
              </div>

              <div className="flex items-center bg-muted rounded-full p-0.5">
                <button onClick={() => { if (lang !== 'zh') toggleLanguage() }}
                  className={`px-2 py-0.5 rounded-full text-xs font-medium transition-all ${lang === 'zh' ? 'bg-card text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}>
                  中
                </button>
                <button onClick={() => { if (lang !== 'en') toggleLanguage() }}
                  className={`px-2 py-0.5 rounded-full text-xs font-medium transition-all ${lang === 'en' ? 'bg-card text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}>
                  EN
                </button>
              </div>

              <div className="flex items-center gap-2 pl-2 border-l border-border">
                <span className="text-xs text-muted-foreground hidden lg:block">{user?.username}</span>
                <button onClick={handleLogout}
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
        {/* 第1行：问候语 + 继续学习大按钮 */}
        <section className="mb-6">
          <WelcomeSection
            user={{ id: user?.id || '', username: user?.username || '' }}
            lastProgress={currentCourse ? {
              courseName: currentCourse.course_name,
              chapterName: currentCourse.current_chapter || '',
            } : null}
            onContinueLearning={handleContinueLearning}
            lang={lang}
          />
        </section>

        {/* 第2行：高频功能区（4模块横向并排） */}
        <section className="mb-6">
          <QuickTools
            wrongCount={reviewStats?.wrong_count ?? 0}
            favoritesCount={favoritesCount}
            notesCount={notesCount}
            streakDays={profile?.streak_days ?? 0}
            isCheckedIn={isCheckedIn}
            onWrongClick={() => router.push('/review?type=wrong')}
            onFavoritesClick={() => router.push('/favorites')}
            onNotesClick={() => router.push('/notes')}
            onCheckIn={handleCheckIn}
            lang={lang}
          />
        </section>

        {/* 第3行：数据概览卡（4卡片等宽等高） */}
        <section className="mb-6">
          <TodayStats
            stats={{
              exercisesToday: todayStats.exercises,
              accuracy: todayStats.accuracy,
              learningMinutes: Math.round(todayStats.time_minutes),
              streakDays: profile?.streak_days ?? 0,
            }}
            trend={trend}
            lang={lang}
            onExercisesClick={() => router.push('/dashboard/exercises')}
            onAccuracyClick={() => router.push('/dashboard/accuracy')}
            onTimeClick={() => router.push('/dashboard/time')}
          />
        </section>

        {/* 第4行：核心内容双栏区（左右高度对齐） */}
        <section className="mb-6">
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
            {/* 左栏 60%：正在学习 + 双排行榜 */}
            <div className="lg:col-span-3 flex flex-col gap-6" style={{ minHeight: '500px' }}>
              {/* 正在学习 - 新的双路径卡片 */}
              <div className="flex-[6] min-h-0">
                <CurrentLearningPanel
                  courses={coursesProgress}
                  currentCourseId={currentCourseId}
                  onSwitchCourse={handleSwitchCourse}
                  recentExercises={recentExercises}
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
                  onViewAll={() => router.push('/leaderboard')}
                  lang={lang}
                />
              </div>
            </div>

            {/* 右栏 40%：知识掌握度 + 最近动态 */}
            <div className="lg:col-span-2 flex flex-col gap-6" style={{ minHeight: '500px' }}>
              {/* 知识掌握度 - 占60%高度 */}
              <div className="flex-[6] min-h-0">
                <KnowledgeMastery
                  courseName={currentCourse?.course_name || 'C语言'}
                  knowledgePoints={knowledgePoints}
                  onLearnClick={(courseId) => router.push(`/mastery/${courseId || currentCourseId || 1}`)}
                  lang={lang}
                  compact
                />
              </div>
              {/* 最近动态 - 占40%高度 */}
              <div className="flex-[4] min-h-0">
                <RecentActivity
                  activities={activities}
                  onStartLearning={() => router.push('/courses')}
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
        <button
          onClick={() => setActiveTab('mastery')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
            activeTab === 'mastery'
              ? 'bg-amber-500/20 text-amber-600 dark:text-amber-400'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          <Trophy className="w-3.5 h-3.5" />
          {t('精进榜', 'Mastery')}
        </button>
        <button
          onClick={() => setActiveTab('arena')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
            activeTab === 'arena'
              ? 'bg-blue-500/20 text-blue-600 dark:text-blue-400'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          <Swords className="w-3.5 h-3.5" />
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
          <div className="space-y-1.5">
            {entries.slice(0, 5).map((entry) => (
              <div
                key={entry.user_id}
                className={`flex items-center gap-2 p-2 rounded-lg transition-colors ${
                  entry.user_id === currentUserId
                    ? 'bg-primary/10 border border-primary/30'
                    : 'hover:bg-muted/50'
                }`}
              >
                <span className={`w-5 h-5 flex items-center justify-center text-xs font-bold ${getRankStyle(entry.rank)}`}>
                  {entry.rank}
                </span>
                <div className="w-6 h-6 rounded-full bg-gradient-to-br from-primary to-primary-600 flex items-center justify-center text-primary-foreground text-xs font-medium">
                  {entry.username.charAt(0)}
                </div>
                <span className="flex-1 text-sm text-foreground truncate">
                  {entry.username}
                  {entry.user_id === currentUserId && (
                    <span className="text-xs text-primary ml-1">({t('你', 'You')})</span>
                  )}
                </span>
                <span className="text-sm font-medium text-foreground">
                  {activeTab === 'mastery'
                    ? entry.total_mastery?.toFixed(0)
                    : entry.total_score?.toFixed(0)}
                </span>
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
            {activeTab === 'mastery' ? t('章节掌握排名', 'Chapter mastery ranking') : t('挑战积分排名', 'Challenge score ranking')}
          </span>
        )}
        {onViewAll && (
          <button
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
