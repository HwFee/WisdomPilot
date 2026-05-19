'use client'

import { useState } from 'react'
import { FileText, Star, Lightbulb, Flame, Calendar, Check, Sparkles, ChevronDown, ChevronUp, Trophy, Clock, Gift } from 'lucide-react'
import { LazyMotion, domAnimation, m } from 'framer-motion'
import { staggerContainer, staggerItem } from '@/lib/animations'

// Crown图标组件 (lucide-react中没有直接的crown图标)
const CrownIcon = ({ className }: { className?: string }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="currentColor"
    className={className}
  >
    <path d="M2 4l3 12h14l3-12-6 7-4-7-4 7-6-7zm3 14h14v2H5v-2z"/>
  </svg>
)

interface QuickToolsProps {
  wrongCount?: number
  favoritesCount?: number
  notesCount?: number
  streakDays?: number
  totalCheckinDays?: number
  isCheckedIn?: boolean
  onWrongClick?: () => void
  onFavoritesClick?: () => void
  onNotesClick?: () => void
  onCheckIn?: () => void
  lang?: 'zh' | 'en'
  // Enhanced check-in fields
  lunarStr?: string
  solarTerm?: string
  holiday?: string
  streakMultiplier?: number
  // Additional details
  nextTierDays?: number | null
  xpEarnedToday?: number
}

