import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { Medal, Gem, Crown, Trophy } from "lucide-react"

import { cn } from "@/lib/utils"

/**
 * Badge 徽章系统
 *
 * 特性：
 * - 多种变体：default、outline、solid、gradient
 * - 语义类型：success、warning、error、info
 * - 尺寸：sm、md、lg
 * - 特殊徽章：段位徽章、难度徽章
 */

const badgeVariants = cva(
  'inline-flex items-center gap-1.5 font-medium transition-all duration-200',
  {
    variants: {
      variant: {
        default: 'bg-primary/10 text-primary border border-primary/20',
        outline: 'border border-current bg-transparent',
        solid: 'bg-primary text-primary-foreground',
        gradient: 'bg-gradient-to-r from-primary to-primary-600 text-primary-foreground',
        secondary: 'bg-secondary text-secondary-foreground',
        destructive: 'bg-destructive/10 text-destructive border border-destructive/20',
        success: 'bg-emerald-500/10 text-emerald-600 border border-emerald-500/20',
        warning: 'bg-amber-500/10 text-amber-600 border border-amber-500/20',
        error: 'bg-red-500/10 text-red-600 border border-red-500/20',
        info: 'bg-blue-500/10 text-blue-600 border border-blue-500/20',
      },
      size: {
        sm: 'text-xs px-2 py-0.5 rounded',
        md: 'text-xs px-2.5 py-1 rounded-md',
        lg: 'text-sm px-3 py-1.5 rounded-lg',
      },
      rounded: {
        default: '',
        full: 'rounded-full',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'md',
      rounded: 'default',
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {
  icon?: React.ReactNode
}

function Badge({
  className,
  variant,
  size,
  rounded,
  icon,
  children,
  ...props
}: BadgeProps) {
  return (
    <div
      className={cn(badgeVariants({ variant, size, rounded, className }))}
      {...props}
    >
      {icon && <span className="flex-shrink-0">{icon}</span>}
      {children}
    </div>
  )
}

/**
 * 难度徽章 - 洛谷风格 8级体系
 */
interface DifficultyBadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  level: 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8
  showLabel?: boolean
}

const DIFFICULTY_CONFIG = {
  1: { label: '入门', className: 'bg-gradient-to-r from-red-500 to-red-600 text-white' },
  2: { label: '普及-', className: 'bg-gradient-to-r from-orange-500 to-orange-600 text-white' },
  3: { label: '普及/提高-', className: 'bg-gradient-to-r from-yellow-500 to-yellow-600 text-white' },
  4: { label: '普及+/提高', className: 'bg-gradient-to-r from-green-500 to-green-600 text-white' },
  5: { label: '提高+/省选-', className: 'bg-gradient-to-r from-blue-500 to-blue-600 text-white' },
  6: { label: '省选/NOI-', className: 'bg-gradient-to-r from-purple-500 to-purple-600 text-white' },
  7: { label: 'NOI', className: 'bg-gradient-to-r from-slate-600 to-slate-700 text-white' },
  8: { label: 'NOI+/CTSC', className: 'bg-gradient-to-r from-slate-800 to-slate-900 text-white' },
} as const

function DifficultyBadge({
  level,
  showLabel = true,
  className,
  ...props
}: DifficultyBadgeProps) {
  const config = DIFFICULTY_CONFIG[level]

  return (
    <div
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-semibold rounded-md shadow-sm',
        config.className,
        className
      )}
      {...props}
    >
      {showLabel && config.label}
    </div>
  )
}

/**
 * 段位徽章 - 王者荣耀风格
 */
interface TierBadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  tier: 'bronze' | 'silver' | 'gold' | 'platinum' | 'diamond' | 'master' | 'king'
  size?: 'sm' | 'md' | 'lg'
}

const TIER_CONFIG = {
  bronze: {
    label: '青铜',
    className: 'bg-gradient-to-r from-amber-600 to-amber-700 text-white',
    icon: Medal,
  },
  silver: {
    label: '白银',
    className: 'bg-gradient-to-r from-gray-400 to-gray-500 text-white',
    icon: Medal,
  },
  gold: {
    label: '黄金',
    className: 'bg-gradient-to-r from-yellow-500 to-yellow-600 text-white',
    icon: Medal,
  },
  platinum: {
    label: '铂金',
    className: 'bg-gradient-to-r from-cyan-400 to-cyan-500 text-white',
    icon: Gem,
  },
  diamond: {
    label: '钻石',
    className: 'bg-gradient-to-r from-blue-400 to-blue-500 text-white',
    icon: Gem,
  },
  master: {
    label: '大师',
    className: 'bg-gradient-to-r from-purple-400 to-purple-500 text-white',
    icon: Crown,
  },
  king: {
    label: '王者',
    className: 'bg-gradient-to-r from-red-400 to-red-500 text-white',
    icon: Trophy,
  },
} as const

const TIER_SIZES = {
  sm: 'px-2 py-0.5 text-xs rounded',
  md: 'px-3 py-1 text-sm rounded-md',
  lg: 'px-4 py-1.5 text-base rounded-lg',
}

function TierBadge({
  tier,
  size = 'md',
  className,
  ...props
}: TierBadgeProps) {
  const config = TIER_CONFIG[tier]
  const Icon = config.icon

  return (
    <div
      className={cn(
        'inline-flex items-center gap-1.5 font-semibold shadow-md',
        config.className,
        TIER_SIZES[size],
        className
      )}
      {...props}
    >
      <Icon className="size-4" />
      <span>{config.label}</span>
    </div>
  )
}

/**
 * 课程徽章
 */
interface CourseBadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  course: 'c' | 'cpp' | 'python'
}

const COURSE_CONFIG = {
  c: { label: 'C语言', className: 'bg-blue-500/10 text-blue-600 border-blue-500/20' },
  cpp: { label: 'C++', className: 'bg-indigo-500/10 text-indigo-600 border-indigo-500/20' },
  python: { label: 'Python', className: 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20' },
} as const

function CourseBadge({ course, className, ...props }: CourseBadgeProps) {
  const config = COURSE_CONFIG[course]

  return (
    <Badge
      variant="outline"
      className={cn(config.className, className)}
      {...props}
    >
      {config.label}
    </Badge>
  )
}

/**
 * 状态徽章 - 带脉冲动画
 */
interface StatusBadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  status: 'online' | 'offline' | 'busy' | 'away'
  showDot?: boolean
}

const STATUS_CONFIG = {
  online: { label: '在线', dotClass: 'bg-emerald-500 animate-pulse' },
  offline: { label: '离线', dotClass: 'bg-gray-400' },
  busy: { label: '忙碌', dotClass: 'bg-amber-500' },
  away: { label: '离开', dotClass: 'bg-blue-500' },
} as const

function StatusBadge({
  status,
  showDot = true,
  className,
  ...props
}: StatusBadgeProps) {
  const config = STATUS_CONFIG[status]

  return (
    <div
      className={cn(
        'inline-flex items-center gap-2 text-xs',
        className
      )}
      {...props}
    >
      {showDot && (
        <span className={cn('size-2 rounded-full', config.dotClass)} />
      )}
      <span className="text-muted-foreground">{config.label}</span>
    </div>
  )
}

export {
  Badge,
  badgeVariants,
  DifficultyBadge,
  TierBadge,
  CourseBadge,
  StatusBadge,
}
