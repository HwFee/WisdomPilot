import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { Loader2 } from "lucide-react"

import { cn } from "@/lib/utils"

/**
 * 增强的Button组件
 *
 * 特性：
 * - 更多变体：gradient、glass、success、warning
 * - 图标支持：leftIcon、rightIcon
 * - 加载状态：loading属性
 * - 更多尺寸：xs、sm、md、lg、xl、icon变体
 * - 动画效果：悬停、点击动画
 */
const buttonVariants = cva(
  // 基础样式 - 增加更多细节和动画
  `inline-flex items-center justify-center whitespace-nowrap rounded-xl
   text-sm font-medium ring-offset-background
   transition-all duration-200 ease-out
   focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring
   focus-visible:ring-offset-2
   disabled:pointer-events-none disabled:opacity-50
   active:scale-[0.98]`,
  {
    variants: {
      variant: {
        default: `
          bg-primary text-primary-foreground
          hover:bg-primary/90 hover:shadow-lg hover:shadow-primary/25
        `,
        destructive: `
          bg-destructive text-destructive-foreground
          hover:bg-destructive/90 hover:shadow-lg hover:shadow-destructive/25
        `,
        outline: `
          border-2 border-input bg-transparent
          hover:bg-accent hover:text-accent-foreground hover:border-primary/50
        `,
        secondary: `
          bg-secondary text-secondary-foreground
          hover:bg-secondary/80
        `,
        ghost: `
          hover:bg-accent hover:text-accent-foreground
        `,
        link: `
          text-primary underline-offset-4 hover:underline
        `,
        // 新增变体
        gradient: `
          bg-gradient-to-r from-primary to-primary-600 text-primary-foreground
          hover:shadow-lg hover:shadow-primary/25 hover:scale-[1.02]
        `,
        glass: `
          glass border border-white/20 text-foreground
          hover:bg-white/10 hover:border-white/30
        `,
        success: `
          bg-emerald-500 text-white
          hover:bg-emerald-600 hover:shadow-lg hover:shadow-emerald-500/25
        `,
        warning: `
          bg-amber-500 text-white
          hover:bg-amber-600 hover:shadow-lg hover:shadow-amber-500/25
        `,
      },
      size: {
        xs: 'h-7 px-2.5 text-xs rounded-lg',
        sm: 'h-9 px-3.5 text-sm rounded-lg',
        default: 'h-10 px-4 text-sm rounded-xl',
        lg: 'h-11 px-6 text-base rounded-xl',
        xl: 'h-12 px-8 text-base rounded-2xl',
        icon: 'h-10 w-10 rounded-xl',
        'icon-sm': 'h-8 w-8 rounded-lg',
        'icon-lg': 'h-12 w-12 rounded-2xl',
      },
      fullWidth: {
        true: 'w-full',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
  loading?: boolean
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({
    className,
    variant,
    size,
    fullWidth,
    asChild = false,
    loading = false,
    leftIcon,
    rightIcon,
    children,
    disabled,
    ...props
  }, ref) => {
    const Comp = asChild ? Slot : "button"

    return (
      <Comp
        className={cn(buttonVariants({ variant, size, fullWidth, className }))}
        ref={ref}
        disabled={disabled || loading}
        {...props}
      >
        {loading ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          <>
            {leftIcon && <span className="mr-2 -ml-1">{leftIcon}</span>}
            {children}
            {rightIcon && <span className="ml-2 -mr-1">{rightIcon}</span>}
          </>
        )}
      </Comp>
    )
  },
)
Button.displayName = "Button"

export { Button, buttonVariants }
