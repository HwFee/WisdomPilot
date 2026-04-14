'use client'

import { TrendingUp, User, Rocket, ArrowRight } from 'lucide-react'

interface PeerUser {
  userId: string
  username: string
  rank: number
  avatar?: string
  xp?: number
  level?: number
}

interface PeerRankingListProps {
  currentUser: PeerUser
  peers: PeerUser[]
  onViewAll?: () => void
  lang?: 'zh' | 'en'
  compact?: boolean
}

// Validate avatar URL to prevent XSS via data: or javascript: URLs
function isValidAvatarUrl(url?: string): boolean {
  if (!url) return false
  try {
    const parsed = new URL(url)
    return ['https:', 'http:'].includes(parsed.protocol)
  } catch {
    return false
  }
}

export function PeerRankingList({ currentUser, peers, onViewAll, lang = 'zh', compact = false }: PeerRankingListProps) {
  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  const sortedPeers = [...peers].sort((a, b) => a.rank - b.rank)

  const getRankBadgeColor = (rank: number) => {
    if (rank === 1) return 'bg-yellow-500 text-white shadow-lg shadow-yellow-500/30'
    if (rank === 2) return 'bg-gray-400 text-white'
    if (rank === 3) return 'bg-amber-600 text-white'
    return 'bg-muted text-muted-foreground'
  }

  return (
    <div className={`bg-card rounded-2xl border border-border p-6 h-full flex flex-col ${compact ? 'overflow-hidden' : ''}`}>
      <h3 className="font-semibold text-foreground flex items-center gap-2 mb-4 flex-shrink-0">
        <TrendingUp className="w-5 h-5 text-yellow-500" />
        {t('同侪榜单', 'Peer Ranking')}
      </h3>

      <div className="flex-1 overflow-auto">
        <div className="space-y-2">
          {/* 当前用户高亮显示 */}
          {currentUser.rank > 0 && (
            <div className="flex items-center gap-3 p-3 rounded-xl border-2 border-primary/50 bg-primary/10 mb-3">
              <span className={`w-8 h-8 flex items-center justify-center rounded-lg text-sm font-bold ${getRankBadgeColor(currentUser.rank)}`}>
                {currentUser.rank}
              </span>
              <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0">
                <User className="w-4 h-4 text-primary" />
              </div>
              <span className="flex-1 text-sm font-bold text-primary truncate">
                {currentUser.username}
                <span className="text-xs text-primary/70 ml-1">({t('你', 'You')})</span>
              </span>
              <span className="text-sm font-bold text-primary">
                {t('第', '')}{currentUser.rank}{t('名', '')}
              </span>
            </div>
          )}

          {/* 排行榜前几名 */}
          {sortedPeers
            .filter((peer) => peer.userId !== currentUser.userId)
            .slice(0, compact ? 3 : 5)
            .map((peer) => (
              <div
                key={peer.userId}
                className="flex items-center gap-3 p-2.5 rounded-xl transition-colors hover:bg-muted/50"
              >
                <span className={`w-7 h-7 flex items-center justify-center rounded-lg text-xs font-bold ${getRankBadgeColor(peer.rank)}`}>
                  {peer.rank}
                </span>
                <div className="w-7 h-7 rounded-full bg-muted flex items-center justify-center overflow-hidden flex-shrink-0">
                  {isValidAvatarUrl(peer.avatar) ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={peer.avatar} alt={peer.username} className="w-full h-full rounded-full" referrerPolicy="no-referrer" />
                  ) : (
                    <User className="w-3.5 h-3.5 text-muted-foreground" />
                  )}
                </div>
                <span className="flex-1 text-sm font-medium text-foreground truncate">
                  {peer.username}
                </span>
                <span className="text-xs text-muted-foreground">
                  {t('第', '')}{peer.rank}{t('名', '')}
                </span>
              </div>
            ))}

          {/* 空状态 */}
          {sortedPeers.length === 0 && currentUser.rank === 0 && (
            <div className="text-center py-6 text-muted-foreground">
              <TrendingUp className="w-10 h-10 mx-auto mb-2 opacity-50" />
              <p className="text-sm">{t('开始学习以加入排行榜', 'Start learning to join the ranking')}</p>
            </div>
          )}
        </div>
      </div>

      {/* 底部查看全部 */}
      {onViewAll && !compact && (
        <button
          onClick={onViewAll}
          className="mt-4 w-full py-2 text-sm text-primary hover:text-primary/80 transition-colors flex items-center justify-center gap-1"
        >
          {t('查看完整排行榜', 'View Full Leaderboard')}
          <ArrowRight className="w-4 h-4" />
        </button>
      )}

      <p className="text-xs text-muted-foreground mt-3 text-center flex-shrink-0">
        {t('显示与你同级别的学习者', 'Showing learners at your level')}
      </p>
    </div>
  )
}
