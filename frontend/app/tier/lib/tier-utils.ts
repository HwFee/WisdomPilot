export interface TierTransaction {
  id: string
  course_id: number
  tier_before: string
  sub_tier_before: number
  stars_before: number
  tier_after: string
  sub_tier_after: number
  stars_after: number
  stars_change: number
  promoted: boolean
  demoted: boolean
  used_protection: boolean
  protection_remaining: number
  source: string
  description: string | null
  created_at: string
}

export interface TransactionListResponse {
  transactions: TierTransaction[]
  total: number
}

export const TIER_NAMES: Record<string, string> = {
  bronze: '青铜',
  silver: '白银',
  gold: '黄金',
  platinum: '铂金',
  diamond: '钻石',
  master: '大师',
  grandmaster: '宗师',
  king: '王者',
}

export const TIER_COLORS: Record<string, string> = {
  bronze: 'text-amber-700 bg-amber-100',
  silver: 'text-gray-600 bg-gray-200',
  gold: 'text-yellow-600 bg-yellow-100',
  platinum: 'text-cyan-600 bg-cyan-100',
  diamond: 'text-blue-600 bg-blue-100',
  master: 'text-purple-600 bg-purple-100',
  grandmaster: 'text-red-600 bg-red-100',
  king: 'text-orange-500 bg-gradient-to-r from-yellow-100 to-orange-100',
}

const ROMAN_NUMERALS = ['', 'I', 'II', 'III', 'IV', 'V']

export function getTierDisplay(tier: string, subTier: number): string {
  return `${TIER_NAMES[tier] || tier} ${ROMAN_NUMERALS[subTier] || subTier}`
}
