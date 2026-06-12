import { Star } from 'lucide-react'
import { TIER_NAMES } from '@/lib/api'
import { getTierConfig } from '@/lib/icons/tier-icons'
import { getSubTierLabel } from '../lib/leaderboard-utils'
import { Panel, PanelHeader } from '@/components/layout'
import type { LeaderboardEntry, Tier } from '@/types/api'

interface CurrentUserCardProps {
  activeTab: 'mastery' | 'arena'
  currentUserRank: number
  currentUserData: LeaderboardEntry | null
}

export function CurrentUserCard({ activeTab, currentUserRank, currentUserData }: CurrentUserCardProps) {
  return (
    <Panel className="mb-6">
      <PanelHeader title="你的排名" count={`#${currentUserRank}`} />
      <div className="px-8 py-6">
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
                  <span className="text-muted-foreground">{getSubTierLabel(currentUserData.sub_tier)}</span>
                )}
              </>
            ) : (
              <span className="text-muted-foreground">未定级</span>
            )}
            <span className="flex items-center gap-1">
              <Star className="size-4 text-amber-600" strokeWidth={1.5} />
              <span className="font-medium">{currentUserData?.stars ?? 0}</span>
            </span>
          </div>
        )}
      </div>
    </Panel>
  )
}
