'use client'

import { CheckCircle, Lock, Play, Circle } from 'lucide-react'

interface Chapter {
  id: number
  title: string
  status: 'locked' | 'unlocked' | 'in_progress' | 'completed'
  progress?: number
}

interface ChapterTimelineProps {
  chapters: Chapter[]
  currentChapterId?: number
  onChapterClick: (chapterId: number) => void
  lang?: 'zh' | 'en'
}

export function ChapterTimeline({
  chapters,
  currentChapterId,
  onChapterClick,
  lang = 'zh',
}: ChapterTimelineProps) {
  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  const getStatusIcon = (status: Chapter['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-emerald-500" />
      case 'in_progress':
        return <Play className="w-5 h-5 text-blue-500" />
      case 'locked':
        return <Lock className="w-5 h-5 text-muted-foreground" />
      default:
        return <Circle className="w-5 h-5 text-muted-foreground/50" />
    }
  }

  const getStatusColor = (status: Chapter['status']) => {
    switch (status) {
      case 'completed':
        return 'text-emerald-500'
      case 'in_progress':
        return 'text-blue-500'
      case 'locked':
        return 'text-muted-foreground'
      default:
        return 'text-muted-foreground/50'
    }
  }

  return (
    <div className="bg-card rounded-2xl border border-border p-6">
      <h3 className="font-semibold text-foreground mb-6">{t('章节列表', 'Chapter List')}</h3>

      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-[18px] top-0 bottom-0 w-0.5 bg-border" />

        {/* Chapter nodes */}
        <div className="space-y-4">
          {chapters.map((chapter, index) => {
            const isClickable = chapter.status !== 'locked'
            const isLast = index === chapters.length - 1

            return (
              <div key={chapter.id} className="relative flex items-start gap-4">
                {/* Node */}
                <div
                  className={`relative z-10 w-9 h-9 rounded-full flex items-center justify-center transition-all ${
                    isClickable
                      ? 'bg-card border-2 border-border hover:border-primary cursor-pointer'
                      : 'bg-card border-2 border-border'
                  }`}
                  onClick={() => isClickable && onChapterClick(chapter.id)}
                >
                  {getStatusIcon(chapter.status)}
                </div>

                {/* Content */}
                <div className="flex-1 pb-6">
                  <div
                    className={`flex items-center justify-between ${
                      !isClickable ? 'opacity-50' : ''
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span className={`text-sm font-medium ${getStatusColor(chapter.status)}`}>
                        {index + 1}. {chapter.title}
                      </span>
                      {(chapter.id === currentChapterId || chapter.status === 'in_progress') && (
                        <span className="px-2 py-0.5 bg-blue-500/20 text-blue-500 text-xs rounded-full">
                          {t('进行中', 'In Progress')}
                        </span>
                      )}
                      {chapter.status === 'completed' && (
                        <span className="px-2 py-0.5 bg-emerald-500/20 text-emerald-500 text-xs rounded-full">
                          {t('已完成', 'Completed')}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Progress bar for in_progress */}
                  {chapter.status === 'in_progress' && chapter.progress !== undefined && (
                    <div className="mt-2">
                      <div className="h-1.5 bg-muted rounded-full overflow-hidden w-48">
                        <div
                          className="h-full bg-blue-500 rounded-full"
                          style={{ width: `${chapter.progress}%` }}
                        />
                      </div>
                    </div>
                  )}

                  {/* Status text */}
                  <p className={`text-xs mt-1 ${getStatusColor(chapter.status)}`}>
                    {chapter.status === 'locked' && t('完成上一章节解锁', 'Complete previous chapter to unlock')}
                    {chapter.status === 'unlocked' && t('可开始学习', 'Ready to start')}
                    {chapter.status === 'in_progress' && t('学习中', 'In learning')}
                    {chapter.status === 'completed' && t('已掌握', 'Mastered')}
                  </p>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
