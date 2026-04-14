'use client'

import { FileText, Star, Lightbulb, Flame, Calendar, Check } from 'lucide-react'

interface QuickToolsProps {
  wrongCount?: number
  favoritesCount?: number
  notesCount?: number
  streakDays?: number
  isCheckedIn?: boolean
  onWrongClick?: () => void
  onFavoritesClick?: () => void
  onNotesClick?: () => void
  onCheckIn?: () => void
  lang?: 'zh' | 'en'
}

export function QuickTools({
  wrongCount = 0,
  favoritesCount = 0,
  notesCount = 0,
  streakDays = 0,
  isCheckedIn = false,
  onWrongClick,
  onFavoritesClick,
  onNotesClick,
  onCheckIn,
  lang = 'zh'
}: QuickToolsProps) {
  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  const now = new Date()
  const dateStr = now.toLocaleDateString('zh-CN', {
    month: 'long',
    day: 'numeric',
    weekday: 'short',
  })

  const tools = [
    {
      icon: FileText,
      label: t('错题本', 'Wrong'),
      count: wrongCount,
      onClick: onWrongClick,
      color: 'text-red-500',
      bgColor: 'bg-red-500/10',
    },
    {
      icon: Star,
      label: t('收藏夹', 'Favorites'),
      count: favoritesCount,
      onClick: onFavoritesClick,
      color: 'text-yellow-500',
      bgColor: 'bg-yellow-500/10',
    },
    {
      icon: Lightbulb,
      label: t('笔记', 'Notes'),
      count: notesCount,
      onClick: onNotesClick,
      color: 'text-blue-500',
      bgColor: 'bg-blue-500/10',
    },
  ]

  return (
    <div className="grid grid-cols-4 gap-3">
      {/* 错题本、收藏夹、笔记 */}
      {tools.map((tool) => {
        const Icon = tool.icon
        return (
          <button
            key={tool.label}
            onClick={tool.onClick}
            className="bg-card rounded-xl border border-border p-4 hover:border-primary/30 hover:shadow-md transition-all text-left group"
          >
            <div className={`w-10 h-10 rounded-lg ${tool.bgColor} flex items-center justify-center mb-2 group-hover:scale-110 transition-transform`}>
              <Icon className={`w-5 h-5 ${tool.color}`} />
            </div>
            <p className="text-sm font-medium text-foreground truncate">{tool.label}</p>
            {tool.count !== undefined && tool.count > 0 && (
              <p className={`text-xl font-bold ${tool.color}`}>{tool.count}</p>
            )}
          </button>
        )
      })}

      {/* 打卡模块 */}
      <div className="bg-gradient-to-br from-orange-500/10 to-orange-500/5 rounded-xl border border-orange-500/20 p-4">
        <div className="flex items-center gap-1.5 mb-2">
          <Calendar className="w-4 h-4 text-orange-500" />
          <span className="text-xs text-muted-foreground">{dateStr}</span>
        </div>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1">
            <Flame className={`w-4 h-4 ${streakDays > 0 ? 'text-orange-500' : 'text-muted-foreground'}`} />
            <span className="text-lg font-bold text-foreground">{streakDays}</span>
            <span className="text-xs text-muted-foreground">{t('天', 'd')}</span>
          </div>
          {isCheckedIn ? (
            <div className="flex items-center gap-1 px-2 py-1 bg-emerald-500/20 text-emerald-600 rounded-full text-xs font-medium">
              <Check className="w-3 h-3" />
              {t('已打卡', 'Done')}
            </div>
          ) : (
            <button
              onClick={onCheckIn}
              className="px-3 py-1.5 bg-orange-500 text-white rounded-full text-xs font-medium hover:bg-orange-600 transition-colors"
            >
              {t('打卡', 'Check')}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
