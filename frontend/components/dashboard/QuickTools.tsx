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
  Crown,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Panel, PanelHeader, ToolItem } from '@/components/layout'

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
  lunarStr?: string
  solarTerm?: string
  holiday?: string
  streakMultiplier?: number
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
      return <Crown className={className} strokeWidth={1.5} />
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
}: QuickToolsProps) {
  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  const now = new Date()
  const dateStr = now.toLocaleDateString('zh-CN', {
    month: 'long',
    day: 'numeric',
    weekday: 'short',
  })

  const nextTierInfo = getNextTierInfo(streakDays, lang)
  const multiplierBadge = getMultiplierBadge(streakMultiplier)

  const tools = [
    {
      icon: <FileText className="size-5 text-foreground" strokeWidth={1.5} />,
      iconClassName: 'bg-red-500/10 text-red-600',
      name: t('错题本', 'Wrong'),
      desc: wrongCount > 0 ? `${wrongCount} ${t('道错题待复习', 'questions to review')}` : t('复习做错的题目', 'Review wrong answers'),
      onClick: onWrongClick,
    },
    {
      icon: <Star className="size-5 text-foreground" strokeWidth={1.5} />,
      iconClassName: 'bg-amber-500/10 text-amber-600',
      name: t('收藏夹', 'Favorites'),
      desc: favoritesCount > 0 ? `${favoritesCount} ${t('个收藏知识点', 'favorited items')}` : t('查看收藏的内容', 'View favorites'),
      onClick: onFavoritesClick,
    },
    {
      icon: <Lightbulb className="size-5 text-foreground" strokeWidth={1.5} />,
      iconClassName: 'bg-green-500/10 text-green-600',
      name: t('笔记', 'Notes'),
      desc: notesCount > 0 ? `${notesCount} ${t('条学习笔记', 'notes')}` : t('记录学习心得', 'Take notes'),
      onClick: onNotesClick,
    },
  ]

  return (
    <div className="flex flex-col gap-6">
      <Panel>
        <PanelHeader title={t('快捷入口', 'Quick Tools')} />
        <div>
          {tools.map((tool) => (
            <ToolItem key={tool.name} {...tool} />
          ))}
        </div>
      </Panel>

      <Panel>
        <PanelHeader title={t('签到', 'Check In')} />
        <div className="px-8 py-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-1.5">
              <Calendar className="size-4 text-foreground" strokeWidth={1.5} />
              <span className="text-xs text-muted-foreground">{dateStr}</span>
            </div>
            {multiplierBadge && (
              <div className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${multiplierBadge.color}`}>
                <Sparkles className="size-3" />
                {multiplierBadge.text}
              </div>
            )}
          </div>

          <CalendarTags lunarStr={lunarStr} solarTerm={solarTerm} holiday={holiday} className="mb-4" />

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <Flame className={`size-5 ${streakDays > 0 ? 'text-orange-500' : 'text-muted-foreground'}`} />
                <span className="text-2xl font-bold text-foreground">{streakDays}</span>
                <span className="text-sm text-muted-foreground">{t('天连续', 'streak')}</span>
              </div>
              {totalCheckinDays > 0 && (
                <div className="text-sm text-muted-foreground">
                  <span className="font-medium text-foreground">{totalCheckinDays}</span>
                  <span className="ml-1">{t('天打卡', 'total')}</span>
                </div>
              )}
            </div>

            {isCheckedIn ? (
              <div className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-500/20 text-emerald-600 rounded-full text-sm font-medium">
                <Check className="size-4" />
                {t('已打卡', 'Done')}
              </div>
            ) : (
              <button
                type="button"
                onClick={onCheckIn}
                className="px-4 py-1.5 bg-foreground text-background text-sm font-medium hover:bg-foreground/90 transition-colors"
              >
                {t('打卡', 'Check')}
              </button>
            )}
          </div>

          <div className="mt-4 flex flex-col gap-y-3">
            <TotalCheckin totalCheckinDays={totalCheckinDays} t={t} />
            {nextTierInfo && (
              <NextTierProgress streakDays={streakDays} nextTierInfo={nextTierInfo} t={t} />
            )}
            <StreakBonus streakDays={streakDays} streakMultiplier={streakMultiplier} t={t} />
          </div>
        </div>
      </Panel>
    </div>
  )
}
