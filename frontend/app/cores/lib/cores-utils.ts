// 重新导出通用日期工具，保持向后兼容
export { normalizeDateStr, formatDate } from '@/lib/formatters'

export interface CoreBalance {
  balance: number
  total_earned: number
  total_spent: number
}

export interface CoreTransaction {
  id: number
  type: 'earn' | 'spend'
  category: string
  amount: number
  balance_after: number
  reference_type?: string
  reference_id?: string
  description?: string
  created_at: string
}

export interface TransactionListResponse {
  transactions: CoreTransaction[]
  total: number
}

// 分类名称映射
export const CATEGORY_NAMES: Record<string, string> = {
  mastery: '精进之路答题',
  arena: '挑战之路答题',
  checkin: '每日签到',
  study_time: '学习时长奖励',
  daily_exercises: '每日练习完成',
  daily_accuracy: '正确率奖励',
  bonus: '系统奖励',
  ai_hint_light: '轻度提示',
  ai_hint_medium: '中度提示',
  ai_hint_deep: '深度解析',
}

// 分类颜色映射
export const CATEGORY_COLORS: Record<string, string> = {
  mastery: 'text-amber-600 bg-amber-50',
  arena: 'text-blue-600 bg-blue-50',
  checkin: 'text-green-600 bg-green-50',
  study_time: 'text-cyan-600 bg-cyan-50',
  daily_exercises: 'text-teal-600 bg-teal-50',
  daily_accuracy: 'text-orange-600 bg-orange-50',
  bonus: 'text-pink-600 bg-pink-50',
  ai_hint_light: 'text-yellow-600 bg-yellow-50',
  ai_hint_medium: 'text-purple-600 bg-purple-50',
  ai_hint_deep: 'text-indigo-600 bg-indigo-50',
}

export function getCategoryName(category: string): string {
  return CATEGORY_NAMES[category] || category
}

export function getCategoryColor(category: string): string {
  return CATEGORY_COLORS[category] || 'text-gray-600 bg-gray-50'
}


