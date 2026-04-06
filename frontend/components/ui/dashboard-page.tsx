'use client'

import { useEffect, useState, useRef } from 'react'
import { useRouter } from 'next/navigation'
import {
  getStoredUser,
  getStoredToken,
  logout,
  User,
  LearningStatistics,
  Activity,
  ChapterProgress,
  getLearningStatistics,
  getActivityHistory,
  getUserProgress,
} from '@/lib/api'
import { CourseSearch } from '@/components/ui/course-search'
import { StatsCards } from '@/components/ui/stats-cards'
import { ActivityFeed } from '@/components/ui/activity-feed'
import { courseChapters, CourseChapter } from '@/lib/course-data'
import { Play, Search, Sparkles, Trophy } from 'lucide-react'

export default function DashboardPage() {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [lang, setLang] = useState<'zh' | 'en'>('zh')
  const [activeTab, setActiveTab] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [stats, setStats] = useState<LearningStatistics | null>(null)
  const [activities, setActivities] = useState<Activity[]>([])
  const [userProgress, setUserProgress] = useState<ChapterProgress[]>([])
  const [isStatsLoading, setIsStatsLoading] = useState(true)
  const fetchGuardRef = useRef(false)

  useEffect(() => {
    if (fetchGuardRef.current) return
    fetchGuardRef.current = true

    const token = getStoredToken()
    const storedUser = getStoredUser()
    const savedLang = localStorage.getItem('language') || 'zh'

    if (!token || !storedUser) {
      router.push('/login')
      return
    }

    setUser(storedUser)
    setLang(savedLang as 'zh' | 'en')

    // Fetch stats and activities
    const fetchData = async () => {
      try {
        const [statsData, activitiesData, progressData] = await Promise.all([
          getLearningStatistics(token),
          getActivityHistory(token, 20),
          getUserProgress(token),
        ])
        setStats(statsData)
        setActivities(activitiesData)
        setUserProgress(progressData)
      } catch (error) {
        console.error('[Dashboard] 获取数据失败:', error)
        // Set default stats on error
        setStats({
          total_learning_time_seconds: 0,
          total_sessions: 0,
          completed_chapters: 0,
          in_progress_chapters: 0,
          total_subsections_completed: 0,
          current_streak: 0,
          longest_streak: 0,
        })
      } finally {
        setIsStatsLoading(false)
        setIsLoading(false)
      }
    }

    fetchData()
  }, [router])

  const handleLogout = () => {
    logout()
    router.push('/login')
  }

  const toggleLanguage = () => {
    const newLang = lang === 'zh' ? 'en' : 'zh'
    setLang(newLang)
    localStorage.setItem('language', newLang)
  }

  const t = (zh: string, en: string) => lang === 'zh' ? zh : en

  // Search courses function - searches in title, topics, and subsections
  const searchCourses = (chapters: CourseChapter[], query: string): CourseChapter[] => {
    if (!query.trim()) {
      return chapters
    }
    const lowerQuery = query.toLowerCase().trim()
    return chapters.filter((chapter) => {
      // Search in title
      if (chapter.title.toLowerCase().includes(lowerQuery)) return true
      // Search in English title
      if (chapter.titleEn.toLowerCase().includes(lowerQuery)) return true
      // Search in topics (main tags)
      if (chapter.topics.some((topic) => topic.toLowerCase().includes(lowerQuery))) return true
      // Search in subsections (detailed content)
      if (chapter.subsections.some((subsection) => subsection.toLowerCase().includes(lowerQuery))) return true
      return false
    })
  }

  // Apply tab filter first, then search filter
  const getChapterStatus = (chapterId: number): string => {
    const progress = userProgress.find(p => p.chapter_id === chapterId)
    if (!progress) return 'not_started'
    return progress.status === 'in_progress' ? 'learning' : progress.status
  }

  const getChapterProgress = (chapterId: number): number => {
    const progress = userProgress.find(p => p.chapter_id === chapterId)
    if (!progress) return 0
    return progress.progress_percent
  }

  const tabFilteredCourses = activeTab === 'all'
    ? courseChapters
    : activeTab === 'learning'
      ? courseChapters.filter(c => getChapterStatus(c.id) === 'learning')
      : courseChapters.filter(c => getChapterStatus(c.id) === 'completed')

  const filteredCourses = searchCourses(tabFilteredCourses, searchQuery)

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <p className="text-muted-foreground">加载中...</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="bg-card border-b border-border sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-primary flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-foreground">DSA 教学平台</h1>
                <p className="text-xs text-muted-foreground">数据结构与算法</p>
              </div>
            </div>

            <div className="flex items-center gap-6">
              <CourseSearch
                chapters={courseChapters}
                placeholder={t('搜索课程、小节...', 'Search courses, subsections...')}
                value={searchQuery}
                onChange={setSearchQuery}
                onSelect={(chapter, subsectionIndex) => {
                  if (subsectionIndex !== undefined) {
                    router.push(`/chapter/${chapter.id}?subsection=${subsectionIndex}`)
                  } else {
                    router.push(`/chapter/${chapter.id}`)
                  }
                }}
                className="w-80"
              />

              <div className="flex items-center bg-muted rounded-full p-1">
                <button
                  onClick={() => { if (lang !== 'zh') toggleLanguage() }}
                  className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
                    lang === 'zh'
                      ? 'bg-card text-foreground shadow-sm'
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  中文
                </button>
                <button
                  onClick={() => { if (lang !== 'en') toggleLanguage() }}
                  className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
                    lang === 'en'
                      ? 'bg-card text-foreground shadow-sm'
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  EN
                </button>
              </div>

              <div className="flex items-center gap-3">
                <span className="text-sm text-muted-foreground">
                  {t('欢迎', 'Welcome')}, <span className="font-semibold text-foreground">{user?.username}</span>
                </span>
                <button
                  onClick={handleLogout}
                  className="text-sm text-red-500 hover:text-red-600 font-medium transition-colors"
                >
                  {t('退出', 'Logout')}
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Welcome Banner */}
        <div className="rounded-xl mb-8 p-6 bg-card border border-border">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-primary flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-primary-foreground" />
            </div>
            <div>
              <p className="text-muted-foreground text-sm">{t('欢迎回来，', 'Welcome back,')}{user?.username}</p>
              <h2 className="text-lg font-bold text-foreground">
                {t('「不积跬步，无以至千里」', '"Small steps lead to great journeys"')}
              </h2>
              <p className="text-muted-foreground text-sm">
                {t('数据结构与算法是程序的灵魂，每天坚持学习必有收获', 'Data structures and algorithms are the soul of programs')}
              </p>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        <StatsCards
          stats={stats}
          totalChapters={courseChapters.length}
          lang={lang}
          isLoading={isStatsLoading}
        />

        {/* Main grid */}
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Left column */}
          <div className="lg:col-span-2">
            {/* Course content header */}
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-xl font-semibold text-foreground">
                {t('课程内容', 'Course Content')}
              </h2>
              <div className="flex gap-2">
                {[
                  { key: 'all', zh: '全部', en: 'All' },
                  { key: 'learning', zh: '进行中', en: 'Learning' },
                  { key: 'completed', zh: '已完成', en: 'Done' },
                ].map((tab) => (
                  <button
                    key={tab.key}
                    onClick={() => setActiveTab(tab.key)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                      activeTab === tab.key
                        ? 'bg-emerald-100 text-emerald-600'
                        : 'bg-transparent text-muted-foreground hover:text-foreground'
                    }`}
                  >
                    {lang === 'zh' ? tab.zh : tab.en}
                  </button>
                ))}
              </div>
            </div>

            {/* Course cards grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredCourses.length > 0 ? (
                filteredCourses.map((chapter) => (
                  <div
                    key={chapter.id}
                    onClick={() => router.push(`/chapter/${chapter.id}`)}
                    className="group bg-card rounded-xl p-5 border border-border hover:shadow-lg hover:border-muted-foreground/30 transition-all duration-300 cursor-pointer"
                  >
                    <div className="flex items-center gap-4 mb-4">
                      <div
                        className="w-12 h-12 rounded-xl flex items-center justify-center font-bold text-lg"
                        style={{ backgroundColor: `${chapter.color}15`, color: chapter.color }}
                      >
                        {chapter.num}
                      </div>
                      <div className="flex-1">
                        <h4 className="font-bold text-foreground group-hover:text-muted-foreground transition-colors">
                          {t(chapter.title, chapter.titleEn)}
                        </h4>
                        <p className="text-xs text-muted-foreground">Chapter {chapter.id}</p>
                      </div>
                    </div>

                    <div className="mb-4">
                      <div className="flex justify-between text-xs text-muted-foreground mb-1">
                        <span>{t('进度', 'Progress')}</span>
                        <span>{getChapterProgress(chapter.id)}%</span>
                      </div>
                      <div className="h-2 bg-muted rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all duration-500"
                          style={{ width: `${getChapterProgress(chapter.id)}%`, backgroundColor: chapter.color }}
                        />
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-1.5">
                      {chapter.topics.slice(0, 3).map((topic, idx) => (
                        <span
                          key={idx}
                          onClick={(e) => {
                            e.stopPropagation()
                            router.push(`/chapter/${chapter.id}`)
                          }}
                          className="text-xs px-2 py-0.5 rounded-full cursor-pointer hover:opacity-80 transition-opacity"
                          style={{ backgroundColor: `${chapter.color}15`, color: chapter.color }}
                        >
                          {topic}
                        </span>
                      ))}
                      {chapter.topics.length > 3 && (
                        <span
                          className="text-xs px-2 py-0.5 rounded-full bg-muted text-muted-foreground font-medium"
                        >
                          +{chapter.topics.length - 3}
                        </span>
                      )}
                    </div>
                  </div>
                ))
              ) : (
                <div className="col-span-full flex flex-col items-center justify-center py-12 text-muted-foreground">
                  <Search className="w-12 h-12 mb-4" />
                  <p className="text-lg font-medium">{t('未找到匹配课程', 'No courses found')}</p>
                  <p className="text-sm">{t('请尝试其他关键词', 'Try a different search term')}</p>
                </div>
              )}
            </div>
          </div>

          {/* Right sidebar - aligned with course cards (offset by header height) */}
          <div className="flex flex-col mt-[56px] h-[calc(100vh-296px)] overflow-auto">
            {/* Last study card */}
            <div className="bg-card rounded-xl p-6 border border-border mb-6">
              <h3 className="font-semibold text-foreground mb-4">{t('上次学习', 'Last Study')}</h3>
              {(() => {
                // 直接取第一个活动（最新）
                const lastActivity = activities[0]
                const lastChapterId = lastActivity?.chapter_id ?? null

                // Find the chapter from progress if exists, otherwise find by chapter_id
                const progress = lastChapterId
                  ? userProgress.find(p => p.chapter_id === lastChapterId)
                  : null
                const lastChapter = lastChapterId
                  ? courseChapters.find(c => c.id === lastChapterId)
                  : null

                if (!lastActivity || !lastChapter) {
                  return (
                    <div className="text-center py-6 text-muted-foreground">
                      <Play className="w-10 h-10 mx-auto mb-2 opacity-50" />
                      <p>{t('暂无学习记录', 'No study record')}</p>
                      <p className="text-sm">{t('开始学习一个章节吧！', 'Start learning a chapter!')}</p>
                    </div>
                  )
                }

                const totalSubsections = lastChapter.subsections.length
                const completedSubsectionsList = progress?.completed_subsections ?? []
                const completedCount = completedSubsectionsList.length
                const progressPercent = progress?.progress_percent ?? 0

                // 直接用最新活动的 subsection_index
                const lastStudiedSubsection = lastActivity?.subsection_index ?? 0

                return (
                  <>
                    <div className="flex items-start gap-4 mb-4">
                      <div
                        className="w-14 h-14 rounded-xl flex items-center justify-center text-xl font-bold"
                        style={{ background: `${lastChapter.color}20`, color: lastChapter.color }}
                      >
                        {lastChapter.num}
                      </div>
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-foreground mb-1">
                          {t(lastChapter.title, lastChapter.titleEn)}
                        </h4>
                        <p className="text-sm text-muted-foreground mb-1">
                          {t('上次学习：', 'Last studied:')} {lastChapter.subsections[lastStudiedSubsection]}
                        </p>
                        {progress ? (
                          <>
                            <div className="h-2 bg-muted rounded-full overflow-hidden mb-2">
                              <div
                                className="h-full rounded-full"
                                style={{ width: `${progressPercent}%`, background: `linear-gradient(90deg, ${lastChapter.color}, ${lastChapter.color}aa)` }}
                              />
                            </div>
                            <div className="flex justify-between text-xs text-muted-foreground">
                              <span>{progressPercent}% {t('已完成', 'completed')}</span>
                              <span>{completedCount}/{totalSubsections} {t('课时', 'lessons')}</span>
                            </div>
                          </>
                        ) : (
                          <div className="flex justify-between text-xs text-muted-foreground">
                            <span>{t('新开始学习', 'Started learning')}</span>
                            <span>{totalSubsections} {t('课时', 'lessons')}</span>
                          </div>
                        )}
                      </div>
                    </div>
                    <button
                      onClick={() => {
                        router.push(`/chapter/${lastChapter.id}?subsection=${lastStudiedSubsection}`)
                      }}
                      className="w-full flex items-center justify-center gap-2 py-3 rounded-xl font-semibold text-white transition-all"
                      style={{ background: `linear-gradient(135deg, ${lastChapter.color}, ${lastChapter.color}aa)` }}
                    >
                      <Play className="w-4 h-4" />
                      {t('继续学习', 'Continue')}
                    </button>
                  </>
                )
              })()}
            </div>

            {/* Recent activity - stretches to fill remaining height */}
            <div className="bg-card rounded-xl p-6 border border-border flex flex-col flex-1 min-h-0">
              <h3 className="font-semibold text-foreground mb-4">{t('最近动态', 'Recent Activity')}</h3>
              <div className="flex-1 overflow-auto">
                <ActivityFeed
                  // 只显示章节级别的活动，不显示小节切换
                  activities={activities.filter(a => a.activity_type !== 'subsection_changed')}
                  lang={lang}
                  isLoading={isStatsLoading}
                />
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
