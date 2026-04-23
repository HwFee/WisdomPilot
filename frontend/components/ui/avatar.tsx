import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"
import { User } from "lucide-react"

/**
 * Avatar 头像系统
 *
 * 特性：
 * - 用户头像组件：支持图片和默认头像
 * - 等级边框：根据用户等级显示不同的边框样式
 * - 在线状态指示：在线、离线、忙碌状态
 * - 头像组：多个头像的堆叠显示
 * - 尺寸选项：xs、sm、md、lg、xl
 */

const avatarVariants = cva(
  'relative inline-flex items-center justify-center overflow-hidden rounded-full bg-muted',
  {
    variants: {
      size: {
        xs: 'w-6 h-6',
        sm: 'w-8 h-8',
        md: 'w-10 h-10',
        lg: 'w-12 h-12',
        xl: 'w-16 h-16',
        '2xl': 'w-20 h-20',
      },
    },
    defaultVariants: {
      size: 'md',
    },
  }
)

const avatarTextVariants = cva(
  'font-medium text-muted-foreground',
  {
    variants: {
      size: {
        xs: 'text-xs',
        sm: 'text-xs',
        md: 'text-sm',
        lg: 'text-base',
        xl: 'text-lg',
        '2xl': 'text-xl',
      },
    },
    defaultVariants: {
      size: 'md',
    },
  }
)

const avatarImageVariants = cva(
  'aspect-square h-full w-full object-cover'
)

// 等级边框样式
const tierBorderVariants = cva(
  'absolute inset-0 rounded-full',
  {
    variants: {
      tier: {
        bronze: 'ring-2 ring-amber-600',
        silver: 'ring-2 ring-gray-400',
        gold: 'ring-2 ring-yellow-500',
        platinum: 'ring-2 ring-cyan-400',
        diamond: 'ring-2 ring-blue-400',
        master: 'ring-2 ring-purple-400',
        king: 'ring-2 ring-red-400 ring-offset-2 ring-offset-background',
      },
    },
    defaultVariants: {
      tier: undefined,
    },
  }
)

// 状态指示器样式
const statusIndicatorVariants = cva(
  'absolute bottom-0 right-0 block rounded-full ring-2 ring-background',
  {
    variants: {
      status: {
        online: 'bg-emerald-500',
        offline: 'bg-gray-400',
        busy: 'bg-amber-500',
        away: 'bg-blue-500',
      },
      size: {
        xs: 'w-1.5 h-1.5',
        sm: 'w-2 h-2',
        md: 'w-2.5 h-2.5',
        lg: 'w-3 h-3',
        xl: 'w-4 h-4',
        '2xl': 'w-5 h-5',
      },
    },
    defaultVariants: {
      status: 'offline',
      size: 'md',
    },
  }
)

export interface AvatarProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof avatarVariants> {
  src?: string | null
  alt?: string
  fallback?: string
  tier?: 'bronze' | 'silver' | 'gold' | 'platinum' | 'diamond' | 'master' | 'king'
  status?: 'online' | 'offline' | 'busy' | 'away'
  showStatus?: boolean
}

const Avatar = React.forwardRef<HTMLDivElement, AvatarProps>(
  ({
    className,
    size,
    src,
    alt = 'Avatar',
    fallback,
    tier,
    status,
    showStatus = false,
    ...props
  }, ref) => {
    const [imageError, setImageError] = React.useState(false)

    // 生成首字母作为fallback
    const initials = React.useMemo(() => {
      if (fallback) return fallback
      if (alt) {
        return alt
          .split(' ')
          .map(word => word[0])
          .join('')
          .toUpperCase()
          .slice(0, 2)
      }
      return 'U'
    }, [fallback, alt])

    return (
      <div
        ref={ref}
        className={cn(
          avatarVariants({ size }),
          tier && 'ring-offset-background',
          className
        )}
        {...props}
      >
        {/* 等级边框 */}
        {tier && (
          <div className={cn(tierBorderVariants({ tier }))} />
        )}

        {/* 头像图片或fallback */}
        {src && !imageError ? (
          <img
            src={src}
            alt={alt}
            className={avatarImageVariants()}
            onError={() => setImageError(true)}
          />
        ) : (
          <span className={avatarTextVariants({ size })}>
            {initials}
          </span>
        )}

        {/* 状态指示器 */}
        {showStatus && status && (
          <span className={statusIndicatorVariants({ status, size })} />
        )}
      </div>
    )
  }
)
Avatar.displayName = "Avatar"

/**
 * AvatarGroup - 头像组（堆叠显示）
 */
interface AvatarGroupProps extends React.HTMLAttributes<HTMLDivElement> {
  max?: number
  size?: VariantProps<typeof avatarVariants>['size']
  children: React.ReactNode
}

function AvatarGroup({
  max = 4,
  size = 'md',
  className,
  children,
  ...props
}: AvatarGroupProps) {
  const childArray = React.Children.toArray(children)
  const visibleCount = Math.min(max, childArray.length)
  const remainingCount = childArray.length - visibleCount

  return (
    <div className={cn("flex -space-x-2", className)} {...props}>
      {childArray.slice(0, visibleCount).map((child, index) => (
        <div
          key={index}
          className="relative ring-2 ring-background rounded-full"
          style={{ zIndex: visibleCount - index }}
        >
          {child}
        </div>
      ))}
      {remainingCount > 0 && (
        <div
          className={cn(
            avatarVariants({ size }),
            "ring-2 ring-background bg-muted"
          )}
        >
          <span className={avatarTextVariants({ size })}>
            +{remainingCount}
          </span>
        </div>
      )}
    </div>
  )
}

/**
 * AvatarWithInfo - 带信息的头像
 */
interface AvatarWithInfoProps extends AvatarProps {
  name: string
  description?: string
  nameClassName?: string
  descriptionClassName?: string
}

function AvatarWithInfo({
  name,
  description,
  className,
  nameClassName,
  descriptionClassName,
  ...props
}: AvatarWithInfoProps) {
  return (
    <div className={cn("flex items-center gap-3", className)}>
      <Avatar {...props} />
      <div className="flex-1 min-w-0">
        <p className={cn(
          "font-medium text-foreground truncate",
          nameClassName
        )}>
          {name}
        </p>
        {description && (
          <p className={cn(
            "text-sm text-muted-foreground truncate",
            descriptionClassName
          )}>
            {description}
          </p>
        )}
      </div>
    </div>
  )
}

export { Avatar, AvatarGroup, AvatarWithInfo, avatarVariants }