export function QuickTools({
  wrongCount = 0,
  favoritesCount = 0,
  notesCount = 0,
  streakDays = 0,
  totalCheckinDays = 0,
  isCheckedIn = false,
  onWrongClick,
  onFavoritesClick,
  onNotesClick,
  onCheckIn,
  lang = 'zh',
  lunarStr,
  solarTerm,
  holiday,
  streakMultiplier = 1.0,
  nextTierDays = null,
  xpEarnedToday = 0,
}: QuickToolsProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  const now = new Date()
  const dateStr = now.toLocaleDateString('zh-CN', {
    month: 'long',
    day: 'numeric',
    weekday: 'short',
  })

  const getMultiplierBadge = () => {
    if (streakMultiplier >= 2.0) return { text: '2x', color: 'bg-purple-500/20 text-purple-600' }
    if (streakMultiplier >= 1.5) return { text: '1.5x', color: 'bg-blue-500/20 text-blue-600' }
    if (streakMultiplier >= 1.2) return { text: '1.2x', color: 'bg-green-500/20 text-green-600' }
    return null
  }

  const multiplierBadge = getMultiplierBadge()

  // Calculate next tier info - 使用图标组件替代emoji
  const getNextTierInfo = () => {
    if (streakDays >= 100) return null
    if (streakDays >= 30) return { days: 100 - streakDays, tier: '100天成就', iconComponent: <CrownIcon className="size-3" />, targetDays: 100 }
    if (streakDays >= 14) return { days: 30 - streakDays, tier: '30天成就', iconComponent: <Trophy className="size-3" />, targetDays: 30 }
    if (streakDays >= 7) return { days: 14 - streakDays, tier: '14天成就', iconComponent: <Sparkles className="size-3" />, targetDays: 14 }
    return { days: 7 - streakDays, tier: '7天成就', iconComponent: <Flame className="size-3" />, targetDays: 7 }
  }

  const nextTierInfo = getNextTierInfo()

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
    <LazyMotion features={domAnimation}>
      <m.div
        variants={staggerContainer}
        initial="initial"
        animate="animate"
        className="grid grid-cols-4 gap-3"
      >
      {/* 错题本、收藏夹、笔记 */}
      {tools.map((tool) => {
        const Icon = tool.icon
        return (
          <m.button
            key={tool.label}
            variants={staggerItem}
            whileHover={{ scale: 1.02, y: -2 }}
            whileTap={{ scale: 0.98 }}
            onClick={tool.onClick}
            className="bg-card rounded-xl border border-border p-4 hover:border-primary/30 hover:shadow-md transition-all text-left group"
          >
            <div className={`size-10 rounded-lg ${tool.bgColor} flex items-center justify-center mb-2 group-hover:scale-110 transition-transform`}>
              <Icon className={`size-5 ${tool.color}`} />
            </div>
            <p className="text-sm font-medium text-foreground truncate">{tool.label}</p>
            {tool.count !== undefined && tool.count > 0 && (
              <p className={`text-xl font-bold ${tool.color}`}>{tool.count}</p>
            )}
          </m.button>
        )
      })}

      {/* 打卡模块 - 根据打卡状态显示不同内容 */}
      <m.div
        variants={staggerItem}
        whileHover={{ scale: 1.01 }}
        className="bg-gradient-to-br from-orange-500/10 to-orange-500/5 rounded-xl border border-orange-500/20 overflow-hidden"
      >
        {/* 打卡前：只显示日期 */}
        {!isCheckedIn && (
          <div className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <Calendar className="size-4 text-orange-500" />
                <span className="text-xs text-muted-foreground">{dateStr}</span>
              </div>
              {(lunarStr || solarTerm || holiday) && (
                <div className="flex flex-wrap gap-1">
                  {lunarStr && (
                    <span className="text-xs text-muted-foreground">{lunarStr}</span>
                  )}
                  {solarTerm && (
                    <span className="text-xs px-1.5 py-0.5 bg-amber-500/20 text-amber-600 rounded-full">
                      {solarTerm}
                    </span>
                  )}
                  {holiday && (
                    <span className="text-xs px-1.5 py-0.5 bg-red-500/20 text-red-600 rounded-full">
                      {holiday}
                    </span>
                  )}
                </div>
              )}
            </div>
            <button type="button"
              onClick={onCheckIn}
              className="w-full mt-3 px-3 py-1.5 bg-orange-500 text-white rounded-full text-xs font-medium hover:bg-orange-600 transition-colors"
            >
              {t('打卡', 'Check')}
            </button>
            {/* 占位内容，让打卡前高度与打卡后一致 */}
            <div className="mt-3">
              {totalCheckinDays > 0 && (
                <p className="text-xs text-muted-foreground">
                  {t('累计打卡', 'Total')}{totalCheckinDays}{t('天', 'd')}
                </p>
              )}
              {nextTierInfo && (
                <div className="gap-y-1 mt-2">
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <div className="flex items-center gap-1">
                      <Trophy className="size-3 text-amber-500" />
                      <span>{t('距离', 'Next')}{nextTierInfo.tier}</span>
                    </div>
                    <span className="font-medium text-foreground">{nextTierInfo.days}{t('天', 'd')}</span>
                  </div>
                  <div className="w-full bg-orange-500/20 rounded-full h-1.5">
                    <div
                      className="bg-orange-500 h-1.5 rounded-full"
                      style={{
                        width: `${Math.min(100, (streakDays / nextTierInfo.targetDays) * 100)}%`
                      }}
                    />
                  </div>
                </div>
              )}
              {streakMultiplier > 1 && (
                <div className="text-xs text-muted-foreground bg-orange-500/10 rounded-lg p-2 mt-2">
                  <p className="font-medium text-orange-600">{t('连续打卡加成', 'Streak Bonus')}</p>
                  <p>{t('连续打卡', 'Streak')}{streakDays}{t('天', 'd')} {t('可获得', 'can earn')} {streakMultiplier}x {t('经验值加成', 'XP bonus')}</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* 打卡后：显示完整内容 */}
        {isCheckedIn && (
          <div className="p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-1.5">
                <Calendar className="size-4 text-orange-500" />
                <span className="text-xs text-muted-foreground">{dateStr}</span>
              </div>
              <div className="flex items-center gap-1 px-2 py-1 bg-emerald-500/20 text-emerald-600 rounded-full text-xs font-medium">
                <Check className="size-3" />
                {t('已打卡', 'Done')}
              </div>
            </div>

            {(lunarStr || solarTerm || holiday) && (
              <div className="flex flex-wrap gap-1 mb-3">
                {lunarStr && (
                  <span className="text-xs text-muted-foreground">{lunarStr}</span>
                )}
                {solarTerm && (
                  <span className="text-xs px-1.5 py-0.5 bg-amber-500/20 text-amber-600 rounded-full">
                    {solarTerm}
                  </span>
                )}
                {holiday && (
                  <span className="text-xs px-1.5 py-0.5 bg-red-500/20 text-red-600 rounded-full">
                    {holiday}
                  </span>
                )}
              </div>
            )}

            {totalCheckinDays > 0 && (
              <p className="text-xs text-muted-foreground mt-1">
                {t('累计打卡', 'Total')}{totalCheckinDays}{t('天', 'd')}
              </p>
            )}

            {/* 成就进度 */}
            {nextTierInfo && (
              <div className="gap-y-1 mt-3">
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <Trophy className="size-3 text-amber-500" />
                    <span>{t('距离', 'Next')}{nextTierInfo.tier}</span>
                  </div>
                  <span className="font-medium text-foreground">{nextTierInfo.days}{t('天', 'd')}</span>
                </div>
                <div className="w-full bg-orange-500/20 rounded-full h-1.5">
                  <div
                    className="bg-orange-500 h-1.5 rounded-full transition-all"
                    style={{
                      width: `${Math.min(100, (streakDays / nextTierInfo.targetDays) * 100)}%`
                    }}
                  />
                </div>
              </div>
            )}

            {/* 打卡加成说明 */}
            {streakMultiplier > 1 && (
              <div className="text-xs text-muted-foreground bg-orange-500/10 rounded-lg p-2 mt-3">
                <p className="font-medium text-orange-600">{t('连续打卡加成', 'Streak Bonus')}</p>
                <p>{t('连续打卡', 'Streak')}{streakDays}{t('天', 'd')} {t('可获得', 'can earn')} {streakMultiplier}x {t('经验值加成', 'XP bonus')}</p>
              </div>
            )}
          </div>
        )}
      </m.div>
      </m.div>
    </LazyMotion>
  )
}
