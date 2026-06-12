'use client'

import {
  FileText,
  Star,
  Lightbulb,
  Flame,
  Calendar,
  Check,
  Sparkles,
  Trophy,
} from 'lucide-react'
import { cn } from '@/lib/utils'

// ── 常量 ──

const STREAK_MILESTONES = [7, 14, 30, 100] as const

interface MultiplierThreshold {
  threshold: number
  text: string
  color: string
}

const STREAK_MULTIPLIER_THRESHOLDS: MultiplierThreshold[] = [
  { threshold: 2.0, text: '2x', color: 'bg-purple-500/20 text-purple-600' },
  { threshold: 1.5, text: '1.5x', color: 'bg-blue-500/20 text-blue-600' },
  { threshold: 1.2, text: '1.2x', color: 'bg-green-500/20 text-green-600' },
]

// ── Crown 图标 (lucide-react 中没有直接的 crown 图标) ──

const CrownIcon = ({ className }: { className?: string }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="currentColor"
    className={className}
  >
    <path d="M2 4l3 12h14l3-12-6 7-4-7-4 7-6-7zm3 14h14v2H5v-2z" />
  </svg>
)

// ── 类型 ──

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

interface TierInfo {
  days: number
  tier: string
  targetDays: number
  iconType: 'crown' | 'trophy' | 'sparkles' | 'flame'
}

// ── 辅助函数 ──

function getMultiplierBadge(streakMultiplier: number) {
  for (const item of STREAK_MULTIPLIER_THRESHOLDS) {
    if (streakMultiplier >= item.threshold) {
      return { text: item.text, color: item.color }
    }
  }
  return null
}

function getNextTierInfo(streakDays: number, lang: 'zh' | 'en'): TierInfo | null {
  const lastMilestone = STREAK_MILESTONES[STREAK_MILESTONES.length - 1]
  if (streakDays >= lastMilestone) return null

  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  for (let i = STREAK_MILESTONES.length - 2; i >= 0; i--) {
    if (streakDays >= STREAK_MILESTONES[i]) {
      const currentTier = STREAK_MILESTONES[i]
      const nextTarget = STREAK_MILESTONES[i + 1]
      const iconType: TierInfo['iconType'] =
        nextTarget === STREAK_MILESTONES[3] ? 'crown'
          : nextTarget === STREAK_MILESTONES[2] ? 'trophy'
            : nextTarget === STREAK_MILESTONES[1] ? 'sparkles'
              : 'flame'

      return {
        days: nextTarget - streakDays,
        tier: `${currentTier}${t('天成就', 'd Goal')}`,
        targetDays: nextTarget,
        iconType,
      }
    }
  }

  const firstMilestone = STREAK_MILESTONES[0]
  return {
    days: firstMilestone - streakDays,
    tier: `${firstMilestone}${t('天成就', 'd Goal')}`,
    targetDays: firstMilestone,
    iconType: 'flame',
  }
}

// ── 子组件 ──

function TierIcon({ type, className }: { type: TierInfo['iconType']; className?: string }) {
  switch (type) {
    case 'crown':
      return <CrownIcon className={className} />
    case 'trophy':
      return <Trophy className={className} strokeWidth={1.5} />
    case 'sparkles':
      return <Sparkles className={className} strokeWidth={1.5} />
    case 'flame':
      return <Flame className={className} strokeWidth={1.5} />
  }
}

function CalendarTags({
  lunarStr,
  solarTerm,
  holiday,
  className,
}: {
  lunarStr?: string
  solarTerm?: string
  holiday?: string
  className?: string
}) {
  if (!lunarStr && !solarTerm && !holiday) return null

  return (
    <div className={cn('flex flex-wrap gap-1', className)}>
      {lunarStr && <span className="text-xs text-muted-foreground">{lunarStr}</span>}
      {solarTerm && (
        <span className="text-xs px-1.5 py-0.5 bg-amber-500/20 text-amber-600 rounded-md">
          {solarTerm}
        </span>
      )}
      {holiday && (
        <span className="text-xs px-1.5 py-0.5 bg-red-500/20 text-red-600 rounded-md">
          {holiday}
        </span>
      )}
    </div>
  )
}

function TotalCheckin({
  totalCheckinDays,
  t,
}: {
  totalCheckinDays: number
  t: (zh: string, en: string) => string
}) {
  if (totalCheckinDays <= 0) return null
  return (
    <p className="text-xs text-muted-foreground">
      {t('累计打卡', 'Total')}
      {totalCheckinDays}
      {t('天', 'd')}
    </p>
  )
}

