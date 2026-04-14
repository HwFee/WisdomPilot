'use client'

import { ArrowLeft, Users, Star, BookOpen } from 'lucide-react'
import Link from 'next/link'

interface CourseHeaderProps {
  id: number
  name: string
  description: string
  progress: number
  completedStages: number
  totalStages: number
  learners: string
  difficulty: number
  color: string
  lang?: 'zh' | 'en'
}

export function CourseHeader({
  id,
  name,
  description,
  progress,
  completedStages,
  totalStages,
  learners,
  difficulty,
  color,
  lang = 'zh',
}: CourseHeaderProps) {
  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  return (
    <div className="bg-card rounded-2xl border border-border overflow-hidden">
      {/* Course Banner */}
      <div
        className="h-32 relative"
        style={{ background: `linear-gradient(135deg, ${color}20 0%, ${color}05 100%)` }}
      >
        <div className="absolute inset-0 bg-gradient-to-t from-card to-transparent" />
      </div>

      {/* Course Info */}
      <div className="px-6 pb-6 -mt-16 relative">
        {/* Back Button */}
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          {t('返回', 'Back')}
        </Link>

        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-4">
            <div
              className="w-16 h-16 rounded-2xl flex items-center justify-center shadow-lg"
              style={{ backgroundColor: `${color}20` }}
            >
              <BookOpen className="w-8 h-8" style={{ color }} />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-foreground">{name}</h1>
              <p className="text-muted-foreground">{description}</p>
            </div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mt-6">
          <div className="flex justify-between text-sm mb-2">
            <span className="text-muted-foreground">
              {t('课程进度', 'Progress')}
            </span>
            <span className="font-medium" style={{ color }}>
              {progress}% ({completedStages}/{totalStages} {t('关', 'stages')})
            </span>
          </div>
          <div className="h-2 bg-muted rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{ width: `${progress}%`, backgroundColor: color }}
            />
          </div>
        </div>

        {/* Stats */}
        <div className="flex items-center gap-6 mt-4 text-sm text-muted-foreground">
          <div className="flex items-center gap-1">
            <Users className="w-4 h-4" />
            {learners} {t('学习者', 'learners')}
          </div>
          <div className="flex items-center gap-1">
            <Star className="w-4 h-4" />
            {t('难度', 'Difficulty')}:
            {[...Array(4)].map((_, i) => (
              <span
                key={i}
                className={`w-1.5 h-1.5 rounded-full ${
                  i < difficulty ? 'text-yellow-500' : 'text-muted'
                }`}
                style={{ backgroundColor: i < difficulty ? '#F59E0B' : undefined }}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
