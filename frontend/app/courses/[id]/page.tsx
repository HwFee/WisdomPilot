'use client'

import { useParams, useRouter } from 'next/navigation'
import { useEffect, useState, useCallback } from 'react'
import Link from 'next/link'
import { ArrowLeft, BookOpen, Trophy, Clock, Target } from 'lucide-react'
import { LearningPathSelector } from '@/components/course/LearningPathSelector'
import { ChapterTimeline } from '@/components/course/ChapterTimeline'
import { getMasteryOverview, getArenaProfile, getStoredToken, logout } from '@/lib/api'
import type { Tier, MasteryLevel } from '@/types/api'

interface Stage {
  id: number
  title: string
  description: string
  order_index: number
  difficulty_level: number
  xp_reward: number
  quota_bonus: number
  required_exercises: number
  course_id?: number
  progress?: {
    status: string
    exercises_completed: number
    accuracy: number
  }
}

interface Course {
  id: number
  code: string
  name: string
  description: string
  difficulty_level: number
  stages: Stage[]
}

// 课程配置
const COURSE_CONFIG: Record<string, { gradient: string; icon: string; color: string }> = {
  'C': { gradient: 'from-blue-500 to-cyan-500', icon: 'C', color: 'text-blue-500' },
  'CPP': { gradient: 'from-indigo-500 to-purple-500', icon: 'C++', color: 'text-indigo-500' },
  'Python': { gradient: 'from-green-500 to-teal-500', icon: 'Py', color: 'text-green-500' },
  'Java': { gradient: 'from-orange-500 to-red-500', icon: 'J', color: 'text-orange-500' },
  'Rust': { gradient: 'from-red-500 to-orange-600', icon: 'Rs', color: 'text-red-500' },
  'DSA': { gradient: 'from-purple-500 to-pink-500', icon: 'DS', color: 'text-purple-500' },
  'ADA': { gradient: 'from-pink-500 to-rose-500', icon: 'AD', color: 'text-pink-500' },
  'DiscreteMath': { gradient: 'from-teal-500 to-cyan-500', icon: 'DM', color: 'text-teal-500' },
}

