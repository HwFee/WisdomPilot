'use client'

import { Suspense } from 'react'
import { useEffect, useState, useRef } from 'react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { getStoredToken, logout } from '@/lib/api'
import { ArrowLeft, Trophy, Swords, Crown, Medal, Flame, Star } from 'lucide-react'
import { getMasteryLeaderboard, getArenaLeaderboard, TIER_NAMES } from '@/lib/api'
import { getUserCourseProgress } from '@/lib/api/courses'
import { getTierConfig } from '@/lib/icons/tier-icons'
import type { LeaderboardEntry, Tier } from '@/types/api'
import type { CourseProgress } from '@/lib/api/courses'

type LeaderboardType = 'mastery' | 'arena'

function LeaderboardContent() {
  const { push } = useRouter()
  const { get } = useSearchParams()
  const [uiState, setUiState] = useState({
    activeTab: (get('tab') as LeaderboardType) || 'mastery',
    offset: 0,
    loading: true,
  })
  const courseIdRef = useRef<number>(1)
  const [dataState, setDataState] = useState({
    enrolledCourses: [] as CourseProgress[],
    leaderboard: [] as LeaderboardEntry[],
  })
  const currentUserIdRef = useRef<string | null>(null)
  const [currentUserState, setCurrentUserState] = useState<{ rank: number | null; data: LeaderboardEntry | null }>({ rank: null, data: null })
  const { activeTab, offset, loading } = uiState
  const { enrolledCourses, leaderboard } = dataState
  const { rank: currentUserRank, data: currentUserData } = currentUserState
  const courseLoadingRef = useRef(true)
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

      // Find current user's data in leaderboard
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

    // Get current user info from token
    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      currentUserIdRef.current = payload.sub
    } catch {
      // Ignore parsing errors
    }

    // Fetch enrolled courses first
    getUserCourseProgress(token)
      .then((progress) => {
        const courses = progress.courses || []
        setDataState(prev => ({ ...prev, enrolledCourses: courses }))
        // Use first enrolled course, or first available course, or default to 1
        if (courses.length > 0) {
          const firstEnrolled = courses.find(c => c.progress !== null && c.progress > 0) || courses[0]
          courseIdRef.current = firstEnrolled.course_id
        }
        // Fetch leaderboard data now that course is determined
        if (!hasFetched.current) {
          hasFetched.current = true
          fetchData(token, uiState.activeTab, 0)
        }
      })
      .catch((err) => {
        console.error('[Leaderboard] Failed to fetch course progress:', err)
      })
      .finally(() => {
        courseLoadingRef.current = false
        hasFetchedCourses.current = true
      })
  }, [push, uiState.activeTab])

  // Update URL when tab changes
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

  const getRankIcon = (rank: number) => {
    switch (rank) {
      case 1:
        return <Crown className="size-6 text-yellow-500" />
      case 2:
        return <Medal className="size-6 text-gray-400" />
      case 3:
        return <Medal className="size-6 text-amber-600" />
      default:
        return <span className="text-lg font-bold text-muted-foreground">{rank}</span>
    }
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 glass border-b border-border/50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-14">
            <Link href="/dashboard" className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors group">
              <ArrowLeft className="size-4 group-hover:-translate-x-0.5 transition-transform" />
              <span className="text-sm">返回</span>
            </Link>
            <div className="flex items-center gap-2">
              {activeTab === 'mastery' ? (
                <>
                  <Trophy className="size-5 text-amber-500" />
                  <span className="font-semibold text-foreground">精进榜</span>
                </>
              ) : (
                <>
                  <Swords className="size-5 text-blue-500" />
                  <span className="font-semibold text-foreground">竞技榜</span>
                </>
              )}
            </div>
            <div className="w-20"></div>
          </div>
        </div>
      </header>

      <main className="pt-20 pb-12">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Tabs */}
          <div className="mb-6">
            <div className="inline-flex items-center bg-muted rounded-xl p-1">
              <button type="button"
                onClick={() => handleTabChange('mastery')}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeTab === 'mastery'
                    ? 'bg-card text-amber-500 shadow-sm'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                <Trophy className="size-4" />
                <span>精进榜</span>
              </button>
              <button type="button"
                onClick={() => handleTabChange('arena')}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeTab === 'arena'
                    ? 'bg-card text-blue-500 shadow-sm'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                <Swords className="size-4" />
                <span>竞技榜</span>
              </button>
            </div>
          </div>

          {/* Current User Card - Shows user's rank and stats */}
          {currentUserRank && (
            <div className="mb-6">
              <div className={`border rounded-xl p-4 ${
                activeTab === 'mastery'
                  ? 'bg-amber-500/5 border-amber-500/20'
                  : 'bg-blue-500/5 border-blue-500/20'
              }`}>
                <div className="flex items-center gap-4">
                  {/* Rank Badge */}
                  <div className={`size-14 rounded-xl flex items-center justify-center font-bold text-xl shadow-lg ${
                    activeTab === 'mastery'
                      ? 'bg-amber-500 text-white shadow-amber-500/25'
                      : 'bg-blue-500 text-white shadow-blue-500/25'
                  }`}>
                    #{currentUserRank}
                  </div>

                  {/* User Info */}
                  <div className="flex-1">
                    <p className="text-sm text-muted-foreground">你的排名</p>
                    {activeTab === 'mastery' ? (
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-foreground text-lg">{currentUserData?.mastery_xp ?? 0}</span>
                        <span className="text-sm text-muted-foreground">经验值</span>
                      </div>
                    ) : (
                      <div className="flex items-center gap-3">
                        {currentUserData?.tier ? (
                          <>
                            <span className="size-5 flex items-center justify-center">
                              {getTierConfig(currentUserData.tier)?.icon}
                            </span>
                            <span className="font-medium text-foreground">{TIER_NAMES[currentUserData.tier as Tier]}</span>
                            {currentUserData.sub_tier && (
                              <span className="text-muted-foreground">{['I','II','III','IV','V'][currentUserData.sub_tier - 1]}</span>
                            )}
                          </>
                        ) : (
                          <span className="text-muted-foreground">未定级</span>
                        )}
                        <span className="flex items-center gap-1">
                          <Star className="size-4 text-yellow-500" />
                          <span className="font-medium">{currentUserData?.stars ?? 0}</span>
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* No Data State */}
          {!loading && leaderboard.length === 0 && (
            <div className="text-center py-12">
              <div className={`size-16 rounded-full mx-auto mb-4 flex items-center justify-center ${
                activeTab === 'mastery' ? 'bg-amber-500/10' : 'bg-blue-500/10'
              }`}>
                {activeTab === 'mastery' ? (
                  <Trophy className="size-8 text-amber-500" />
                ) : (
                  <Swords className="size-8 text-blue-500" />
                )}
              </div>
              {enrolledCourses.length === 0 ? (
                <>
                  <p className="text-muted-foreground mb-2">你还没有选择任何课程</p>
                  <p className="text-sm text-muted-foreground">
                    先选择并加入一门课程后才能查看排行榜
                  </p>
                  <Link href="/dashboard" className="inline-block mt-4 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors">
                    前往课程页面
                  </Link>
                </>
              ) : (
                <>
                  <p className="text-muted-foreground mb-2">暂无排名数据</p>
                  <p className="text-sm text-muted-foreground">
                    {activeTab === 'mastery'
                      ? '完成精进之路的学习和测试，获得经验值上榜'
                      : '参与竞技挑战，获得星星和段位上榜'}
                  </p>
                </>
              )}
            </div>
          )}

          {/* Leaderboard List */}
          {loading && offset === 0 ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full size-8 border-2 border-primary border-t-transparent"></div>
            </div>
          ) : leaderboard.length > 0 && (
            <div className="gap-y-2">
              {leaderboard.map((entry) => (
                <div
                  key={entry.user_id}
                  className={`rounded-xl border p-4 flex items-center justify-between transition-all ${
                    entry.user_id === currentUserIdRef.current ? 'ring-2 ring-primary border-primary/30 bg-primary/5' : 'bg-card hover:border-primary/30'
                  }`}
                >
                  <div className="flex items-center gap-4">
                    <div className="size-10 bg-muted rounded-xl flex items-center justify-center">
                      {getRankIcon(entry.rank)}
                    </div>
                    <div className="size-10 bg-gradient-to-br from-primary to-primary-600 rounded-full flex items-center justify-center text-primary-foreground font-medium shadow-md">
                      {entry.username.charAt(0)}
                    </div>
                    <div>
                      <p className="font-medium text-foreground">
                        {entry.username}
                        {entry.user_id === currentUserIdRef.current && (
                          <span className="ml-2 text-xs text-primary">(你)</span>
                        )}
                      </p>
                    </div>
                  </div>

                  <div className="text-right">
                    {activeTab === 'mastery' ? (
                      <div className="flex items-center gap-2 justify-end">
                        <Trophy className="size-4 text-amber-500" />
                        <span className="font-bold text-foreground text-lg">{entry.mastery_xp ?? 0}</span>
                        <span className="text-xs text-muted-foreground">经验值</span>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2 justify-end">
                        {entry.tier ? (
                          <>
                            <span className="size-4 flex items-center justify-center">
                              {getTierConfig(entry.tier)?.icon}
                            </span>
                            <span className="font-medium text-foreground">{TIER_NAMES[entry.tier as Tier]}</span>
                            {entry.sub_tier && (
                              <span className="text-muted-foreground">{['I','II','III','IV','V'][entry.sub_tier - 1]}</span>
                            )}
                          </>
                        ) : (
                          <span className="text-muted-foreground">未定级</span>
                        )}
                        <span className="flex items-center gap-1">
                          <Star className="size-4 text-yellow-500" />
                          <span className="font-bold">{entry.stars ?? 0}</span>
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Load More */}
          {!loading && leaderboard.length >= limit && (
            <div className="text-center mt-6">
              <button type="button"
                onClick={handleLoadMore}
                className="px-6 py-2 bg-muted text-foreground rounded-xl text-sm font-medium hover:bg-muted/80 transition-colors"
              >
                加载更多
              </button>
            </div>
          )}
        </div>
      </main>

      {/* Footer Info */}
      <div className="text-center pb-8">
        <p className="text-sm text-muted-foreground">
          {activeTab === 'mastery'
            ? '精进榜基于精进经验值计算排名，通过学习和答题获得经验'
            : '竞技榜按段位排名：大段位 > 小段位 > 星星数'}
        </p>
      </div>
    </div>
  )
}

export default function LeaderboardPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-spin rounded-full size-8 border-2 border-primary border-t-transparent"></div>
      </div>
    }>
      <LeaderboardContent />
    </Suspense>
  )
}
