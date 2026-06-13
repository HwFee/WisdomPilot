/**
 * Tier API - 段位系统相关API调用
 */

import { getStoredToken } from './auth'
import { API_BASE_URL } from './client'
import type { TierConfig, TierInfo, TierRank, UpdateStarsResult } from '@/types/api'

/**
 * 获取所有段位配置
 */
export async function getTierConfigs(): Promise<{ tiers: TierConfig[] }> {
  const token = getStoredToken()

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(`${API_BASE_URL}/api/tier/config`, {
    headers,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail || '获取段位配置失败')
  }

  return response.json()
}

/**
 * 获取用户在指定课程的段位信息
 */
export async function getTierInfo(courseId: number): Promise<TierInfo> {
  const token = getStoredToken()
  if (!token) {
    throw new Error('未登录')
  }

  const response = await fetch(`${API_BASE_URL}/api/tier/profile/${courseId}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail || '获取段位信息失败')
  }

  return response.json()
}

/**
 * 获取用户全局段位信息（挑战之路用，不关联课程）
 */
export async function getGlobalTierInfo(): Promise<TierInfo> {
  const token = getStoredToken()
  if (!token) {
    throw new Error('未登录')
  }

  const response = await fetch(`${API_BASE_URL}/api/tier/profile`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail || '获取段位信息失败')
  }

  return response.json()
}

/**
 * 更新用户星星数
 */
export async function updateStars(
  courseId: number,
  starsChange: number,
  accuracy?: number,
  difficulty?: number
): Promise<UpdateStarsResult> {
  const token = getStoredToken()
  if (!token) {
    throw new Error('未登录')
  }

  const response = await fetch(`${API_BASE_URL}/api/tier/profile/${courseId}/stars`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      stars_change: starsChange,
      accuracy,
      difficulty,
    }),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail || '更新星星失败')
  }

  return response.json()
}

export interface TierTransaction {
  id: string
  course_id?: number
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
  reference_id?: string
  description?: string
  created_at: string
}

export interface TierTransactionList {
  transactions: TierTransaction[]
  total: number
}

/**
 * 获取段位变化历史
 */
export async function getTierTransactions(
  courseId?: number,
  limit: number = 20,
  offset: number = 0,
): Promise<TierTransactionList> {
  const token = getStoredToken()
  if (!token) {
    throw new Error('未登录')
  }

  const params = new URLSearchParams({
    limit: limit.toString(),
    offset: offset.toString(),
  })
  if (courseId !== undefined) {
    params.append('course_id', courseId.toString())
  }

  const response = await fetch(`${API_BASE_URL}/api/tier/transactions?${params}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail || '获取段位流水失败')
  }

  return response.json()
}

/**
 * 段位名称映射
 */
export const TIER_NAMES: Record<TierRank, string> = {
  bronze: '青铜',
  silver: '白银',
  gold: '黄金',
  platinum: '铂金',
  diamond: '钻石',
  master: '星耀',
  king: '王者',
}

/**
 * 段位颜色映射
 */
export const TIER_COLORS: Record<TierRank, string> = {
  bronze: '#CD7F32',
  silver: '#C0C0C0',
  gold: '#FFD700',
  platinum: '#E5E4E2',
  diamond: '#B9F2FF',
  master: '#9370DB',
  king: '#FF4500',
}

/**
 * 段位图标映射（使用emoji作为简单图标）
 */
const TIER_ICONS: Record<TierRank, string> = {
  bronze: '🥉',
  silver: '🥈',
  gold: '🥇',
  platinum: '💎',
  diamond: '💠',
  master: '⭐',
  king: '👑',
}

/**
 * 获取完整段位名称
 */
function getFullTierName(tier: TierRank, subTier: number): string {
  if (tier === 'king') {
    return '王者'
  }
  const tierName = TIER_NAMES[tier] || tier
  const subTierName = getSubTierName(subTier)
  return `${tierName}${subTierName}`
}

/**
 * 获取小段位罗马数字名称
 */
function getSubTierName(subTier: number): string {
  const roman: Record<number, string> = {
    1: 'I',
    2: 'II',
    3: 'III',
    4: 'IV',
    5: 'V',
  }
  return roman[subTier] || String(subTier)
}

/**
 * 获取段位顺序（用于比较）
 */
function getTierOrder(tier: TierRank): number {
  const order: Record<TierRank, number> = {
    bronze: 0,
    silver: 1,
    gold: 2,
    platinum: 3,
    diamond: 4,
    master: 5,
    king: 6,
  }
  return order[tier] ?? 0
}
