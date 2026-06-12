'use client'

import { Flame, Clock, Pin, Megaphone } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Panel, PanelHeader } from '@/components/layout'

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
    <Panel>
      <PanelHeader title={t('分类', 'Categories')} />
      <div className="p-2 flex flex-col gap-y-1">
        {CATEGORIES.map(cat => {
          const Icon = cat.icon
          const isActive = activeCategory === cat.key

          return (
            <Button
              key={cat.key}
              variant={isActive ? 'default' : 'ghost'}
              onClick={() => onCategoryChange(cat.key)}
              className="w-full justify-start gap-3"
            >
              <Icon className="size-4" strokeWidth={1.5} />
              <span>{t(cat.zh, cat.en)}</span>
            </Button>
          )
        })}
      </div>
    </Panel>
  )
}