function NextTierProgress({
  streakDays,
  nextTierInfo,
  t,
}: {
  streakDays: number
  nextTierInfo: TierInfo
  t: (zh: string, en: string) => string
}) {
  const progressPercent = Math.min(100, (streakDays / nextTierInfo.targetDays) * 100)

  return (
    <div className="flex flex-col gap-y-1">
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <div className="flex items-center gap-1">
          <TierIcon type={nextTierInfo.iconType} className="size-3 text-amber-500" />
          <span>
            {t('距离', 'Next')}
            {nextTierInfo.tier}
          </span>
        </div>
        <span className="font-medium text-foreground">
          {nextTierInfo.days}
          {t('天', 'd')}
        </span>
      </div>
      <div className="w-full bg-secondary rounded-md h-1.5">
        <div
          className="bg-foreground h-1.5 rounded-md transition-all"
          style={{ width: `${progressPercent}%` }}
        />
      </div>
    </div>
  )
}

function StreakBonus({
  streakDays,
  streakMultiplier,
  t,
}: {
  streakDays: number
  streakMultiplier: number
  t: (zh: string, en: string) => string
}) {
  if (streakMultiplier <= 1) return null

  return (
    <div className="text-xs text-muted-foreground bg-secondary rounded-lg p-2">
      <p className="font-medium text-foreground">{t('连续打卡加成', 'Streak Bonus')}</p>
      <p>
        {t('连续打卡', 'Streak')}
        {streakDays}
        {t('天', 'd')} {t('可获得', 'can earn')} {streakMultiplier}x {t('经验值加成', 'XP bonus')}
      </p>
    </div>
  )
}

// ── 主组件 ──

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
  nextTierDays,
  xpEarnedToday,
}: QuickToolsProps) {
  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  const now = new Date()
  const dateStr = now.toLocaleDateString('zh-CN', {
    month: 'long',
    day: 'numeric',
    weekday: 'short',
  })

  const nextTierInfo = getNextTierInfo(streakDays, lang)

  const tools = [
    {
      icon: FileText,
      label: t('错题本', 'Wrong'),
      count: wrongCount,
      onClick: onWrongClick,
    },
    {
      icon: Star,
      label: t('收藏夹', 'Favorites'),
      count: favoritesCount,
      onClick: onFavoritesClick,
    },
    {
      icon: Lightbulb,
      label: t('笔记', 'Notes'),
      count: notesCount,
      onClick: onNotesClick,
    },
  ] as const

  return (
    <div className="grid grid-cols-4 gap-3">
      {tools.map((tool) => {
        const Icon = tool.icon
        return (
          <button
            key={tool.label}
            type="button"
            onClick={tool.onClick}
            className="bg-card rounded-lg border border-border p-4 hover:border-foreground/30 transition-colors text-left"
          >
            <div className="size-10 rounded-lg bg-secondary border border-border flex items-center justify-center mb-2">
              <Icon className="size-5 text-foreground" strokeWidth={1.5} />
            </div>
            <p className="text-sm font-medium text-foreground truncate">{tool.label}</p>
            {tool.count > 0 && (
              <p className="text-xl font-bold text-foreground">{tool.count}</p>
            )}
          </button>
        )
      })}

      {/* 打卡模块 */}
      <div className="bg-card rounded-lg border border-border overflow-hidden">
        {/* 未打卡状态 */}
        {!isCheckedIn && (
          <div className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <Calendar className="size-4 text-foreground" strokeWidth={1.5} />
                <span className="text-xs text-muted-foreground">{dateStr}</span>
              </div>
              <CalendarTags lunarStr={lunarStr} solarTerm={solarTerm} holiday={holiday} />
            </div>
            <button
              type="button"
              onClick={onCheckIn}
              className="w-full mt-3 px-3 py-1.5 bg-foreground text-background rounded-lg text-xs font-medium hover:bg-foreground/90 transition-colors"
            >
              {t('打卡', 'Check')}
            </button>
            <div className="mt-3 flex flex-col gap-y-2">
              <TotalCheckin totalCheckinDays={totalCheckinDays} t={t} />
              {nextTierInfo && (
                <NextTierProgress streakDays={streakDays} nextTierInfo={nextTierInfo} t={t} />
              )}
              <StreakBonus streakDays={streakDays} streakMultiplier={streakMultiplier} t={t} />
            </div>
          </div>
        )}

        {/* 已打卡状态 */}
        {isCheckedIn && (
          <div className="p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-1.5">
                <Calendar className="size-4 text-foreground" strokeWidth={1.5} />
                <span className="text-xs text-muted-foreground">{dateStr}</span>
              </div>
              <div className="flex items-center gap-1 px-2 py-1 bg-emerald-500/20 text-emerald-600 rounded-md text-xs font-medium">
                <Check className="size-3" strokeWidth={1.5} />
                {t('已打卡', 'Done')}
              </div>
            </div>
            <CalendarTags
              lunarStr={lunarStr}
              solarTerm={solarTerm}
              holiday={holiday}
              className="mb-3"
            />
            <TotalCheckin totalCheckinDays={totalCheckinDays} t={t} />
            <div className="mt-3 flex flex-col gap-y-2">
              {nextTierInfo && (
                <NextTierProgress streakDays={streakDays} nextTierInfo={nextTierInfo} t={t} />
              )}
              <StreakBonus streakDays={streakDays} streakMultiplier={streakMultiplier} t={t} />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
