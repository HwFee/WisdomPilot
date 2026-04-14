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
  getCourseStages,
  getLeaderboard,
  getReviewStats,
} from '@/lib/api'
import { ActivityFeed } from '@/components/ui/activity-feed'
import {
  Play, Sparkles, Zap, Trophy, Clock, Target,
  ChevronRight, BookOpen, Award, TrendingUp,
  Flame, BarChart3, CheckCircle, Lock,
  Code2, Users, ArrowRight
} from 'lucide-react'
import type { StageWithProgress } from '@/types/stage'
import type { ReviewStatsResponse } from '@/types/review'
import type { UserProfileResponse, UserRankResponse } from '@/types/api'

// Course configuration - 8 courses with gradient colors (matching homepage style)
const COURSES = [
  { id: 1, code: 'C', name: 'C语言程序设计', icon: Code2, gradient: 'from-blue-500 to-cyan-500', color: '#0077B6', description: '编程入门首选，打好扎实基础', learners: '12,580+', difficulty: 1 },
  { id: 2, code: 'CPP', name: 'C++程序设计', icon: Code2, gradient: 'from-indigo-500 to-purple-500', color: '#00599C', description: '面向对象编程，系统开发利器', learners: '8,420+', difficulty: 2 },
  { id: 3, code: 'Python', name: 'Python程序设计', icon: Code2, gradient: 'from-green-500 to-teal-500', color: '#3776AB', description: '简洁优雅，人工智能首选语言', learners: '25,800+', difficulty: 1 },
  { id: 4, code: 'Java', name: 'Java程序设计', icon: Code2, gradient: 'from-orange-500 to-red-500', color: '#ED8B00', description: '企业级开发，跨平台应用', learners: '15,300+', difficulty: 2 },
  { id: 5, code: 'Rust', name: 'Rust程序设计', icon: Code2, gradient: 'from-red-500 to-orange-600', color: '#CE422B', description: '安全高效，系统编程新星', learners: '3,250+', difficulty: 4 },
  { id: 6, code: 'DSA', name: '数据结构与算法', icon: Target, gradient: 'from-emerald-500 to-green-600', color: '#10B981', description: '程序员内功，面试必考', learners: '18,900+', difficulty: 3 },
  { id: 7, code: 'ADA', name: '算法设计与分析', icon: Target, gradient: 'from-violet-500 to-purple-600', color: '#8B5CF6', description: '深入算法，提升编程思维', learners: '6,780+', difficulty: 4 },
  { id: 8, code: 'DiscreteMath', name: '离散数学', icon: BookOpen, gradient: 'from-amber-500 to-yellow-600', color: '#F59E0B', description: '计算机科学数学基础', learners: '4,560+', difficulty: 3 },
]

interface CourseWithProgress {
  id: number
  code: string
  name: string
  icon: React.ComponentType<{ className?: string }>
  gradient: string
  color: string
  description: string
  totalStages: number
  completedStages: number
  progress: number
  learners?: string
  difficulty?: number
}

