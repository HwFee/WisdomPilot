/**
 * 反馈组件集
 *
 * 包含成功、错误、警告等反馈组件，以及加载占位和空状态组件
 */

import * as React from "react"
import { LazyMotion, domAnimation, m, AnimatePresence } from "framer-motion"
import { cn } from "@/lib/utils"
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  Info,
  Loader2,
  type LucideIcon,
} from "lucide-react"
import { Button } from "./button-enhanced"

// ── 基础反馈组件 ──

interface FeedbackProps {
  show: boolean
  message: string
  description?: string
  icon?: LucideIcon
  type?: 'success' | 'error' | 'warning' | 'info'
  position?: 'top' | 'bottom'
  duration?: number
  onClose?: () => void
}

const feedbackConfig = {
  success: {
    icon: CheckCircle,
    className: 'bg-emerald-500 text-white',
    iconClass: 'text-white',
  },
  error: {
    icon: XCircle,
    className: 'bg-red-500 text-white',
    iconClass: 'text-white',
  },
  warning: {
    icon: AlertTriangle,
    className: 'bg-amber-500 text-white',
    iconClass: 'text-white',
  },
  info: {
    icon: Info,
    className: 'bg-blue-500 text-white',
    iconClass: 'text-white',
  },
}

/**
 * 成功反馈
 */
export function SuccessFeedback({
  show,
  message,
  description,
  duration = 3000,
  onClose,
}: Omit<FeedbackProps, 'icon' | 'type'>) {
  return (
    <FeedbackToast
      show={show}
      message={message}
      description={description}
      type="success"
      duration={duration}
      onClose={onClose}
    />
  )
}

/**
 * 错误反馈
 */
export function ErrorFeedback({
  show,
  message,
  description,
  duration = 4000,
  onClose,
}: Omit<FeedbackProps, 'icon' | 'type'>) {
  return (
    <FeedbackToast
      show={show}
      message={message}
      description={description}
      type="error"
      duration={duration}
      onClose={onClose}
    />
  )
}

/**
 * 警告反馈
 */
export function WarningFeedback({
  show,
  message,
  description,
  duration = 3500,
  onClose,
}: Omit<FeedbackProps, 'icon' | 'type'>) {
  return (
    <FeedbackToast
      show={show}
      message={message}
      description={description}
      type="warning"
      duration={duration}
      onClose={onClose}
    />
  )
}

/**
 * 信息反馈
 */
export function InfoFeedback({
  show,
  message,
  description,
  duration = 3000,
  onClose,
}: Omit<FeedbackProps, 'icon' | 'type'>) {
  return (
    <FeedbackToast
      show={show}
      message={message}
      description={description}
      type="info"
      duration={duration}
      onClose={onClose}
    />
  )
}

/**
 * 通用反馈Toast
 */
function FeedbackToast({
  show,
  message,
  description,
  type = 'info',
  position = 'bottom',
  duration,
  onClose,
}: FeedbackProps) {
  const config = feedbackConfig[type]
  const Icon = config.icon

  React.useEffect(() => {
    if (show && duration && onClose) {
      const timer = setTimeout(onClose, duration)
      return () => clearTimeout(timer)
    }
  }, [show, duration, onClose])

  return (
    <AnimatePresence>
      {show && (
        <LazyMotion features={domAnimation}>
          <m.div
            initial={{ opacity: 0, y: position === 'bottom' ? 20 : -20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: position === 'bottom' ? 20 : -20, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className={cn(
              'fixed z-50 flex items-center gap-3 px-4 py-3 rounded-xl shadow-lg',
              config.className,
              position === 'bottom' ? 'bottom-6 right-6' : 'top-6 right-6'
            )}
          >
            <m.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.1, type: 'spring' }}
            >
              <Icon className={cn('size-5', config.iconClass)} />
            </m.div>
          <div>
            <p className="font-medium">{message}</p>
            {description && (
              <p className="text-sm opacity-90">{description}</p>
            )}
          </div>
          </m.div>
        </LazyMotion>
      )}
    </AnimatePresence>
  )
}

// ── 加载占位组件 ──

interface LoadingPlaceholderProps {
  type?: 'card' | 'text' | 'list' | 'code' | 'stats'
  className?: string
}

/**
 * 加载占位
 */
