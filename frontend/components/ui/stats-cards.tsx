'use client'

import { BookOpen, Trophy, TrendingUp, Clock, Flame } from 'lucide-react'
import { LearningStatistics } from '@/lib/api'

interface StatsCardsProps {
  stats: LearningStatistics | null
  totalChapters: number
  lang: 'zh' | 'en'
  isLoading?: boolean
}

export function StatsCards({ stats, totalChapters, lang, isLoading }: StatsCardsProps) {
  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  const formatTime = (seconds: number): string => {
    if (seconds < 60) return `${seconds}s`
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`
    const hours = Math.floor(seconds / 3600)
    const mins = Math.floor((seconds % 3600) / 60)
    return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`
  }

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-card rounded-xl p-5 border border-border animate-pulse">
            <div className="h-10 w-10 bg-muted rounded-lg mb-3" />
            <div className="h-4 bg-muted rounded w-20 mb-2" />
            <div className="h-8 bg-muted rounded w-16" />
          </div>
        ))}
      </div>
    )
  }

  const cards = [
    {
      icon: BookOpen,
      label: t('课程章节', 'Chapters'),
      value: totalChapters,
      color: 'blue',
      bgColor: 'bg-blue-50',
      iconColor: 'text-blue-600',
    },
    {
      icon: Trophy,
      label: t('已完成', 'Completed'),
      value: stats?.completed_chapters ?? 0,
      color: 'emerald',
      bgColor: 'bg-emerald-50',
      iconColor: 'text-emerald-600',
    },
    {
      icon: TrendingUp,
      label: t('进行中', 'In Progress'),
      value: stats?.in_progress_chapters ?? 0,
      color: 'amber',
      bgColor: 'bg-amber-50',
      iconColor: 'text-amber-600',
    },
    {
      icon: Clock,
      label: t('学习时长', 'Hours'),
      value: formatTime(stats?.total_learning_time_seconds ?? 0),
      color: 'violet',
      bgColor: 'bg-violet-50',
      iconColor: 'text-violet-600',
      isText: true,
    },
  ]

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
      {cards.map((card, index) => {
        const Icon = card.icon
        return (
          <div
            key={index}
            className="bg-card rounded-xl p-5 border border-border hover:shadow-md transition-shadow"
          >
            <div className={`w-10 h-10 ${card.bgColor} rounded-lg flex items-center justify-center mb-3`}>
              <Icon className={`w-5 h-5 ${card.iconColor}`} />
            </div>
            <p className="text-sm text-muted-foreground mb-1">{card.label}</p>
            <p className={`text-3xl font-bold text-foreground ${card.isText ? 'text-lg' : ''}`}>
              {card.value}
            </p>
          </div>
        )
      })}
    </div>
  )
}
