'use client'

import { Suspense } from 'react'
import { useEffect, useState, useRef, useCallback } from 'react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { getStoredToken, logout } from '@/lib/api'
import { ArrowLeft, Trophy, Swords, Crown, Medal, TrendingUp, Users, Clock, Flame, ChevronLeft, ChevronRight, Target } from 'lucide-react'
import { LeaderboardTabs, LeaderboardPreview } from '@/components/leaderboard/LeaderboardTabs'
import { getMasteryLeaderboard, getArenaLeaderboard, TIER_ICONS, TIER_NAMES } from '@/lib/api'
import type { LeaderboardEntry, Tier } from '@/types/api'

type LeaderboardType = 'mastery' | 'arena'

function LeaderboardContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [activeTab, setActiveTab] = useState<LeaderboardType>(
    (searchParams.get('tab') as LeaderboardType) || 'mastery'
  )
  const [courseId, setCourseId] = useState<number>(1)
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [currentUserId, setCurrentUserId] = useState<string | null>(null)
  const [currentUserRank, setCurrentUserRank] = useState<number | null>(null)
  const [offset, setOffset] = useState(0)
  const limit = 20
  const hasFetched = useRef(false)

  const fetchData = useCallback(async (token: string, tab: LeaderboardType, off: number = 0) => {
    try {
      setLoading(true)
      const data = tab === 'mastery'
        ? await getMasteryLeaderboard(courseId, token, limit, off)
        : await getArenaLeaderboard(courseId, token, limit, off)

      if (off === 0) {
        setLeaderboard(data.entries)
      } else {
        setLeaderboard(prev => [...prev, ...data.entries])
      }
      setCurrentUserRank(data.user_rank)
    } catch {
      // Handle error silently
    } finally {
      setLoading(false)
    }
  }, [courseId])

  useEffect(() => {
    if (hasFetched.current) return
    const token = getStoredToken()
    if (!token) {
      logout()
      router.push('/login')
      return
    }

    // Get current user info from token
    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      setCurrentUserId(payload.sub)
    } catch {
      // Ignore parsing errors
    }

    hasFetched.current = true
    fetchData(token, activeTab, 0)
  }, [router, fetchData, activeTab])

  // Update URL when tab changes
  const handleTabChange = (tab: LeaderboardType) => {
    setActiveTab(tab)
    setOffset(0)
    const token = getStoredToken()
    if (token) {
      fetchData(token, tab, 0)
    }
    router.push(`/leaderboard?tab=${tab}`)
  }

  const handleLoadMore = () => {
    const newOffset = offset + limit
    setOffset(newOffset)
    const token = getStoredToken()
    if (token) {
      fetchData(token, activeTab, newOffset)
    }
  }

  const getRankIcon = (rank: number) => {
    switch (rank) {
      case 1:
        return <Crown className="w-6 h-6 text-yellow-500" />
      case 2:
        return <Medal className="w-6 h-6 text-gray-400" />
      case 3:
        return <Medal className="w-6 h-6 text-amber-600" />
      default:
        return <span className="text-lg font-bold text-muted-foreground">{rank}</span>
    }
  }

  const getRankStyle = (rank: number) => {
    switch (rank) {
      case 1:
        return 'bg-gradient-to-r from-yellow-500/20 via-yellow-500/10 to-transparent border-yellow-500/30'
      case 2:
        return 'bg-gradient-to-r from-gray-400/20 via-gray-400/10 to-transparent border-gray-400/30'
      case 3:
        return 'bg-gradient-to-r from-amber-600/20 via-amber-600/10 to-transparent border-amber-600/30'
      default:
        return 'bg-card border-border hover:border-primary/30'
    }
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 glass border-b border-border/50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-14">
            <Link href="/dashboard" className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors group">
              <ArrowLeft className="w-4 h-4 group-hover:-translate-x-0.5 transition-transform" />
              <span className="text-sm">返回</span>
            </Link>
            <div className="flex items-center gap-2">
              {activeTab === 'mastery' ? (
                <>
                  <Trophy className="w-5 h-5 text-amber-500" />
                  <span className="font-semibold text-foreground">精进榜</span>
                </>
              ) : (
                <>
                  <Swords className="w-5 h-5 text-blue-500" />
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
              <button
                onClick={() => handleTabChange('mastery')}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeTab === 'mastery'
                    ? 'bg-card text-amber-500 shadow-sm'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                <Trophy className="w-4 h-4" />
                <span>精进榜</span>
              </button>
              <button
                onClick={() => handleTabChange('arena')}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeTab === 'arena'
                    ? 'bg-card text-blue-500 shadow-sm'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                <Swords className="w-4 h-4" />
                <span>竞技榜</span>
              </button>
            </div>
          </div>

          {/* Tab description */}
          <div className="mb-6 p-4 bg-card rounded-xl border border-border">
            {activeTab === 'mastery' ? (
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-amber-500/20 flex items-center justify-center">
                  <Target className="w-5 h-5 text-amber-500" />
                </div>
                <div>
                  <p className="font-medium text-foreground">精进榜</p>
                  <p className="text-sm text-muted-foreground">按章节掌握进度排名，鼓励系统学习</p>
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-blue-500/20 flex items-center justify-center">
                  <Swords className="w-5 h-5 text-blue-500" />
                </div>
                <div>
                  <p className="font-medium text-foreground">竞技榜</p>
                  <p className="text-sm text-muted-foreground">按挑战积分排名，展示竞技实力</p>
                </div>
              </div>
            )}
          </div>

          {/* Current User Rank Card */}
          {currentUserRank && (
            <div className="mb-6">
              <div className={`border rounded-xl p-4 flex items-center justify-between ${
                activeTab === 'mastery'
                  ? 'bg-amber-500/5 border-amber-500/20'
                  : 'bg-blue-500/5 border-blue-500/20'
              }`}>
                <div className="flex items-center gap-4">
                  <div className={`w-12 h-12 rounded-xl flex items-center justify-center font-bold text-lg shadow-lg ${
                    activeTab === 'mastery'
                      ? 'bg-amber-500 text-white shadow-amber-500/25'
                      : 'bg-blue-500 text-white shadow-blue-500/25'
                  }`}>
                    {currentUserRank}
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">你的排名</p>
                    <p className="font-semibold text-foreground">继续努力，冲上榜单！</p>
                  </div>
                </div>
                <Link
                  href="/dashboard"
                  className={`px-4 py-2 text-primary-foreground rounded-lg text-sm font-medium hover:opacity-90 transition-opacity ${
                    activeTab === 'mastery' ? 'bg-amber-500' : 'bg-blue-500'
                  }`}
                >
                  开始学习
                </Link>
              </div>
            </div>
          )}

          {/* Top 3 Podium */}
          {!loading && leaderboard.length >= 3 && (
            <div className="mb-8">
              <div className="flex items-end justify-center gap-4">
                {/* 2nd Place */}
                <div className="flex flex-col items-center">
                  <div className="w-16 h-16 bg-gradient-to-br from-gray-300 to-gray-400 rounded-full flex items-center justify-center mb-2 shadow-lg">
                    <span className="text-xl font-bold text-white">{leaderboard[1]?.username.charAt(0)}</span>
                  </div>
                  <p className="font-medium text-foreground text-sm mb-1">{leaderboard[1]?.username}</p>
                  <div className="bg-gray-100 dark:bg-gray-800 rounded-xl px-4 py-6 text-center w-28">
                    <Medal className="w-6 h-6 text-gray-400 mx-auto mb-1" />
                    <p className="text-lg font-bold text-foreground">
                      {activeTab === 'mastery'
                        ? leaderboard[1]?.total_mastery?.toFixed(0)
                        : leaderboard[1]?.total_score?.toFixed(0)}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {activeTab === 'mastery' ? '掌握分' : '积分'}
                    </p>
                    {activeTab === 'arena' && leaderboard[1]?.tier && (
                      <p className="text-xs mt-1">
                        {TIER_ICONS[leaderboard[1].tier as Tier]} {TIER_NAMES[leaderboard[1].tier as Tier]}
                      </p>
                    )}
                  </div>
                </div>

                {/* 1st Place */}
                <div className="flex flex-col items-center -mt-4">
                  <div className="w-20 h-20 bg-gradient-to-br from-yellow-400 to-yellow-500 rounded-full flex items-center justify-center mb-2 shadow-xl ring-4 ring-yellow-400/30">
                    <span className="text-2xl font-bold text-white">{leaderboard[0]?.username.charAt(0)}</span>
                  </div>
                  <p className="font-semibold text-foreground mb-1">{leaderboard[0]?.username}</p>
                  <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-xl px-5 py-8 text-center w-32 border border-yellow-200 dark:border-yellow-800">
                    <Crown className="w-8 h-8 text-yellow-500 mx-auto mb-1" />
                    <p className="text-xl font-bold text-foreground">
                      {activeTab === 'mastery'
                        ? leaderboard[0]?.total_mastery?.toFixed(0)
                        : leaderboard[0]?.total_score?.toFixed(0)}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {activeTab === 'mastery' ? '掌握分' : '积分'}
                    </p>
                    {activeTab === 'arena' && leaderboard[0]?.tier && (
                      <p className="text-xs mt-1">
                        {TIER_ICONS[leaderboard[0].tier as Tier]} {TIER_NAMES[leaderboard[0].tier as Tier]}
                      </p>
                    )}
                  </div>
                </div>

                {/* 3rd Place */}
                <div className="flex flex-col items-center">
                  <div className="w-16 h-16 bg-gradient-to-br from-amber-500 to-amber-600 rounded-full flex items-center justify-center mb-2 shadow-lg">
                    <span className="text-xl font-bold text-white">{leaderboard[2]?.username.charAt(0)}</span>
                  </div>
                  <p className="font-medium text-foreground text-sm mb-1">{leaderboard[2]?.username}</p>
                  <div className="bg-amber-50 dark:bg-amber-900/20 rounded-xl px-4 py-5 text-center w-28 border border-amber-200 dark:border-amber-800">
                    <Medal className="w-6 h-6 text-amber-600 mx-auto mb-1" />
                    <p className="text-lg font-bold text-foreground">
                      {activeTab === 'mastery'
                        ? leaderboard[2]?.total_mastery?.toFixed(0)
                        : leaderboard[2]?.total_score?.toFixed(0)}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {activeTab === 'mastery' ? '掌握分' : '积分'}
                    </p>
                    {activeTab === 'arena' && leaderboard[2]?.tier && (
                      <p className="text-xs mt-1">
                        {TIER_ICONS[leaderboard[2].tier as Tier]} {TIER_NAMES[leaderboard[2].tier as Tier]}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Leaderboard List */}
          {loading && offset === 0 ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary border-t-transparent"></div>
            </div>
          ) : (
            <div className="space-y-2">
              {leaderboard.slice(3).map((entry) => (
                <div
                  key={entry.user_id}
                  className={`rounded-xl border p-4 flex items-center justify-between transition-all ${
                    entry.user_id === currentUserId ? 'ring-2 ring-primary border-primary/30 bg-primary/5' : 'bg-card hover:border-primary/30'
                  }`}
                >
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-muted rounded-xl flex items-center justify-center">
                      {getRankIcon(entry.rank)}
                    </div>
                    <div className="w-10 h-10 bg-gradient-to-br from-primary to-primary-600 rounded-full flex items-center justify-center text-primary-foreground font-medium shadow-md">
                      {entry.username.charAt(0)}
                    </div>
                    <div>
                      <p className="font-medium text-foreground">
                        {entry.username}
                        {entry.user_id === currentUserId && (
                          <span className="ml-2 text-xs text-primary">(你)</span>
                        )}
                      </p>
                      {activeTab === 'mastery' ? (
                        <div className="flex items-center gap-3 text-sm text-muted-foreground">
                          <span>{entry.mastered_chapters}/{entry.total_chapters} 章节</span>
                          <span>平均 {entry.avg_mastery?.toFixed(0)}%</span>
                        </div>
                      ) : (
                        <div className="flex items-center gap-3 text-sm text-muted-foreground">
                          <span>{TIER_ICONS[entry.tier as Tier]} {TIER_NAMES[entry.tier as Tier]}</span>
                          <span className="flex items-center gap-1">
                            <Flame className="w-3 h-3 text-orange-500" />
                            {entry.wins}胜
                          </span>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="text-right">
                    <p className="font-bold text-foreground text-lg">
                      {activeTab === 'mastery'
                        ? entry.total_mastery?.toFixed(0)
                        : entry.total_score?.toFixed(0)}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {activeTab === 'mastery' ? '掌握分' : '竞技分'}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Load More */}
          {!loading && leaderboard.length >= limit && (
            <div className="text-center mt-6">
              <button
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
            ? '精进榜基于章节掌握进度计算排名'
            : '竞技榜基于挑战积分计算排名，段位越高排名越靠前'}
        </p>
      </div>
    </div>
  )
}

export default function LeaderboardPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary border-t-transparent"></div>
      </div>
    }>
      <LeaderboardContent />
    </Suspense>
  )
}
