export interface XpBalance {
  balance: number
  level: string
}

export interface XpTransaction {
  id: string
  type: 'earn' | 'spend'
  category: string
  amount: number
  balance_after: number
  level_before: string
  level_after: string
  level_up: boolean
  reference_type?: string
  reference_id?: string
  description?: string
  created_at: string
}

export interface TransactionListResponse {
  transactions: XpTransaction[]
  total: number
}

const CATEGORY_NAMES: Record<string, string> = {
  base_test: '基础测试答题',
  mastery_quiz: '精进测验完成',
  achievement: '成就奖励',
  bonus: '系统奖励',
}

const CATEGORY_COLORS: Record<string, string> = {
  base_test: 'text-blue-600 bg-blue-50',
  mastery_quiz: 'text-purple-600 bg-purple-50',
  achievement: 'text-amber-600 bg-amber-50',
  bonus: 'text-green-600 bg-green-50',
}

const LEVEL_COLORS: Record<string, string> = {
  入门: 'text-gray-600 bg-gray-100',
  学习: 'text-blue-600 bg-blue-100',
  练习: 'text-green-600 bg-green-100',
  熟练: 'text-purple-600 bg-purple-100',
  精通: 'text-amber-600 bg-gradient-to-r from-amber-100 to-orange-100',
}

export function getCategoryName(category: string): string {
  return CATEGORY_NAMES[category] || category
}

export function getCategoryColor(category: string): string {
  return CATEGORY_COLORS[category] || 'text-gray-600 bg-gray-50'
}

export function getLevelColor(level: string): string {
  return LEVEL_COLORS[level] || 'text-gray-600 bg-gray-100'
}
