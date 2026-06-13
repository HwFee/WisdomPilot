'use client'

import { Trophy, Shield, Star, TrendingUp } from 'lucide-react'
import { StatsGrid, StatCell } from '@/components/layout'
import { getFullTierName, formatNumber } from '../lib/tier-utils'

interface TierStatsProps {
  tier: string
  subTier: number
  stars: number
  starsNeeded: number
  protectionRemaining: number
  highestFullName?: string
}

interface StatItem {
  icon: typeof Trophy
  label: string
  value: string | number
  accent?: string
}

export function TierStats({
  tier,
  subTier,
  stars,
  starsNeeded,
  protectionRemaining,
  highestFullName,
}: TierStatsProps) {
  const fullName = getFullTierName(tier, subTier)
  const stats: StatItem[] = [
    { icon: Trophy, label: '当前段位', value: fullName },
    { icon: Star, label: '当前星星', value: formatNumber(stars) },
    { icon: TrendingUp, label: '升级还需', value: formatNumber(Math.max(0, starsNeeded - stars)) },
    { icon: Shield, label: '保护次数', value: formatNumber(protectionRemaining) },
  ]

  return (
    <StatsGrid>
      {stats.map((stat) => (
        <StatCell key={stat.label}>
          <div className="flex flex-col justify-between h-full">
            <div className="w-10 h-10 rounded-lg bg-secondary border border-border flex items-center justify-center mb-4">
              <stat.icon className="w-5 h-5 text-foreground" strokeWidth={1.5} />
            </div>
            <div>
              <p className="text-3xl font-bold text-foreground tracking-tight">{stat.value}</p>
              <p className="text-sm text-muted-foreground mt-1">{stat.label}</p>
              {stat.label === '当前段位' && highestFullName && highestFullName !== fullName && (
                <p className="text-xs text-primary mt-2 font-medium">
                  最高 {highestFullName}
                </p>
              )}
            </div>
          </div>
        </StatCell>
      ))}
    </StatsGrid>
  )
}
