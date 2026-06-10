import { Trophy, Star } from 'lucide-react'
import { TIER_NAMES } from '@/lib/api'
import { getTierConfig } from '@/lib/icons/tier-icons'
import type { LeaderboardEntry, Tier } from '@/types/api'

interface CurrentUserCardProps {
  activeTab: 'mastery' | 'arena'
  currentUserRank: number
  currentUserData: LeaderboardEntry | null
}

export function CurrentUserCard({ activeTab, currentUserRank, currentUserData }: CurrentUserCardProps) {
  return (
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
  )
}
