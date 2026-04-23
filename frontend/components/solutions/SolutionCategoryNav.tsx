'use client'

import { Flame, Clock, Pin, Megaphone } from 'lucide-react'

type CategoryType = 'hot' | 'new' | 'pinned' | 'announcement'

interface SolutionCategoryNavProps {
  activeCategory: CategoryType
  onCategoryChange: (category: CategoryType) => void
  lang?: 'zh' | 'en'
}

const CATEGORIES: { key: CategoryType; icon: typeof Flame; zh: string; en: string }[] = [
  { key: 'hot', icon: Flame, zh: '热门', en: 'Hot' },
  { key: 'new', icon: Clock, zh: '最新', en: 'New' },
  { key: 'pinned', icon: Pin, zh: '置顶', en: 'Pinned' },
  { key: 'announcement', icon: Megaphone, zh: '公告', en: 'Announcement' },
]

export function SolutionCategoryNav({ activeCategory, onCategoryChange, lang = 'zh' }: SolutionCategoryNavProps) {
  const t = (zh: string, en: string) => lang === 'zh' ? zh : en

  return (
    <nav className="bg-card rounded-2xl border border-border p-4 sticky top-24">
      <h2 className="text-sm font-medium text-muted-foreground mb-3 px-3">
        {t('分类', 'Categories')}
      </h2>
      <div className="space-y-1">
        {CATEGORIES.map(cat => {
          const Icon = cat.icon
          const isActive = activeCategory === cat.key

          return (
            <button type="button"
              key={cat.key}
              onClick={() => onCategoryChange(cat.key)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                isActive
                  ? 'bg-primary text-primary-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-foreground hover:bg-muted'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{t(cat.zh, cat.en)}</span>
            </button>
          )
        })}
      </div>
    </nav>
  )
}
