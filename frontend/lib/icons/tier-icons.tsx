/**
 * 段位图标系统 - 王者荣耀风格
 *
 * 用户等级对应的段位徽章配置
 * 使用更清晰的图标来表示段位级别
 */

import React from 'react'
import { Medal, Gem, Crown, Swords, Shield, Zap } from 'lucide-react'

export interface TierIconConfig {
  id: string
  name: string
  icon: React.ReactNode
  color: string
  bgColor: string
  gradient: string
  borderColor: string
  minXP: number
  maxXP: number
}

// 段位图标使用更清晰的Lucide图标
// 青铜-白银-黄金：使用不同颜色的Medal徽章
// 铂金-钻石：使用Gem宝石
// 大师：使用Crown皇冠
// 王者：使用Swords代表竞技/权力

export const TIER_ICONS: Record<string, TierIconConfig> = {
  bronze: {
    id: 'bronze',
    name: '青铜',
    icon: <Medal className="size-5 text-amber-600" />,
    color: 'text-amber-600',
    bgColor: 'bg-amber-600/10',
    gradient: 'from-amber-600 to-amber-700',
    borderColor: 'ring-amber-600',
    minXP: 0,
    maxXP: 999,
  },
  silver: {
    id: 'silver',
    name: '白银',
    icon: <Medal className="size-5 text-gray-400" />,
    color: 'text-gray-400',
    bgColor: 'bg-gray-400/10',
    gradient: 'from-gray-400 to-gray-500',
    borderColor: 'ring-gray-400',
    minXP: 1000,
    maxXP: 2999,
  },
  gold: {
    id: 'gold',
    name: '黄金',
    icon: <Medal className="size-5 text-yellow-500 fill-yellow-500/20" />,
    color: 'text-yellow-500',
    bgColor: 'bg-yellow-500/10',
    gradient: 'from-yellow-500 to-yellow-600',
    borderColor: 'ring-yellow-500',
    minXP: 3000,
    maxXP: 5999,
  },
  platinum: {
    id: 'platinum',
    name: '铂金',
    icon: <Gem className="size-5 text-cyan-400" />,
    color: 'text-cyan-400',
    bgColor: 'bg-cyan-400/10',
    gradient: 'from-cyan-400 to-cyan-500',
    borderColor: 'ring-cyan-400',
    minXP: 6000,
    maxXP: 9999,
  },
  diamond: {
    id: 'diamond',
    name: '钻石',
    icon: <Gem className="size-5 text-blue-400 fill-blue-400/30" />,
    color: 'text-blue-400',
    bgColor: 'bg-blue-400/10',
    gradient: 'from-blue-400 to-blue-500',
    borderColor: 'ring-blue-400',
    minXP: 10000,
    maxXP: 14999,
  },
  master: {
    id: 'master',
    name: '大师',
    icon: <Crown className="size-5 text-purple-500" />,
    color: 'text-purple-400',
    bgColor: 'bg-purple-400/10',
    gradient: 'from-purple-400 to-purple-500',
    borderColor: 'ring-purple-400',
    minXP: 15000,
    maxXP: 24999,
  },
  king: {
    id: 'king',
    name: '王者',
    icon: <Swords className="size-5 text-red-500" />,
    color: 'text-red-400',
    bgColor: 'bg-red-400/10',
    gradient: 'from-red-400 to-red-500',
    borderColor: 'ring-red-400',
    minXP: 25000,
    maxXP: Infinity,
  },
} as const

// 段位顺序
export const TIER_ORDER = [
  'bronze',
  'silver',
  'gold',
  'platinum',
  'diamond',
  'master',
  'king',
] as const

/**
 * 根据XP获取段位
 */
export function getTierByXP(xp: number): TierIconConfig {
  for (const tierId of TIER_ORDER) {
    const tier = TIER_ICONS[tierId]
    if (xp >= tier.minXP && xp <= tier.maxXP) {
      return tier
    }
  }
  return TIER_ICONS.bronze
}

/**
 * 获取段位配置
 */
export function getTierConfig(tierId: string): TierIconConfig | undefined {
  return TIER_ICONS[tierId]
}

/**
 * 获取下一个段位
 */
export function getNextTier(currentTierId: string): TierIconConfig | undefined {
  const currentIndex = TIER_ORDER.indexOf(currentTierId as any)
  if (currentIndex === -1 || currentIndex === TIER_ORDER.length - 1) {
    return undefined
  }
  return TIER_ICONS[TIER_ORDER[currentIndex + 1]]
}

/**
 * 计算升级进度
 */
export function calculateTierProgress(xp: number): {
  current: TierIconConfig
  next?: TierIconConfig
  progress: number
  xpToNext: number
} {
  const current = getTierByXP(xp)
  const next = getNextTier(current.id)

  if (!next) {
    return {
      current,
      progress: 100,
      xpToNext: 0,
    }
  }

  const progress = ((xp - current.minXP) / (next.minXP - current.minXP)) * 100
  const xpToNext = next.minXP - xp

  return {
    current,
    next,
    progress: Math.min(100, Math.max(0, progress)),
    xpToNext,
  }
}

// 导出图标组件供直接使用
export {
  Medal,
  Gem,
  Crown,
  Swords,
  Shield,
  Zap,
}

