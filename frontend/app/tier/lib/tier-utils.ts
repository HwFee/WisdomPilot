import { TIER_NAMES } from '@/lib/api/tier'

const SUB_TIER_ROMAN: Record<number, string> = {
  1: 'I',
  2: 'II',
  3: 'III',
  4: 'IV',
  5: 'V',
}

export function getFullTierName(tier: string, subTier: number): string {
  if (tier === 'king') return TIER_NAMES['king']
  const tierName = TIER_NAMES[tier as keyof typeof TIER_NAMES] || tier
  const subTierName = SUB_TIER_ROMAN[subTier] || String(subTier)
  return `${tierName}${subTierName}`
}

export const TIER_SOURCE_LABELS: Record<string, string> = {
  arena_challenge: '挑战之路',
  test: '测试',
  admin: '管理员',
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
