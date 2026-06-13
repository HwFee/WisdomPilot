'use client'

import { Wallet, ArrowUpRight, ArrowDownRight, Scale } from 'lucide-react'
import { StatsGrid, StatCell } from '@/components/layout'
import { formatNumber } from '../lib/core-utils'

interface CoreStatsProps {
  balance: number
  totalEarned: number
  totalSpent: number
  earnedToday: number
  spentToday: number
}

interface StatItem {
  icon: typeof Wallet
  label: string
  value: number
}

export function CoreStats({ balance, totalEarned, totalSpent, earnedToday, spentToday }: CoreStatsProps) {
  const stats: StatItem[] = [
    { icon: Wallet, label: '当前余额', value: balance },
    { icon: ArrowUpRight, label: '累计获取', value: totalEarned },
    { icon: ArrowDownRight, label: '累计消耗', value: totalSpent },
    { icon: Scale, label: '今日净增', value: earnedToday - spentToday },
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
              <p className="text-3xl font-bold text-foreground tracking-tight">
                {formatNumber(stat.value)}
              </p>
              <p className="text-sm text-muted-foreground mt-1">{stat.label}</p>
            </div>
          </div>
        </StatCell>
      ))}
    </StatsGrid>
  )
}
