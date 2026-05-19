'use client'

import { useEffect, useState, useRef } from 'react'

let _cachedToken: string | null | undefined = undefined
function getCachedToken(): string | null {
  if (_cachedToken === undefined && typeof window !== 'undefined') {
    _cachedToken = localStorage.getItem('token:v1')
  }
  return _cachedToken ?? null
}
import { Trophy, Swords, Crown, Medal, Flame, ChevronRight, Star } from 'lucide-react'
import { getMasteryLeaderboard, getArenaLeaderboard, TIER_NAMES } from '@/lib/api'
import { getTierConfig } from '@/lib/icons/tier-icons'
import type { LeaderboardEntry, Tier } from '@/types/api'

interface LeaderboardTabsProps {
  courseId: number
  initialTab?: 'mastery' | 'arena'
  limit?: number
  showViewAll?: boolean
  onViewAll?: (tab: 'mastery' | 'arena') => void
}

export function LeaderboardTabs({
  courseId,
  initialTab = 'mastery',
  limit = 10,
  showViewAll = true,
  onViewAll,
}: LeaderboardTabsProps) {
  const [leaderboardState, setLeaderboardState] = useState({
    entries: [] as LeaderboardEntry[],
    userRank: null as number | null,
    loading: true,
  })
  const [currentUserId, setCurrentUserId] = useState<string | null>(null)
  const token = getCachedToken()
  const initialTabRef = useRef(initialTab)
  const [activeTab, setActiveTab] = useState<'mastery' | 'arena'>(initialTabRef.current)
  const { entries, userRank, loading } = leaderboardState

  useEffect(() => {
    // Get current user from token
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]))
        setCurrentUserId(payload.sub)
      } catch {
        // Ignore
      }
    }
  }, [token])

  useEffect(() => {
    const fetchData = async () => {
      if (!token) return

      try {
        const data = activeTab === 'mastery'
          ? await getMasteryLeaderboard(courseId, token, limit)
          : await getArenaLeaderboard(courseId, token, limit)

        setLeaderboardState({
          entries: data.entries,
          userRank: data.user_rank,
          loading: false,
        })
      } catch (error) {
        console.error('Failed to fetch leaderboard:', error)
        setLeaderboardState(prev => ({ ...prev, entries: [], loading: false }))
      }
    }

    fetchData()
  }, [courseId, activeTab, limit])

  const getRankStyle = (rank: number) => {
    switch (rank) {
      case 1:
        return 'bg-gradient-to-r from-yellow-500/20 via-yellow-500/10 to-transparent border-yellow-500/30'
      case 2:
        return 'bg-gradient-to-r from-gray-400/20 via-gray-400/10 to-transparent border-gray-400/30'
      case 3:
        return 'bg-gradient-to-r from-amber-600/20 via-amber-600/10 to-transparent border-amber-600/30'
      default:
        return 'bg-card border-border'
    }
  }

  const getRankIcon = (rank: number) => {
    switch (rank) {
      case 1:
        return <Crown className="size-5 text-yellow-500" />
      case 2:
        return <Medal className="size-5 text-gray-400" />
      case 3:
        return <Medal className="size-5 text-amber-600" />
      default:
        return <span className="text-sm font-bold text-muted-foreground">{rank}</span>
    }
  }

  return (
    <div className="bg-card rounded-2xl border border-border overflow-hidden">
      {/* Tabs */}
      <div className="flex border-b border-border">
        <button type="button"
          onClick={() => setActiveTab('mastery')}
          className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 text-sm font-medium transition-colors ${
            activeTab === 'mastery'
              ? 'text-amber-500 border-b-2 border-amber-500 bg-amber-500/5'
              : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
          }`}
        >
          <Trophy className="size-4" />
          精进榜
        </button>
        <button type="button"
          onClick={() => setActiveTab('arena')}
          className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 text-sm font-medium transition-colors ${
            activeTab === 'arena'
              ? 'text-blue-500 border-b-2 border-blue-500 bg-blue-500/5'
              : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
          }`}
        >
          <Swords className="size-4" />
          竞技榜
        </button>
      </div>

      {/* Content */}
      <div className="p-4">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full size-6 border-2 border-primary border-t-transparent"></div>
          </div>
        ) : entries.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-muted-foreground">暂无排名数据</p>
          </div>
        ) : (
          <div className="flex flex-col gap-y-2">
            {entries.map((entry) => (
              <div
                key={entry.user_id}
                className={`rounded-xl border p-3 flex items-center justify-between transition-all ${
                  entry.user_id === currentUserId
                    ? 'ring-2 ring-primary border-primary/30 bg-primary/5'
                    : getRankStyle(entry.rank)
                }`}
              >
                <div className="flex items-center gap-3">
                  {/* Rank */}
                  <div className="size-8 flex items-center justify-center">
                    {getRankIcon(entry.rank)}
                  </div>

                  {/* Avatar */}
                  <div className={`size-9 rounded-full flex items-center justify-center text-white font-medium text-sm ${
                    activeTab === 'mastery'
                      ? 'bg-gradient-to-br from-amber-500 to-amber-600'
                      : 'bg-gradient-to-br from-blue-500 to-blue-600'
                  }`}>
                    {entry.username.charAt(0)}
                  </div>

                  {/* Info */}
                  <div>
                    <p className="font-medium text-foreground text-sm">
                      {entry.username}
                      {entry.user_id === currentUserId && (
                        <span className="ml-1 text-xs text-primary">(你)</span>
                      )}
                    </p>
                    {activeTab === 'mastery' ? (
                      <p className="text-xs text-muted-foreground">
                        {entry.mastered_chapters}/{entry.total_chapters} 章节精通
                      </p>
                    ) : (
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <span className="size-4 flex items-center justify-center">
                          {getTierConfig(entry.tier as Tier)?.icon}
                        </span>
                        <span>{TIER_NAMES[entry.tier as Tier]}</span>
                        <span className="flex items-center gap-0.5">
                          <Flame className="size-3 text-orange-500" />
                          {entry.wins}胜
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Score */}
                <div className="text-right">
                  {activeTab === 'mastery' ? (
                    <>
                      <p className="font-bold text-foreground">
                        {entry.mastery_xp ?? 0}
                      </p>
                      <p className="text-xs text-muted-foreground">经验值</p>
                    </>
                  ) : (
                    <>
                      <p className="font-bold text-blue-500 flex items-center gap-1">
                        <Star className="size-4 text-yellow-500 fill-yellow-500" />
                        {entry.stars ?? 0}
                      </p>
                      <p className="text-xs text-muted-foreground">星星</p>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* User rank */}
        {userRank && userRank > limit && (
          <div className="mt-4 p-3 bg-primary/5 rounded-xl border border-primary/20">
            <p className="text-sm text-center text-muted-foreground">
              你的排名：<span className="font-bold text-primary">#{userRank}</span>
            </p>
          </div>
        )}

        {/* View all */}
        {showViewAll && (
          <button type="button"
            onClick={() => onViewAll?.(activeTab)}
            className="w-full mt-4 py-2 text-sm text-muted-foreground hover:text-foreground transition-colors inline-flex items-center justify-center gap-1"
          >
            查看完整榜单
            <ChevronRight className="size-4" />
          </button>
        )}
      </div>
    </div>
  )
}

// Minimal preview component for dashboard
export function LeaderboardPreview({
  type,
  courseId,
  limit = 5,
}: {
  type: 'mastery' | 'arena'
  courseId: number
  limit?: number
}) {
  const [leaderboardState, setLeaderboardState] = useState({
    entries: [] as LeaderboardEntry[],
    loading: true,
  })

  const token = getCachedToken()

  useEffect(() => {
    const fetchData = async () => {
      if (!token) return

      try {
        const data = type === 'mastery'
          ? await getMasteryLeaderboard(courseId, token, limit)
          : await getArenaLeaderboard(courseId, token, limit)

        setLeaderboardState({ entries: data.entries, loading: false })
      } catch {
        setLeaderboardState({ entries: [], loading: false })
      }
    }

    fetchData()
  }, [courseId, type, limit])

  const { entries, loading } = leaderboardState

  if (loading) {
    return (
      <div className="flex items-center justify-center py-6">
        <div className="animate-spin rounded-full size-5 border-2 border-primary border-t-transparent"></div>
      </div>
    )
  }

  if (entries.length === 0) {
    return (
      <p className="text-center text-sm text-muted-foreground py-4">暂无数据</p>
    )
  }

  return (
    <div className="flex flex-col gap-y-2">
      {entries.slice(0, 3).map((entry) => (
        <div
          key={entry.user_id}
          className="flex items-center gap-2 p-2 rounded-lg hover:bg-muted/50 transition-colors"
        >
          <span className={`size-5 flex items-center justify-center text-xs font-bold ${
            entry.rank === 1 ? 'text-yellow-500' :
            entry.rank === 2 ? 'text-gray-400' :
            entry.rank === 3 ? 'text-amber-600' :
            'text-muted-foreground'
          }`}>
            {entry.rank}
          </span>
          <div className="size-6 rounded-full bg-gradient-to-br from-primary to-primary-600 flex items-center justify-center text-primary-foreground text-xs font-medium">
            {entry.username.charAt(0)}
          </div>
          <span className="flex-1 text-sm text-foreground truncate">{entry.username}</span>
          <span className="text-sm font-medium text-foreground">
            {type === 'mastery'
              ? (entry.mastery_xp ?? 0)
              : (entry.stars ?? 0)}
          </span>
        </div>
      ))}
    </div>
  )
}
