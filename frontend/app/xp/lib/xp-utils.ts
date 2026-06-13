export const XP_CATEGORY_LABELS: Record<string, string> = {
  base_test: '基础测试',
  mastery_quiz: '精进测验',
  achievement: '成就奖励',
  bonus: '系统奖励',
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
