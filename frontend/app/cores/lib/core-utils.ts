export const EARN_CATEGORY_LABELS: Record<string, string> = {
  mastery: '精进答题',
  arena: '挑战答题',
  checkin: '每日签到',
  study_time: '学习时长',
  daily_exercises: '每日做题',
  daily_accuracy: '每日正确率',
  bonus: '系统奖励',
}

export const SPEND_CATEGORY_LABELS: Record<string, string> = {
  ai_hint_light: 'AI 轻提示',
  ai_hint_medium: 'AI 中提示',
  ai_hint_deep: 'AI 深解析',
}

export const CATEGORY_LABELS: Record<string, string> = {
  ...EARN_CATEGORY_LABELS,
  ...SPEND_CATEGORY_LABELS,
}

const MILLISECONDS_PER_DAY = 1000 * 60 * 60 * 24

function isSameDay(a: Date, b: Date): boolean {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  )
}

export function getRelativeDayLabel(isoString: string): string {
  const date = new Date(isoString)
  const now = new Date()

  if (isSameDay(date, now)) return '今天'

  const yesterday = new Date(now)
  yesterday.setDate(yesterday.getDate() - 1)
  if (isSameDay(date, yesterday)) return '昨天'

  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

export function formatDateTime(isoString: string): string {
  const date = new Date(isoString)
  return date.toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function formatNumber(value: number): string {
  return value.toLocaleString('zh-CN')
}
