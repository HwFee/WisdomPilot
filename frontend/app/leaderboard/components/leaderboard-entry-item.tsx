import { Trophy, Star } from 'lucide-react'
import { TIER_NAMES } from '@/lib/api'
import { getTierConfig } from '@/lib/icons/tier-icons'
import { getRankIcon, getSubTierLabel } from '../lib/leaderboard-utils'
import { cn } from '@/lib/utils'
import type { LeaderboardEntry, Tier } from '@/types/api'

interface LeaderboardEntryItemProps {
  entry: LeaderboardEntry
  activeTab: 'mastery' | 'arena'
  isCurrentUser: boolean
}

export function LeaderboardEntryItem({ entry, activeTab, isCurrentUser }: LeaderboardEntryItemProps) {
  return (
    <div
      className={cn(
        "grid grid-cols-[auto_auto_1fr_auto] items-center gap-5 px-8 py-5 border-b border-border last:border-b-0",
        isCurrentUser ? "bg-primary/5" : "hover:bg-muted/30 transition-colors"
      )}
    >
      <div className="size-10 bg-muted rounded-lg flex items-center justify-center">
        {getRankIcon(entry.rank)}
      </div>
      <div className="size-10 bg-primary rounded-full flex items-center justify-center text-primary-foreground font-medium">
        {entry.username.charAt(0)}
      </div>
      <div className="font-medium text-foreground">
        {entry.username}
        {isCurrentUser && (
          <span className="ml-2 text-xs text-primary">(你)</span>
        )}
      </div>
      <div className="text-right">
        {activeTab === 'mastery' ? (
          <div className="flex items-center gap-2 justify-end">
            <Trophy className="size-4 text-amber-600" strokeWidth={1.5} />
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
                  <span className="text-muted-foreground">{getSubTierLabel(entry.sub_tier)}</span>
                )}
              </>
            ) : (
              <span className="text-muted-foreground">未定级</span>
            )}
            <span className="flex items-center gap-1">
              <Star className="size-4 text-amber-600" strokeWidth={1.5} />
              <span className="font-bold">{entry.stars ?? 0}</span>
            </span>
          </div>
        )}
      </div>
    </div>
  )
}