export function LoadingPlaceholder({
  type = 'card',
  className,
}: LoadingPlaceholderProps) {
  if (type === 'card') {
    return (
      <div className={cn("bg-card rounded-2xl border border-border p-5", className)}>
        <div className="flex items-center gap-3 mb-4">
          <div className="size-10 bg-muted rounded-xl animate-pulse" />
          <div className="flex-1">
            <div className="h-4 bg-muted rounded w-1/2 mb-2 animate-pulse" />
            <div className="h-3 bg-muted rounded w-1/4 animate-pulse" />
          </div>
        </div>
        <div className="flex flex-col gap-y-2">
          <div className="h-3 bg-muted rounded w-full animate-pulse" />
          <div className="h-3 bg-muted rounded w-4/5 animate-pulse" />
          <div className="h-3 bg-muted rounded w-3/5 animate-pulse" />
        </div>
      </div>
    )
  }

  if (type === 'text') {
    return (
      <div className={cn("flex flex-col gap-y-2", className)}>
        <div className="h-4 bg-muted rounded w-full animate-pulse" />
        <div className="h-4 bg-muted rounded w-4/5 animate-pulse" />
        <div className="h-4 bg-muted rounded w-3/5 animate-pulse" />
      </div>
    )
  }

  if (type === 'list') {
    return (
      <div className={cn("flex flex-col gap-y-3", className)}>
        {[1, 2, 3].map(n => (
          <div key={`list-skeleton-${n}`} className="flex items-center gap-3">
            <div className="size-10 bg-muted rounded-full animate-pulse" />
            <div className="flex-1">
              <div className="h-4 bg-muted rounded w-1/3 mb-2 animate-pulse" />
              <div className="h-3 bg-muted rounded w-1/2 animate-pulse" />
            </div>
          </div>
        ))}
      </div>
    )
  }

  if (type === 'code') {
    return (
      <div className={cn("bg-card rounded-xl border border-border overflow-hidden", className)}>
        <div className="flex items-center gap-2 p-3 border-b border-border bg-muted/30">
          <div className="size-3 bg-muted rounded-full animate-pulse" />
          <div className="size-3 bg-muted rounded-full animate-pulse" />
          <div className="size-3 bg-muted rounded-full animate-pulse" />
        </div>
        <div className="p-4 flex flex-col gap-y-2">
          {[1, 2, 3, 4, 5].map(n => (
            <div key={`code-skeleton-${n}`} className="flex gap-4">
              <div className="w-6 h-4 bg-muted animate-pulse" />
              <div className={cn(
                "h-4 bg-muted animate-pulse",
                n % 3 === 0 ? "w-3/4" : n % 3 === 1 ? "w-1/2" : "w-2/3"
              )} />
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (type === 'stats') {
    return (
      <div className={cn("bg-card rounded-2xl border border-border p-5", className)}>
        <div className="flex items-center justify-between mb-3">
          <div className="size-10 bg-muted rounded-xl animate-pulse" />
          <div className="w-16 h-5 bg-muted rounded-full animate-pulse" />
        </div>
        <div className="h-8 w-24 bg-muted rounded mb-2 animate-pulse" />
        <div className="h-3 w-32 bg-muted rounded animate-pulse" />
      </div>
    )
  }

  return null
}

/**
 * 加载覆盖层
 */
export function LoadingOverlay({
  show,
  message = '加载中...',
}: {
  show: boolean
  message?: string
}) {
  return (
    <LazyMotion features={domAnimation}>
      <AnimatePresence>
        {show && (
          <m.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm"
          >
            <div className="flex flex-col items-center gap-4">
              <Loader2 className="size-8 animate-spin text-primary" />
              <p className="text-muted-foreground">{message}</p>
            </div>
          </m.div>
        )}
      </AnimatePresence>
    </LazyMotion>
  )
}

// ── 空状态组件 ──

interface EmptyStateProps {
  icon?: LucideIcon
  title: string
  description?: string
  action?: {
    label: string
    onClick: () => void
  }
  className?: string
}

/**
 * 空状态
 */
export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <LazyMotion features={domAnimation}>
      <m.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className={cn(
          "flex flex-col items-center justify-center py-16 px-4",
          className
        )}
      >
        {Icon && (
          <m.div
            initial={{ scale: 0.5, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.1, type: 'spring' }}
            className="size-20 bg-muted rounded-2xl flex items-center justify-center mb-6"
          >
            <Icon className="size-10 text-muted-foreground" />
          </m.div>
        )}

        <h3 className="text-lg font-semibold text-foreground mb-2">{title}</h3>

        {description && (
          <p className="text-muted-foreground text-center max-w-sm mb-6">
            {description}
          </p>
        )}

        {action && (
          <Button onClick={action.onClick} variant="default">
            {action.label}
          </Button>
        )}
      </m.div>
    </LazyMotion>
  )
}

// ── 内联加载组件 ──

/**
 * 内联加载
 */
export function InlineLoading({
  message = '加载中...',
  className,
}: {
  message?: string
  className?: string
}) {
  return (
    <div className={cn("flex items-center justify-center gap-2 py-8", className)}>
      <Loader2 className="size-5 animate-spin text-primary" />
      <span className="text-muted-foreground">{message}</span>
    </div>
  )
}

/**
 * 按钮加载状态
 */
export function ButtonLoading({ className }: { className?: string }) {
  return (
    <Loader2 className={cn("size-4 animate-spin", className)} />
  )
}
