'use client'

import { Target, CheckCircle, Clock, Flame, TrendingUp, TrendingDown } from 'lucide-react'

interface TodayStatsProps {
  stats: {
    exercisesToday: number
    accuracy: number
    learningMinutes: number
    streakDays?: number
  }
  trend?: {
    exercises: number
    accuracy: number
    time?: number
  }
  lang?: 'zh' | 'en'
  onExercisesClick?: () => void
  onAccuracyClick?: () => void
  onTimeClick?: () => void
}

interface StatCardProps {
  icon: React.ReactNode
  value: string | number
  label: string
  guide?: string
  trend?: number
  color: string
  onClick?: () => void
}

function StatCard({ icon, value, label, guide, trend, color, onClick }: StatCardProps) {
  return (
    <div
      className={`bg-card rounded-2xl border border-border p-5 hover:shadow-lg hover:border-primary/20 transition-all min-h-[100px] flex flex-col ${onClick ? 'cursor-pointer' : ''}`}
      onClick={onClick}
    >
      <div className="flex items-center justify-between mb-2">
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${color}`}>
          {icon}
        </div>
        {trend !== undefined && trend !== 0 && (
          <div className={`flex items-center gap-1 text-xs px-2 py-1 rounded-full ${trend > 0 ? 'text-emerald-500 bg-emerald-500/10' : 'text-red-500 bg-red-500/10'}`}>
            {trend > 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
            {trend > 0 ? '+' : ''}{trend}%
          </div>
        )}
      </div>
      <div className="flex-1 flex flex-col justify-end">
        <p className="text-2xl font-bold text-foreground">{value}</p>
        <p className="text-sm text-muted-foreground">{label}</p>
        {guide && <p className="text-xs text-primary mt-1 hover:underline">{guide}</p>}
      </div>
    </div>
  )
}

export function TodayStats({ stats, trend, lang = 'zh', onExercisesClick, onAccuracyClick, onTimeClick }: TodayStatsProps) {
  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
      <StatCard
        icon={<Target className="w-5 h-5 text-blue-500" />}
        value={stats.exercisesToday}
        label={t('今日做题', 'Exercises')}
        guide={stats.exercisesToday === 0 ? t('目标：10题 →', 'Goal: 10') : undefined}
        trend={trend?.exercises}
        color="bg-blue-500/10"
        onClick={onExercisesClick}
      />
      <StatCard
        icon={<CheckCircle className="w-5 h-5 text-emerald-500" />}
        value={`${stats.accuracy}%`}
        label={t('正确率', 'Accuracy')}
        guide={stats.accuracy === 0 ? t('保持专注 →', 'Stay focused!') : undefined}
        trend={trend?.accuracy}
        color="bg-emerald-500/10"
        onClick={onAccuracyClick}
      />
      <StatCard
        icon={<Clock className="w-5 h-5 text-purple-500" />}
        value={t(`${stats.learningMinutes}分钟`, `${stats.learningMinutes}min`)}
        label={t('学习时长', 'Time')}
        guide={stats.learningMinutes === 0 ? t('目标：30分钟 →', 'Goal: 30min') : undefined}
        trend={trend?.time}
        color="bg-purple-500/10"
        onClick={onTimeClick}
      />
      <StatCard
        icon={<Flame className="w-5 h-5 text-orange-500" />}
        value={stats.streakDays ?? 0}
        label={t('连续打卡', 'Streak')}
        color="bg-orange-500/10"
      />
    </div>
  )
}
