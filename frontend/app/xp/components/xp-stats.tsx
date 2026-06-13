'use client'

import { Zap, Target, TrendingUp, Award } from 'lucide-react'
import { StatsGrid, StatCell } from '@/components/layout'
import { formatNumber } from '../lib/xp-utils'

interface XpStatsProps {
  balance: number
  level: string
  totalEarned: number
  levelUpCount: number
}

interface StatItem {
  icon: typeof Zap
  label: string
  value: string | number
}

export function XpStats({ balance, level, totalEarned, levelUpCount }: XpStatsProps) {
  const stats: StatItem[] = [
    { icon: Zap, label: '当前经验', value: formatNumber(balance) },
    { icon: Award, label: '当前等级', value: level },
    { icon: TrendingUp, label: '累计获得', value: formatNumber(totalEarned) },
    { icon: Target, label: '升级次数', value: levelUpCount },
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
            </div>
          </div>
        </StatCell>
      ))}
    </StatsGrid>
  )
}
