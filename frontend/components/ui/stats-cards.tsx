'use client'

import { BookOpen, Trophy, Play, Clock } from 'lucide-react'

interface StageStats {
  totalStages: number
  completedStages: number
  inProgressStages: number
}

interface StatsCardsProps {
  stageStats: StageStats
  totalCourses?: number
  learningTimeSeconds?: number
  lang: 'zh' | 'en'
  isLoading?: boolean
}

export function StatsCards({ stageStats, totalCourses = 8, learningTimeSeconds = 0, lang, isLoading }: StatsCardsProps) {
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
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-card rounded-2xl p-5 border border-border animate-pulse">
            <div className="h-10 w-10 bg-muted rounded-xl mb-3" />
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
      label: t('课程', 'Courses'),
      value: totalCourses,
      sublabel: t('门课程', 'courses'),
      gradient: 'from-blue-500 to-cyan-500',
      iconBg: 'bg-blue-500/10',
      iconColor: 'text-blue-500',
    },
    {
      icon: Trophy,
      label: t('已通关', 'Completed'),
      value: stageStats.completedStages,
      sublabel: t('个关卡', 'stages'),
      gradient: 'from-green-500 to-emerald-500',
      iconBg: 'bg-green-500/10',
      iconColor: 'text-green-500',
    },
    {
      icon: Play,
      label: t('进行中', 'In Progress'),
      value: stageStats.inProgressStages,
      sublabel: t('个关卡', 'stages'),
      gradient: 'from-amber-500 to-orange-500',
      iconBg: 'bg-amber-500/10',
      iconColor: 'text-amber-500',
    },
    {
      icon: Clock,
      label: t('学习时长', 'Learning Time'),
      value: formatTime(learningTimeSeconds),
      sublabel: '',
      gradient: 'from-purple-500 to-violet-500',
      iconBg: 'bg-purple-500/10',
      iconColor: 'text-purple-500',
      isText: true,
    },
  ]

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {cards.map((card, index) => {
        const Icon = card.icon
        return (
          <div
            key={index}
            className="bg-card rounded-2xl p-5 border border-border hover:shadow-lg hover:border-primary/20 transition-all group"
          >
            <div className={`w-12 h-12 ${card.iconBg} rounded-xl flex items-center justify-center mb-3 group-hover:scale-110 transition-transform`}>
              <Icon className={`w-6 h-6 ${card.iconColor}`} />
            </div>
            <p className="text-sm text-muted-foreground mb-1">{card.label}</p>
            <div className="flex items-baseline gap-1">
              <p className={`text-3xl font-bold text-foreground ${card.isText ? 'text-2xl' : ''}`}>
                {card.value}
              </p>
              {card.sublabel && (
                <span className="text-sm text-muted-foreground">{card.sublabel}</span>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
