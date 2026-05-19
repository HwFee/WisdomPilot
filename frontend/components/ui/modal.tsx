/**
 * Modal 模态框系统
 *
 * 尺寸支持：sm、md、lg、xl、full
 * 动画效果：缩放、淡入淡出
 * 子组件：ModalHeader、ModalBody、ModalFooter
 */

import * as React from "react"
import { LazyMotion, domAnimation, m, AnimatePresence } from "framer-motion"
import { cn } from "@/lib/utils"
import { X } from "lucide-react"

// ── Modal 组件 ──

interface ModalProps {
  open: boolean
  onClose: () => void
  children: React.ReactNode
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full'
  closeOnOverlayClick?: boolean
  closeOnEscape?: boolean
  showCloseButton?: boolean
  className?: string
  overlayClassName?: string
}

const sizeClasses = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-lg',
  xl: 'max-w-xl',
  full: 'max-w-[90vw] max-h-[90vh]',
}

function Modal({
  open,
  onClose,
  children,
  size = 'md',
  closeOnOverlayClick = true,
  closeOnEscape = true,
  showCloseButton = true,
  className,
  overlayClassName,
}: ModalProps) {
  // ESC 键关闭
  const onCloseEvent = React.useEffectEvent(() => {
    onClose()
  })
  const openRef = React.useRef(open)
  openRef.current = open

  React.useEffect(() => {
    if (!closeOnEscape) return

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && openRef.current) {
        onCloseEvent()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [closeOnEscape])

  // 禁止背景滚动
  React.useEffect(() => {
    if (open) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => {
      document.body.style.overflow = ''
    }
  }, [open])

  return (
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center p-4">
          {/* 遮罩层 - 玻璃态效果 */}
          <LazyMotion features={domAnimation}>
          <m.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className={cn(
              "absolute inset-0 bg-black/40 backdrop-blur-xl",
              overlayClassName
            )}
            onClick={closeOnOverlayClick ? onClose : undefined}
          />

          {/* 模态框内容 - 玻璃态 + 渐变边框 */}
          <m.div
            initial={{ opacity: 0, scale: 0.96, y: 12 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: 12 }}
            transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
            className={cn(
              "relative w-full rounded-2xl border border-white/10 shadow-2xl overflow-hidden",
              "bg-card/95 backdrop-blur-sm",
              sizeClasses[size],
              className
            )}
            onClick={(e) => e.stopPropagation()}
          >
            {/* 顶部渐变光效 */}
            <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-primary/30 to-transparent" />

            {showCloseButton && (
              <button type="button"
                onClick={onClose}
                className="absolute top-4 right-4 z-10 p-1.5 rounded-lg bg-muted/50 hover:bg-muted border border-border/50 hover:border-border transition-all group"
              >
                <X className="size-4 text-muted-foreground group-hover:text-foreground transition-colors" />
              </button>
            )}
            {children}
          </m.div>
          </LazyMotion>
        </div>
      )}
    </AnimatePresence>
  )
}

// ── ModalHeader 组件 ──

interface ModalHeaderProps {
  children: React.ReactNode
  className?: string
}

function ModalHeader({ children, className }: ModalHeaderProps) {
  return (
    <div className={cn(
      "px-6 pt-6 pb-4 border-b border-border/50 bg-gradient-to-r from-primary/5 via-primary/[0.02] to-transparent",
      className
    )}>
      <h2 className="text-lg font-semibold text-foreground">{children}</h2>
    </div>
  )
}

// ── ModalBody 组件 ──

interface ModalBodyProps {
  children: React.ReactNode
  className?: string
}

function ModalBody({ children, className }: ModalBodyProps) {
  return (
    <div className={cn("px-6 py-4 max-h-[60vh] overflow-y-auto", className)}>
      {children}
    </div>
  )
}

// ── ModalFooter 组件 ──

interface ModalFooterProps {
  children: React.ReactNode
  className?: string
  align?: 'left' | 'center' | 'right'
}

function ModalFooter({ children, className, align = 'right' }: ModalFooterProps) {
  const alignClasses = {
    left: 'justify-start',
    center: 'justify-center',
    right: 'justify-end',
  }

  return (
    <div className={cn(
      "flex items-center gap-3 px-6 py-4 border-t border-border/50 bg-muted/30",
      alignClasses[align],
      className
    )}>
      {children}
    </div>
  )
}

// ── ConfirmModal 组件 ──

interface ConfirmModalProps {
  open: boolean
  onClose: () => void
  onConfirm: () => void
  title: string
  description?: string
  confirmText?: string
  cancelText?: string
  variant?: 'default' | 'danger'
  loading?: boolean
}

function ConfirmModal({
  open,
  onClose,
  onConfirm,
  title,
  description,
  confirmText = '确认',
  cancelText = '取消',
  variant = 'default',
  loading = false,
}: ConfirmModalProps) {
  return (
    <Modal open={open} onClose={onClose} size="sm" showCloseButton={false}>
      <ModalHeader>{title}</ModalHeader>
      {description && (
        <ModalBody>
          <p className="text-muted-foreground">{description}</p>
        </ModalBody>
      )}
      <ModalFooter>
        <button type="button"
          onClick={onClose}
          disabled={loading}
          className="px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors rounded-lg hover:bg-muted"
        >
          {cancelText}
        </button>
        <button type="button"
          onClick={onConfirm}
          disabled={loading}
          className={cn(
            "px-4 py-2 text-sm font-medium rounded-lg transition-all shadow-sm hover:shadow-md hover:-translate-y-0.5",
            variant === 'danger'
              ? "bg-gradient-to-r from-red-500 to-red-600 text-white hover:from-red-600 hover:to-red-700"
              : "bg-gradient-to-r from-primary to-primary-600 text-primary-foreground hover:from-primary-600 hover:to-primary-700"
          )}
        >
          {loading ? '处理中...' : confirmText}
        </button>
      </ModalFooter>
    </Modal>
  )
}

// ── useModal Hook ──

function useModal() {
  const [open, setOpen] = React.useState(false)

  const openModal = React.useCallback(() => setOpen(true), [])
  const closeModal = React.useCallback(() => setOpen(false), [])
  const toggleModal = React.useCallback(() => setOpen((prev) => !prev), [])

  return {
    open,
    openModal,
    closeModal,
    toggleModal,
    modalProps: { open, onClose: closeModal },
  }
}

export {
  Modal,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ConfirmModal,
  useModal,
}