export default function DashboardPage() {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [profile, setProfile] = useState<UserProfileResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [lang, setLang] = useState<'zh' | 'en'>('zh')
  const hasFetched = useRef(false)
  const isMounted = useRef(true)

  // State for stages, leaderboard, review
  const [coursesWithProgress, setCoursesWithProgress] = useState<CourseWithProgress[]>([])
  const [allInProgressStages, setAllInProgressStages] = useState<StageWithProgress[]>([])
  const [leaderboard, setLeaderboard] = useState<UserRankResponse[]>([])
  const [reviewStats, setReviewStats] = useState<ReviewStatsResponse | null>(null)
  const [activities, setActivities] = useState<Activity[]>([])
  const [stagesLoading, setStagesLoading] = useState(false)

  // Cleanup on unmount
  useEffect(() => {
    isMounted.current = true
    return () => {
      isMounted.current = false
    }
  }, [])

  const fetchData = useCallback(async (token: string) => {
    try {
      // Fetch profile and leaderboard in parallel with error handling
      const [profileResult, leaderboardResult, reviewResult, activitiesResult] = await Promise.allSettled([
        getProfile(token).catch(err => {
          console.error('Profile fetch failed:', err)
          // If 401 (unauthorized), redirect to login
          if (err.message?.includes('401') || err.status === 401) {
            handleAuthError()
          }
          return null
        }),
        getLeaderboard(5, token).catch(err => { console.error('Leaderboard fetch failed:', err); return [] }),
        getReviewStats(token).catch(err => { console.error('Review stats fetch failed:', err); return null }),
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/users/me/activities?limit=10`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }).then(r => {
          if (!r.ok) {
            if (r.status === 401) handleAuthError()
            return { activities: [] }
          }
          return r.json()
        }).catch(() => ({ activities: [] })),
      ])

      if (!isMounted.current) return

      const profileData = profileResult.status === 'fulfilled' ? profileResult.value : null
      const leaderboardData = leaderboardResult.status === 'fulfilled' ? leaderboardResult.value : []
      const reviewData = reviewResult.status === 'fulfilled' ? reviewResult.value : null
      const activitiesData = activitiesResult.status === 'fulfilled' ? activitiesResult.value : { activities: [] }

      setProfile(profileData)
      setLeaderboard(leaderboardData)
      if (reviewData) setReviewStats(reviewData)
      setActivities(activitiesData.activities || [])

      // Fetch all courses progress
      try {
        const coursesProgress = await Promise.all(
          COURSES.map(async (course) => {
            try {
              const stagesData = await getCourseStages(course.id, token)
              const totalStages = stagesData.stages.length
              const completedStages = stagesData.stages.filter((s: StageWithProgress) => s.progress?.status === 'completed').length
              return {
                ...course,
                totalStages,
                completedStages,
                progress: totalStages > 0 ? Math.round((completedStages / totalStages) * 100) : 0
              }
            } catch {
              return { ...course, totalStages: 0, completedStages: 0, progress: 0 }
            }
          })
        )
        setCoursesWithProgress(coursesProgress)
      } catch (err) {
        console.error('Failed to fetch courses progress:', err)
        // Set default courses with 0 progress on failure
        setCoursesWithProgress(COURSES.map(c => ({ ...c, totalStages: 0, completedStages: 0, progress: 0 })))
      }

      // Fetch all in-progress stages across all courses
      const allStages: StageWithProgress[] = []
      for (const course of COURSES) {
        try {
          const stagesData = await getCourseStages(course.id, token)
          const inProgress = stagesData.stages.filter((s: StageWithProgress) => s.progress?.status === 'in_progress')
          allStages.push(...inProgress)
        } catch {
          // ignore
        }
      }
      setAllInProgressStages(allStages)
    } catch {
      if (!isMounted.current) return
    } finally {
      if (!isMounted.current) return
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    if (hasFetched.current) return

    const token = getStoredToken()
    const storedUser = getStoredUser()

    let savedLang = 'zh'
    try {
      savedLang = localStorage.getItem('language') || 'zh'
    } catch {
      // localStorage may throw in private browsing mode
    }

    if (!token || !storedUser) {
      router.push('/login')
      return
    }

    setUser(storedUser)
    setLang(savedLang as 'zh' | 'en')
    hasFetched.current = true
    fetchData(token)
  }, [router, fetchData])

  const handleLogout = () => {
    logout()
    router.push('/login')
  }

  const handleAuthError = () => {
    logout()
    router.push('/login')
  }

  const toggleLanguage = () => {
    const newLang = lang === 'zh' ? 'en' : 'zh'
    setLang(newLang)
    try {
      localStorage.setItem('language', newLang)
    } catch {
      // localStorage may throw in private browsing mode
    }
  }

  const t = (zh: string, en: string) => lang === 'zh' ? zh : en

  // Get stage status icon
  const getStageStatusIcon = (progress?: { status: string }) => {
    if (!progress) return <Lock className="w-4 h-4 text-muted-foreground" />
    if (progress.status === 'completed') return <CheckCircle className="w-4 h-4 text-green-500" />
    if (progress.status === 'in_progress') return <Play className="w-4 h-4 text-blue-500" />
    return <Lock className="w-4 h-4 text-muted-foreground" />
  }

  // Calculate overall stats
  const totalStagesAll = coursesWithProgress.reduce((sum, c) => sum + c.totalStages, 0)
  const completedStagesAll = coursesWithProgress.reduce((sum, c) => sum + c.completedStages, 0)
  const inProgressStages = allInProgressStages.length

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
      {/* Header - Glass Effect */}
      <header className="fixed top-0 left-0 right-0 z-50 glass border-b border-border/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
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

            <div className="flex items-center gap-4">
              {/* Stats Pills */}
              <div className="hidden sm:flex items-center gap-2">
                <div className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-500/10 rounded-full">
                  <Zap className="w-4 h-4 text-blue-500" />
                  <span className="text-sm font-medium text-blue-600 dark:text-blue-400">
                    {profile?.ai_quota ?? 50}
                  </span>
                </div>
                <div className="flex items-center gap-1.5 px-3 py-1.5 bg-yellow-500/10 rounded-full">
                  <Trophy className="w-4 h-4 text-yellow-500" />
                  <span className="text-sm font-medium text-yellow-600 dark:text-yellow-400">
                    {profile?.xp ?? 0}
                  </span>
                </div>
              </div>

              <div className="flex items-center bg-muted rounded-full p-0.5">
                <button
                  onClick={() => { if (lang !== 'zh') toggleLanguage() }}
                  className={`px-2.5 py-1 rounded-full text-xs font-medium transition-all ${
                    lang === 'zh' ? 'bg-card text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  中
                </button>
                <button
                  onClick={() => { if (lang !== 'en') toggleLanguage() }}
                  className={`px-2.5 py-1 rounded-full text-xs font-medium transition-all ${
                    lang === 'en' ? 'bg-card text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  EN
                </button>
              </div>

              <div className="flex items-center gap-2 pl-3 border-l border-border">
                <span className="text-sm text-muted-foreground hidden lg:block">{user?.username}</span>
                <button
                  onClick={handleLogout}
                  className="p-2 text-muted-foreground hover:text-red-500 hover:bg-red-500/10 rounded-lg transition-all"
                  title={t('退出登录', 'Logout')}
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" x2="9" y1="12" y2="12"/></svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-8">
        {/* Welcome Banner */}
        <div className="relative rounded-2xl mb-8 p-6 sm:p-8 overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-r from-primary/10 via-primary/5 to-transparent"></div>
          <div className="absolute top-0 right-0 w-96 h-96 bg-primary/20 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2"></div>

          <div className="relative flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary to-primary-600 flex items-center justify-center shadow-xl shadow-primary/25">
                <Sparkles className="w-7 h-7 text-primary-foreground" />
              </div>
              <div>
                <p className="text-muted-foreground text-sm">{t('欢迎回来，', 'Welcome back,')}<span className="font-semibold text-foreground">{user?.username}</span></p>
                <h2 className="text-xl sm:text-2xl font-bold text-foreground">
                  {t('「不积跬步，无以至千里」', '"Small steps lead to great journeys"')}
                </h2>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="text-center px-4 py-3 bg-gradient-to-br from-orange-500/15 to-orange-500/5 rounded-xl border border-orange-500/20">
                <div className="flex items-center gap-1.5">
                  <Flame className="w-5 h-5 text-orange-500 animate-flame" />
                  <span className="text-2xl font-bold text-orange-600 dark:text-orange-400">{profile?.streak_days ?? 0}</span>
                </div>
                <span className="text-xs text-muted-foreground">{t('连续', 'Streak')}</span>
              </div>
              <div className="text-center px-4 py-3 bg-gradient-to-br from-purple-500/15 to-purple-500/5 rounded-xl border border-purple-500/20">
                <div className="flex items-center gap-1.5">
                  <Award className="w-5 h-5 text-purple-500" />
                  <span className="text-2xl font-bold text-purple-600 dark:text-purple-400">Lv.{profile?.level ?? 1}</span>
                </div>
                <span className="text-xs text-muted-foreground">{t('等级', 'Level')}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="mb-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {/* Courses */}
            <div className="bg-card rounded-2xl p-5 border border-border hover:shadow-lg hover:border-primary/20 transition-all group">
              <div className="w-12 h-12 bg-blue-500/10 rounded-xl flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                <BookOpen className="w-6 h-6 text-blue-500" />
              </div>
              <p className="text-sm text-muted-foreground mb-1">{t('课程', 'Courses')}</p>
              <div className="flex items-baseline gap-1">
                <span className="text-3xl font-bold text-foreground">8</span>
                <span className="text-sm text-muted-foreground">{t('门课程', 'courses')}</span>
              </div>
            </div>
            {/* Completed Stages */}
            <div className="bg-card rounded-2xl p-5 border border-border hover:shadow-lg hover:border-primary/20 transition-all group">
              <div className="w-12 h-12 bg-green-500/10 rounded-xl flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                <Trophy className="w-6 h-6 text-green-500" />
              </div>
              <p className="text-sm text-muted-foreground mb-1">{t('已通关', 'Completed')}</p>
              <div className="flex items-baseline gap-1">
                <span className="text-3xl font-bold text-foreground">{completedStagesAll}</span>
                <span className="text-sm text-muted-foreground">{t('个关卡', 'stages')}</span>
              </div>
            </div>
            {/* In Progress */}
            <div className="bg-card rounded-2xl p-5 border border-border hover:shadow-lg hover:border-primary/20 transition-all group">
              <div className="w-12 h-12 bg-amber-500/10 rounded-xl flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                <Play className="w-6 h-6 text-amber-500" />
              </div>
              <p className="text-sm text-muted-foreground mb-1">{t('进行中', 'In Progress')}</p>
              <div className="flex items-baseline gap-1">
                <span className="text-3xl font-bold text-foreground">{inProgressStages}</span>
                <span className="text-sm text-muted-foreground">{t('个关卡', 'stages')}</span>
              </div>
            </div>
            {/* Learning Time */}
            <div className="bg-card rounded-2xl p-5 border border-border hover:shadow-lg hover:border-primary/20 transition-all group">
              <div className="w-12 h-12 bg-purple-500/10 rounded-xl flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                <Clock className="w-6 h-6 text-purple-500" />
              </div>
              <p className="text-sm text-muted-foreground mb-1">{t('学习时长', 'Learning Time')}</p>
              <span className="text-2xl font-bold text-foreground">{t('暂无数据', 'N/A')}</span>
            </div>
          </div>
        </div>

        {/* Course Selection - Bento Grid (Homepage Style) */}
        <div className="mb-8">
          <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-primary" />
            {t('选择课程', 'Select Course')}
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6">
            {coursesWithProgress.map((course, index) => {
              const IconComponent = course.icon
              return (
                <div
                  key={course.id}
                  onClick={() => router.push(`/courses/${course.id}`)}
                  className={`group relative p-6 rounded-2xl bg-card border border-border hover:border-primary/40 transition-all card-interactive ${
                    index === 0 || index === 5 ? 'sm:col-span-2 lg:col-span-1' : ''
                  }`}
                >
                  {/* Difficulty indicator */}
                  <div className="absolute top-4 right-4 flex gap-1">
                    {[...Array(4)].map((_, i) => (
                      <div
                        key={i}
                        className={`w-1.5 h-1.5 rounded-full ${
                          i < (course.difficulty || 1) ? 'bg-primary' : 'bg-muted'
                        }`}
                      />
                    ))}
                  </div>

                  {/* Icon */}
                  <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${course.gradient} flex items-center justify-center mb-4 shadow-lg group-hover:scale-105 transition-transform`}>
                    <IconComponent className="w-7 h-7 text-white" />
                  </div>

                  {/* Content */}
                  <h4 className="text-lg font-semibold text-foreground mb-2 group-hover:text-primary transition-colors">
                    {course.name}
                  </h4>
                  <p className="text-sm text-muted-foreground mb-4 truncate-2">
                    {course.description}
                  </p>

                  {/* Progress bar */}
                  <div className="mb-3">
                    <div className="flex justify-between text-xs text-muted-foreground mb-1">
                      <span>{t('进度', 'Progress')}</span>
                      <span>{course.progress}%</span>
                    </div>
                    <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-primary to-primary-600 rounded-full transition-all duration-500"
                        style={{ width: `${course.progress}%` }}
                      />
                    </div>
                  </div>

                  {/* Bottom info */}
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Users className="w-3.5 h-3.5" />
                      {course.learners || '0'}
                    </span>
                    <span className="flex items-center gap-1 text-primary opacity-0 group-hover:opacity-100 transition-opacity">
                      {t('开始学习', 'Start')}
                      <ArrowRight className="w-3 h-3" />
                    </span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Main grid */}
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Left column - Continue Learning */}
          <div className="lg:col-span-2">
            <div className="bg-card rounded-2xl border border-border p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="font-semibold text-foreground flex items-center gap-2 text-lg">
                  <Target className="w-5 h-5 text-primary" />
                  {t('继续学习', 'Continue Learning')}
                </h3>
              </div>

              {stagesLoading ? (
                <div className="flex items-center justify-center py-12">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
              ) : allInProgressStages.length === 0 ? (
                <div className="text-center py-12">
                  <div className="w-16 h-16 bg-muted rounded-2xl flex items-center justify-center mx-auto mb-4">
                    <Target className="w-8 h-8 text-muted-foreground" />
                  </div>
                  <p className="text-muted-foreground mb-4">{t('点击上方课程卡片开始学习', 'Click a course above to start learning')}</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {allInProgressStages.slice(0, 6).map((stage) => (
                    <div
                      key={stage.id}
                      onClick={() => router.push(`/stage/${stage.id}`)}
                      className="flex items-center gap-4 p-4 rounded-xl bg-muted/30 hover:bg-muted/50 border border-border/50 hover:border-primary/30 transition-all cursor-pointer group"
                    >
                      <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-blue-500/10">
                        <Play className="w-5 h-5 text-blue-500" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-foreground truncate">{stage.title}</p>
                        <div className="flex items-center gap-3 text-xs text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <Trophy className="w-3 h-3 text-yellow-500" />
                            {stage.xp_reward} XP
                          </span>
                          <span className="flex items-center gap-1">
                            <Zap className="w-3 h-3 text-blue-500" />
                            +{stage.quota_bonus}
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="w-24 h-2 bg-muted rounded-full overflow-hidden">
                          <div
                            className="h-full bg-blue-500 rounded-full"
                            style={{
                              width: `${stage.required_exercises > 0
                                ? Math.min(100, ((stage.progress?.exercises_completed || 0) / stage.required_exercises) * 100)
                                : 0}%`
                            }}
                          />
                        </div>
                      </div>
                      <ChevronRight className="w-5 h-5 text-muted-foreground group-hover:text-primary group-hover:translate-x-1 transition-all" />
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Right sidebar */}
          <div className="flex flex-col space-y-6">
            {/* Review Queue */}
            {reviewStats && reviewStats.total_due > 0 && (
              <div className="bg-gradient-to-br from-orange-500/10 to-orange-500/5 rounded-2xl border border-orange-500/20 p-5">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-foreground flex items-center gap-2">
                    <Clock className="w-5 h-5 text-orange-500" />
                    {t('待复习', 'Review Due')}
                  </h3>
                  <span className="px-2.5 py-1 bg-orange-500/20 text-orange-500 text-sm font-bold rounded-lg">
                    {reviewStats.total_due}
                  </span>
                </div>
                <button
                  onClick={() => router.push('/review')}
                  className="w-full flex items-center justify-center gap-2 py-3 bg-orange-500 text-white rounded-xl font-medium hover:bg-orange-600 transition-colors"
                >
                  <BarChart3 className="w-4 h-4" />
                  {t('开始复习', 'Start Review')}
                </button>
              </div>
            )}

            {/* Leaderboard */}
            <div className="bg-card rounded-2xl border border-border p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-foreground flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-yellow-500" />
                  {t('排行榜', 'Leaderboard')}
                </h3>
                <button
                  onClick={() => router.push('/leaderboard')}
                  className="text-xs text-primary hover:text-primary/80 transition-colors"
                >
                  {t('查看全部', 'View All')}
                </button>
              </div>
              <div className="space-y-2">
                {leaderboard.slice(0, 5).map((player, idx) => (
                  <div
                    key={player.user_id}
                    className={`flex items-center gap-3 p-2 rounded-xl ${
                      player.user_id === user?.id ? 'bg-primary/10' : 'hover:bg-muted/50'
                    } transition-colors`}
                  >
                    <span className={`w-7 h-7 flex items-center justify-center rounded-lg text-xs font-bold ${
                      idx === 0 ? 'bg-yellow-500 text-white' :
                      idx === 1 ? 'bg-gray-400 text-white' :
                      idx === 2 ? 'bg-amber-600 text-white' :
                      'bg-muted text-muted-foreground'
                    }`}>
                      {idx + 1}
                    </span>
                    <span className="flex-1 text-sm font-medium text-foreground truncate">
                      {player.username}
                    </span>
                    <span className="text-sm text-muted-foreground font-medium">
                      {player.xp}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Recent Activity */}
            <div className="bg-card rounded-2xl border border-border p-5">
              <h3 className="font-semibold text-foreground mb-4">{t('最近动态', 'Recent Activity')}</h3>
              <div className="max-h-48 overflow-auto">
                {activities.length > 0 ? (
                  <ActivityFeed
                    activities={activities}
                    lang={lang}
                    isLoading={false}
                  />
                ) : (
                  <div className="text-center py-6 text-muted-foreground">
                    <Play className="w-10 h-10 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">{t('暂无学习记录', 'No activity yet')}</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