export default function CoursePage() {
  const params = useParams()
  const router = useRouter()
  const courseId = Number(params.id)

  const [course, setCourse] = useState<Course | null>(null)
  const [loading, setLoading] = useState(true)

  // Mastery progress state
  const [masteryProgress, setMasteryProgress] = useState<{
    currentChapter: string
    completedChapters: number
    totalChapters: number
    masteryPoints: number
    avgMastery: number
    currentMasteryLevel: MasteryLevel
  } | undefined>(undefined)

  // Arena progress state
  const [arenaProgress, setArenaProgress] = useState<{
    tier: Tier
    score: number
    highestDifficulty: number
    totalChallenges: number
    wins: number
  } | undefined>(undefined)

  const fetchCourse = useCallback(async () => {
    const token = getStoredToken()
    if (!token) {
      logout()
      router.push('/login')
      return
    }

    try {
      // Fetch course details
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/courses/${courseId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (response.ok) {
        const data = await response.json()
        setCourse(data.course)

        // Fetch stages
        try {
          const stagesResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/stages/course/${courseId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
          })

          if (stagesResponse.ok) {
            const stagesData = await stagesResponse.json()
            setCourse(prev => prev ? { ...prev, stages: stagesData.stages || [] } : null)
          } else {
            console.error('Failed to fetch stages:', stagesResponse.status)
          }
        } catch (stagesError) {
          console.error('Error fetching stages:', stagesError)
        }
      }
    } catch (error) {
      console.error('Failed to fetch course:', error)
    }

    // Fetch mastery overview separately (non-blocking)
    const masteryPromise = getMasteryOverview(courseId, token)
      .then(masteryData => {
        setMasteryProgress({
          currentChapter: masteryData.current_chapter || '第一章',
          completedChapters: masteryData.completed_chapters || masteryData.mastered_chapters || 0,
          totalChapters: masteryData.total_chapters || 1,
          masteryPoints: masteryData.total_mastery_score ?? 0,
          avgMastery: masteryData.avg_mastery ?? 0,
          currentMasteryLevel: (masteryData.current_mastery_level || '入门') as MasteryLevel,
        })
      })
      .catch(() => {
        // Mastery data not available yet - silently ignore
      })

    // Fetch arena profile separately (non-blocking)
    const arenaPromise = getArenaProfile(courseId, token)
      .then(arenaData => {
        setArenaProgress({
          tier: (arenaData.tier || 'bronze') as Tier,
          score: arenaData.total_score ?? 0,
          highestDifficulty: arenaData.highest_difficulty ?? 0,
          totalChallenges: arenaData.total_challenges ?? 0,
          wins: arenaData.wins ?? 0,
        })
      })
      .catch(() => {
        // Arena data not available yet - silently ignore
      })

    // Don't wait for mastery/arena data - set loading to false immediately after core data
    setLoading(false)

    // Let mastery/arena load in background
    Promise.allSettled([masteryPromise, arenaPromise])
  }, [courseId, router])

  useEffect(() => {
    fetchCourse()
  }, [fetchCourse])

  const handleStartStage = async (stageId: number) => {
    const token = getStoredToken()
    if (!token) return

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/stages/${stageId}/start`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (response.ok) {
        router.push(`/stage/${stageId}`)
      }
    } catch (error) {
      console.error('Failed to start stage:', error)
    }
  }

  const handleMasteryPathStart = () => {
    // Check if there are any stages
    if (!course?.stages?.length) {
      console.error('No stages available for this course')
      return
    }

    const inProgressStage = course.stages.find(s => s.progress?.status === 'in_progress')
    const nextUnlocked = course.stages.find((s, i) =>
      !s.progress && (i === 0 || course.stages[i-1]?.progress?.status === 'completed')
    )
    const firstStage = course.stages[0]

    const stageId = inProgressStage?.id || nextUnlocked?.id || firstStage?.id
    if (stageId) {
      handleStartStage(stageId)
    } else {
      console.error('No valid stage to start')
    }
  }

  const handleChallengePathStart = () => {
    router.push(`/challenge/${courseId}`)
  }

  // 计算进度
  const getProgress = () => {
    if (!course?.stages?.length) return { completed: 0, total: 0, percent: 0 }
    const completed = course.stages.filter(s => s.progress?.status === 'completed').length
    const total = course.stages.length
    return { completed, total, percent: Math.round((completed / total) * 100) }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <div className="animate-spin rounded-full h-10 w-10 border-2 border-primary border-t-transparent mx-auto mb-4"></div>
          <p className="text-muted-foreground">加载中...</p>
        </div>
      </div>
    )
  }

  if (!course) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <div className="w-16 h-16 bg-muted rounded-2xl flex items-center justify-center mx-auto mb-4">
            <BookOpen className="w-8 h-8 text-muted-foreground" />
          </div>
          <h2 className="text-xl font-semibold text-foreground mb-2">课程不存在</h2>
          <Link href="/" className="text-primary hover:underline">返回首页</Link>
        </div>
      </div>
    )
  }

  const config = COURSE_CONFIG[course.code] || { gradient: 'from-gray-500 to-gray-600', icon: course.code, color: 'text-gray-500' }
  const progress = getProgress()

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 glass border-b border-border/50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-14">
            <Link href="/dashboard" className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors group">
              <ArrowLeft className="w-4 h-4 group-hover:-translate-x-0.5 transition-transform" />
              <span className="text-sm">返回</span>
            </Link>
            <div className="flex items-center gap-4">
              <Link href="/leaderboard" className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors">
                <Trophy className="w-4 h-4" />
                <span className="hidden sm:inline">排行榜</span>
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Course Hero */}
      <section className="relative pt-20 pb-8 overflow-hidden">
        {/* Background */}
        <div className={`absolute inset-0 bg-gradient-to-br ${config.gradient} opacity-5`}></div>
        <div className="absolute top-0 right-0 w-96 h-96 bg-primary/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2"></div>

        <div className="relative max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-col sm:flex-row items-start gap-6">
            {/* Course Icon */}
            <div className={`w-20 h-20 rounded-2xl bg-gradient-to-br ${config.gradient} flex items-center justify-center text-white font-bold text-2xl shadow-xl`}>
              {config.icon}
            </div>

            <div className="flex-1">
              <h1 className="text-2xl sm:text-3xl font-bold text-foreground mb-2">{course.name}</h1>
              <p className="text-muted-foreground mb-4">{course.description || '系统学习编程知识，掌握核心技能'}</p>

              {/* Stats */}
              <div className="flex flex-wrap items-center gap-4 sm:gap-6 text-sm">
                <div className="flex items-center gap-1.5 text-muted-foreground">
                  <Target className="w-4 h-4 text-primary" />
                  <span><strong className="text-foreground">{course.stages?.length || 0}</strong> 个关卡</span>
                </div>
                <div className="flex items-center gap-1.5 text-muted-foreground">
                  <Clock className="w-4 h-4 text-primary" />
                  <span>预计 <strong className="text-foreground">30</strong> 小时</span>
                </div>
                <div className="flex items-center gap-1.5 text-muted-foreground">
                  <Trophy className="w-4 h-4 text-yellow-500" />
                  <span>经验值奖励</span>
                </div>
              </div>
            </div>
          </div>

          {/* Progress Bar */}
          {progress.total > 0 && (
            <div className="mt-6 p-4 bg-card rounded-xl border border-border">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-foreground">学习进度</span>
                <span className="text-sm text-muted-foreground">{progress.completed}/{progress.total} 关卡完成</span>
              </div>
              <div className="h-2 bg-muted rounded-full overflow-hidden">
                <div
                  className={`h-full bg-gradient-to-r ${config.gradient} rounded-full transition-all duration-500`}
                  style={{ width: `${progress.percent}%` }}
                />
              </div>
            </div>
          )}
        </div>
      </section>

      {/* Dual Learning Path */}
      <section className="py-8">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          {course.stages?.length === 0 ? (
            <div className="text-center py-16 bg-card rounded-2xl border border-border">
              <div className="w-16 h-16 bg-muted rounded-2xl flex items-center justify-center mx-auto mb-4">
                <BookOpen className="w-8 h-8 text-muted-foreground" />
              </div>
              <p className="text-muted-foreground">课程内容正在准备中，敬请期待</p>
            </div>
          ) : (
            <>
              {/* Learning Path Selector - 精进之路 / 挑战之路 */}
              <LearningPathSelector
                courseId={courseId}
                masteryProgress={masteryProgress}
                arenaProgress={arenaProgress}
                onMasteryPathStart={handleMasteryPathStart}
                onChallengePathStart={handleChallengePathStart}
                masteryPathUnlocked={true}
                challengePathUnlocked={true}
              />

              {/* Chapter Timeline */}
              <div className="mt-8">
                <h3 className="text-lg font-semibold text-foreground mb-4">章节进度</h3>
                <ChapterTimeline
                  chapters={course.stages?.map((s, i) => ({
                    id: s.id,
                    title: s.title,
                    status: s.progress?.status as 'locked' | 'unlocked' | 'in_progress' | 'completed' ||
                      (!s.progress && i > 0 && course.stages[i-1]?.progress?.status !== 'completed' ? 'locked' :
                       !s.progress ? 'unlocked' : s.progress.status) || 'locked'
                  })) || []}
                  currentChapterId={course.stages?.find(s => s.progress?.status === 'in_progress')?.id}
                  onChapterClick={handleStartStage}
                />
              </div>
            </>
          )}
        </div>
      </section>

    </div>
  )
}
