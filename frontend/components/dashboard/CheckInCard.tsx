'use client'

import { Flame, Check, Calendar, Sparkles, Moon } from 'lucide-react'

interface CheckInCardProps {
  streakDays: number
  totalCheckinDays?: number
  isCheckedIn?: boolean
  onCheckIn: () => void
  lang?: 'zh' | 'en'
  // Enhanced fields
  lunarStr?: string
  solarTerm?: string
  holiday?: string
  streakMultiplier?: number
}

export function CheckInCard({
  streakDays,
  totalCheckinDays = 0,
  isCheckedIn = false,
  onCheckIn,
  lang = 'zh',
  lunarStr,
  solarTerm,
  holiday,
  streakMultiplier = 1.0,
}: CheckInCardProps) {
  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  const now = new Date()
  const dateStr = now.toLocaleDateString('zh-CN', {
    month: 'long',
    day: 'numeric',
    weekday: 'long',
  })

  const getMultiplierBadge = () => {
    if (streakMultiplier >= 2.0) return { text: t('2倍', '2x'), color: 'bg-purple-500/20 text-purple-600' }
    if (streakMultiplier >= 1.5) return { text: t('1.5倍', '1.5x'), color: 'bg-blue-500/20 text-blue-600' }
    if (streakMultiplier >= 1.2) return { text: t('1.2倍', '1.2x'), color: 'bg-green-500/20 text-green-600' }
    return null
  }

  const multiplierBadge = getMultiplierBadge()

  return (
    <div className="bg-gradient-to-br from-orange-500/10 to-orange-500/5 rounded-2xl border border-orange-500/20 p-4">
      {/* Header with date */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4 text-orange-500" />
          <span className="text-sm text-muted-foreground">{dateStr}</span>
        </div>
        {multiplierBadge && (
          <div className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${multiplierBadge.color}`}>
            <Sparkles className="w-3 h-3" />
            {multiplierBadge.text}
          </div>
        )}
      </div>

      {/* Lunar date and solar term */}
      {(lunarStr || solarTerm || holiday) && (
        <div className="flex flex-wrap items-center gap-2 mb-3 text-xs text-muted-foreground">
          {lunarStr && (
            <div className="flex items-center gap-1">
              <Moon className="w-3 h-3" />
              <span>{lunarStr}</span>
            </div>
          )}
          {solarTerm && (
            <div className="px-2 py-0.5 bg-amber-500/20 text-amber-600 rounded-full font-medium">
              {solarTerm}
            </div>
          )}
          {holiday && (
            <div className="px-2 py-0.5 bg-red-500/20 text-red-600 rounded-full">
              {holiday}
            </div>
          )}
        </div>
      )}

      {/* Stats row */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          {/* Streak */}
          <div className="flex items-center gap-2">
            <Flame className={`w-5 h-5 ${streakDays > 0 ? 'text-orange-500' : 'text-muted-foreground'}`} />
            <span className="text-2xl font-bold text-foreground">{streakDays}</span>
            <span className="text-sm text-muted-foreground">{t('天连续', 'streak')}</span>
          </div>

          {/* Total days */}
          {totalCheckinDays > 0 && (
            <div className="text-sm text-muted-foreground">
              <span className="font-medium text-foreground">{totalCheckinDays}</span>
              <span className="ml-1">{t('天打卡', 'total')}</span>
            </div>
          )}
        </div>

        {isCheckedIn ? (
          <div className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-500/20 text-emerald-600 rounded-full text-sm font-medium">
            <Check className="w-4 h-4" />
            {t('已打卡', 'Done')}
          </div>
        ) : (
          <button type="button"
            onClick={onCheckIn}
            className="px-4 py-1.5 bg-orange-500 text-white rounded-full text-sm font-medium hover:bg-orange-600 transition-colors"
          >
            {t('打卡', 'Check in')}
          </button>
        )}
      </div>
    </div>
  )
}
