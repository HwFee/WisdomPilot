'use client'

import { Activity } from '@/lib/api'
import { Trophy, BookOpen, Clock, Award } from 'lucide-react'

interface ActivityFeedProps {
  activities: Activity[]
  lang: 'zh' | 'en'
  isLoading?: boolean
}

const activityIcons: Record<string, typeof BookOpen> = {
  chapter_started: BookOpen,
  chapter_completed: Trophy,
  subsection_completed: BookOpen,
  session_ended: Clock,
  achievement: Award,
}

const activityColors: Record<string, string> = {
  chapter_started: 'bg-blue-100 text-blue-600',
  chapter_completed: 'bg-emerald-100 text-emerald-600',
  subsection_completed: 'bg-purple-100 text-purple-600',
  session_ended: 'bg-amber-100 text-amber-600',
  achievement: 'bg-violet-100 text-violet-600',
}

export function ActivityFeed({ activities, lang, isLoading }: ActivityFeedProps) {
  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  const formatTime = (dateStr: string): string => {
    // Parse as local time to fix timezone issue (backend returns UTC)
    const date = new Date(dateStr + 'Z')
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return lang === 'zh' ? '刚刚' : 'Just now'
    if (diffMins < 60) return lang === 'zh' ? `${diffMins}分钟前` : `${diffMins}m ago`
    if (diffHours < 24) return lang === 'zh' ? `${diffHours}小时前` : `${diffHours}h ago`
    if (diffDays < 7) return lang === 'zh' ? `${diffDays}天前` : `${diffDays}d ago`
    return date.toLocaleDateString(lang === 'zh' ? 'zh-CN' : 'en-US')
  }

  if (isLoading) {
    return (
      <div className="gap-y-4">
        {[1, 2, 3, 4, 5].map((n) => (
          <div key={`feed-skeleton-${n}`} className="flex gap-3 animate-pulse">
            <div className="size-2 bg-muted rounded-full mt-2" />
            <div className="flex-1">
              <div className="h-4 bg-muted rounded w-48 mb-2" />
              <div className="h-3 bg-muted rounded w-20" />
            </div>
          </div>
        ))}
      </div>
    )
  }

  if (activities.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <Clock className="size-12 mx-auto mb-3 opacity-50" />
        <p>{t('暂无学习记录', 'No learning records yet')}</p>
        <p className="text-sm">{t('开始学习吧！', 'Start learning!')}</p>
      </div>
    )
  }

  return (
    <div className="gap-y-4">
      {activities.map((activity, index) => {
        const Icon = activityIcons[activity.activity_type] || BookOpen
        const colorClass = activityColors[activity.activity_type] || 'bg-muted text-muted-foreground'

        return (
          <div key={activity.id} className="flex gap-3">
            <div className="flex flex-col items-center">
              <div className={`size-6 rounded-full ${colorClass} flex items-center justify-center`}>
                <Icon className="size-3" />
              </div>
              {index < activities.length - 1 && (
                <div className="w-0.5 flex-1 my-1 bg-muted" />
              )}
            </div>
            <div className="flex-1 pb-4">
              <p className="text-sm text-foreground">{activity.description}</p>
              <p className="text-xs text-muted-foreground mt-1">{formatTime(activity.created_at)}</p>
            </div>
          </div>
        )
      })}
    </div>
  )
}
