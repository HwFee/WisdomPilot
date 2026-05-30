'use client'

import { ArrowRight, Users } from 'lucide-react'
import Link from 'next/link'

interface CourseCardProps {
  id: number
  code: string
  name: string
  description: string
  gradient: string
  color: string
  difficulty: number
  learners: string
  isLoggedIn?: boolean
  onClick?: () => void
}

export function CourseCard({
  id,
  code,
  name,
  description,
  gradient,
  color,
  difficulty,
  learners,
  isLoggedIn = false,
  onClick,
}: CourseCardProps) {
  const href = isLoggedIn ? `/mastery/${id}` : '/login'

  return (
    <Link
      href={href}
      onClick={onClick}
      className="group relative p-6 rounded-2xl bg-card border border-border hover:border-primary/40 transition-all card-interactive"
    >
      {/* Difficulty indicator */}
      <div className="absolute top-4 right-4 flex gap-1">
        <div className={`size-1.5 rounded-full ${0 < difficulty ? 'bg-primary' : 'bg-muted'}`} />
        <div className={`size-1.5 rounded-full ${1 < difficulty ? 'bg-primary' : 'bg-muted'}`} />
        <div className={`size-1.5 rounded-full ${2 < difficulty ? 'bg-primary' : 'bg-muted'}`} />
        <div className={`size-1.5 rounded-full ${3 < difficulty ? 'bg-primary' : 'bg-muted'}`} />
      </div>

      {/* Icon */}
      <div className={`size-14 rounded-xl bg-gradient-to-br ${gradient} flex items-center justify-center mb-4 shadow-lg group-hover:scale-105 transition-transform`}>
        <span className="text-xl font-bold text-white">{code}</span>
      </div>

      {/* Content */}
      <h3 className="text-lg font-semibold text-foreground mb-2 group-hover:text-primary transition-colors">
        {name}
      </h3>
      <p className="text-sm text-muted-foreground mb-4 truncate-2">
        {description}
      </p>

      {/* Bottom info */}
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span className="flex items-center gap-1">
          <Users className="size-3.5" />
          {learners}
        </span>
        <span className="flex items-center gap-1 text-primary opacity-0 group-hover:opacity-100 transition-opacity">
          {isLoggedIn ? (
            <>
              {t('开始学习', 'Start')}
              <ArrowRight className="size-3" />
            </>
          ) : (
            <>
              {t('登录后学习', 'Login to start')}
              <ArrowRight className="size-3" />
            </>
          )}
        </span>
      </div>
    </Link>
  )
}

function t(zh: string, en: string): string {
  // Simple translation - in real app would use i18n
  return zh
}
