'use client'

import { Flame, Check, Calendar } from 'lucide-react'

interface CheckInCardProps {
  streakDays: number
  isCheckedIn?: boolean
  onCheckIn: () => void
  lang?: 'zh' | 'en'
}

export function CheckInCard({ streakDays, isCheckedIn = false, onCheckIn, lang = 'zh' }: CheckInCardProps) {
  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  const now = new Date()
  const dateStr = now.toLocaleDateString('zh-CN', {
    month: 'long',
    day: 'numeric',
    weekday: 'long',
  })

  return (
    <div className="bg-gradient-to-br from-orange-500/10 to-orange-500/5 rounded-2xl border border-orange-500/20 p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4 text-orange-500" />
          <span className="text-sm text-muted-foreground">{dateStr}</span>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Flame className={`w-5 h-5 ${streakDays > 0 ? 'text-orange-500 animate-flame' : 'text-muted-foreground'}`} />
          <span className="text-2xl font-bold text-foreground">{streakDays}</span>
          <span className="text-sm text-muted-foreground">{t('天', 'days')}</span>
        </div>

        {isCheckedIn ? (
          <div className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-500/20 text-emerald-600 rounded-full text-sm font-medium">
            <Check className="w-4 h-4" />
            {t('已打卡', 'Checked in')}
          </div>
        ) : (
          <button
            onClick={onCheckIn}
            className="px-3 py-1.5 bg-orange-500 text-white rounded-full text-sm font-medium hover:bg-orange-600 transition-colors"
          >
            {t('打卡', 'Check in')}
          </button>
        )}
      </div>
    </div>
  )
}
