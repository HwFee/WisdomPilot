/**
 * Toast 通知系统
 *
 * 位置支持：顶部、底部
 * 动画效果：滑入滑出、淡入淡出
 * 自动关闭：支持自定义关闭时间
 */

import * as React from "react"
import { create } from "zustand"
import { LazyMotion, domAnimation, m, AnimatePresence } from "framer-motion"
import { cn } from "@/lib/utils"
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  Info,
  X,
  type LucideIcon,
} from "lucide-react"

// ── 类型定义 ──

type ToastType = 'success' | 'error' | 'warning' | 'info'
type ToastPosition = 'top-left' | 'top-center' | 'top-right' | 'bottom-left' | 'bottom-center' | 'bottom-right'

interface Toast {
  id: string
  type: ToastType
  title: string
  description?: string
  duration?: number
  action?: {
    label: string
    onClick: () => void
  }
}

interface ToastStore {
  toasts: Toast[]
  position: ToastPosition
  addToast: (toast: Omit<Toast, 'id'>) => string
  removeToast: (id: string) => void
  setPosition: (position: ToastPosition) => void
  clearAll: () => void
}

// ── Toast 状态管理 ──

const useToastStore = create<ToastStore>((set, get) => ({
  toasts: [],
  position: 'bottom-right',

  addToast: (toast) => {
    const id = Math.random().toString(36).substr(2, 9)
    set((state) => ({
      toasts: [...state.toasts, { ...toast, id }],
    }))

    // 自动关闭
    if (toast.duration !== 0) {
      setTimeout(() => {
        get().removeToast(id)
      }, toast.duration || 4000)
    }

    return id
  },

  removeToast: (id) => {
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    }))
  },

  setPosition: (position) => {
    set({ position })
  },

  clearAll: () => {
    set({ toasts: [] })
  },
}))

// ── Toast 配置 ──

const toastConfig: Record<ToastType, {
  icon: LucideIcon
  className: string
  iconClass: string
}> = {
  success: {
    icon: CheckCircle,
    className: 'bg-emerald-500 text-white border-emerald-600',
    iconClass: 'text-white',
  },
  error: {
    icon: XCircle,
    className: 'bg-red-500 text-white border-red-600',
    iconClass: 'text-white',
  },
  warning: {
    icon: AlertTriangle,
    className: 'bg-amber-500 text-white border-amber-600',
    iconClass: 'text-white',
  },
  info: {
    icon: Info,
    className: 'bg-blue-500 text-white border-blue-600',
    iconClass: 'text-white',
  },
}

const positionClasses: Record<ToastPosition, string> = {
  'top-left': 'top-4 left-4',
  'top-center': 'top-4 left-1/2 -translate-x-1/2',
  'top-right': 'top-4 right-4',
  'bottom-left': 'bottom-4 left-4',
  'bottom-center': 'bottom-4 left-1/2 -translate-x-1/2',
  'bottom-right': 'bottom-4 right-4',
}

// ── ToastItem 组件 ──

interface ToastItemProps {
  toast: Toast
  onClose: () => void
}

function ToastItem({ toast, onClose }: ToastItemProps) {
  const config = toastConfig[toast.type]
  const Icon = config.icon

  return (
    <m.div
      layout
      initial={{ opacity: 0, y: 50, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 20, scale: 0.95 }}
      transition={{ duration: 0.2 }}
      className={cn(
        "flex items-start gap-3 p-4 rounded-xl shadow-lg border min-w-[300px] max-w-[400px]",
        config.className
      )}
    >
      <Icon className={cn("size-5 flex-shrink-0 mt-0.5", config.iconClass)} />

      <div className="flex-1 min-w-0">
        <p className="font-medium">{toast.title}</p>
        {toast.description && (
          <p className="text-sm opacity-90 mt-0.5">{toast.description}</p>
        )}
        {toast.action && (
          <button type="button"
            onClick={toast.action.onClick}
            className="text-sm font-medium underline mt-2 hover:opacity-80 transition-opacity"
          >
            {toast.action.label}
          </button>
        )}
      </div>

      <button type="button"
        onClick={onClose}
        className="flex-shrink-0 hover:opacity-80 transition-opacity"
      >
        <X className="size-4" />
      </button>
    </m.div>
  )
}

// ── ToastProvider 组件 ──

interface ToastProviderProps {
  position?: ToastPosition
}

export function ToastProvider({ position = 'bottom-right' }: ToastProviderProps) {
  const { toasts, setPosition } = useToastStore()

  const prevPositionRef = React.useRef(position)
  if (position !== prevPositionRef.current) {
    prevPositionRef.current = position
    setPosition(position)
  }

  const currentPosition = useToastStore((state) => state.position)

  return (
    <div className={cn("fixed z-[100] flex flex-col gap-2", positionClasses[currentPosition])}>
      <AnimatePresence mode="popLayout">
        {toasts.map((toast) => (
          <ToastItem
            key={toast.id}
            toast={toast}
            onClose={() => useToastStore.getState().removeToast(toast.id)}
          />
        ))}
      </AnimatePresence>
    </div>
  )
}

// ── 便捷方法 ──

export const toast = {
  success: (title: string, description?: string, options?: Partial<Toast>) => {
    return useToastStore.getState().addToast({ type: 'success', title, description, ...options })
  },

  error: (title: string, description?: string, options?: Partial<Toast>) => {
    return useToastStore.getState().addToast({ type: 'error', title, description, ...options })
  },

  warning: (title: string, description?: string, options?: Partial<Toast>) => {
    return useToastStore.getState().addToast({ type: 'warning', title, description, ...options })
  },

  info: (title: string, description?: string, options?: Partial<Toast>) => {
    return useToastStore.getState().addToast({ type: 'info', title, description, ...options })
  },

  dismiss: (id: string) => {
    useToastStore.getState().removeToast(id)
  },

  clearAll: () => {
    useToastStore.getState().clearAll()
  },

  setPosition: (position: ToastPosition) => {
    useToastStore.getState().setPosition(position)
  },
}

// ── useToast Hook ──

export function useToast() {
  return toast
}

export type { ToastType, ToastPosition, Toast }
