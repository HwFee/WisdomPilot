'use client'

import { useState, useCallback, useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'
import { Loader2, Sparkles, GripVertical, AlertCircle, Gem } from 'lucide-react'
import { cn } from '@/lib/utils'
import { HintMessage } from './HintMessage'
import { HINT_CONFIG, type HintLevel } from './hint-message.constants'
import { CloseButton, ModalFooterAction, CostLabel, ErrorToast } from './HintActions'

// ========================================
// Public types
// ========================================

export interface ExerciseHintData {
  exercise_id?: string
  exercise_title: string
  exercise_description: string
  difficulty: number
  knowledge_points: string[]
  code_template?: string
  sample_input?: string
  sample_output?: string
}

// ========================================
// HintBubble - single-level hint button + draggable streaming modal
// ========================================

interface HintBubbleProps {
  level: HintLevel
  exerciseData: ExerciseHintData
  token: string
  onBalanceChange: () => void
  currentBalance?: number
  disabled?: boolean
}

export function HintBubble({
  level,
  exerciseData,
  token,
  onBalanceChange,
  currentBalance,
  disabled,
}: HintBubbleProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [hintContent, setHintContent] = useState('')
  const [streamState, setStreamState] = useState({ streaming: false, cached: false })
  const { streaming: isStreaming, cached: isCached } = streamState
  const [error, setError] = useState<string | null>(null)

  const config = HINT_CONFIG[level]
  const Icon = config.icon
  const canAfford = currentBalance === undefined || currentBalance >= config.cost

  const fetchStreamHint = async () => {
    setIsOpen(true)
    setHintContent('')
    setStreamState({ streaming: true, cached: false })
    setError(null)

    try {
      const { streamExerciseHint } = await import('@/lib/api/ai')

      const result = await streamExerciseHint(
        {
          exercise_id: exerciseData.exercise_id,
          exercise_title: exerciseData.exercise_title,
          exercise_description: exerciseData.exercise_description,
          difficulty: exerciseData.difficulty,
          knowledge_points: exerciseData.knowledge_points,
          hint_level: level,
          code_template: exerciseData.code_template,
          sample_input: exerciseData.sample_input,
          sample_output: exerciseData.sample_output,
        },
        token,
        (chunk, cached) => {
          setHintContent((prev) => prev + chunk)
          if (cached) {
            setStreamState((prev) => ({ ...prev, cached: true }))
          }
        },
        (errorMsg) => {
          if (errorMsg.includes('余额不足') || errorMsg.includes('INSUFFICIENT')) {
            onBalanceChange()
          }
          setError(errorMsg)
          setStreamState((prev) => ({ ...prev, streaming: false }))
        },
        () => {
          setStreamState((prev) => ({ ...prev, streaming: false }))
        }
      )

      if (!result.cached && result.cost > 0) {
        onBalanceChange()
      }
    } catch {
      setError('AI 提示请求失败，请重试')
      setStreamState((prev) => ({ ...prev, streaming: false }))
    }
  }

  const handleClose = () => {
    setIsOpen(false)
    setHintContent('')
    setStreamState({ streaming: false, cached: false })
    setError(null)
  }

  return (
    <>
      <div className="relative">
        <button
          type="button"
          onClick={fetchStreamHint}
          disabled={disabled || !canAfford}
          className={`
            flex flex-col items-center gap-1 p-2 rounded-lg border transition-all
            ${config.bgColor} ${config.borderColor} ${config.hoverColor}
            disabled:opacity-50 disabled:cursor-not-allowed
          `}
          title={`${config.label}: ${config.description} (-${config.cost}智核)`}
        >
          <Icon className={`size-5 ${config.color}`} />
          <span className={`text-xs font-medium ${config.color}`}>{config.label}</span>
          <span className="text-[10px] text-muted-foreground flex items-center gap-0.5">
            <Gem className="size-3" />
            {config.cost}
          </span>
        </button>

        {!canAfford && (
          <div className="absolute -top-1 -right-1 size-3 bg-red-500 rounded-full flex items-center justify-center">
            <AlertCircle className="size-2 text-white" />
          </div>
        )}
      </div>

      <StreamHintModal
        isOpen={isOpen}
        onClose={handleClose}
        level={level}
        hintContent={hintContent}
        isStreaming={isStreaming}
        cost={config.cost}
        isCached={isCached}
      />

      {error && <ErrorToast message={error} onDismiss={() => setError(null)} />}
    </>
  )
}

// ========================================
// StreamHintModal - draggable, portal-rendered modal showing the hint body
// ========================================

interface StreamHintModalProps {
  isOpen: boolean
  onClose: () => void
  level: HintLevel
  hintContent: string
  isStreaming: boolean
  cost: number
  isCached?: boolean
}

const MODAL_POSITION_KEY = 'aiHintModalPosition:v1'

function StreamHintModal({
  isOpen,
  onClose,
  level,
  hintContent,
  isStreaming,
  isCached = false,
}: StreamHintModalProps) {
  const config = HINT_CONFIG[level]
  const Icon = config.icon

  const [position, setPosition] = useState<{ x: number; y: number } | null>(() => {
    if (typeof window === 'undefined') return null
    const saved = localStorage.getItem(MODAL_POSITION_KEY)
    if (!saved) return null
    try {
      return JSON.parse(saved)
    } catch {
      return null
    }
  })
  const [isDragging, setIsDragging] = useState(false)
  const dragStartRef = useRef<{ x: number; y: number; posX: number; posY: number } | null>(null)

  const savePosition = useCallback((pos: { x: number; y: number }) => {
    localStorage.setItem(MODAL_POSITION_KEY, JSON.stringify(pos))
  }, [])

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true)
    const currentPos = position || { x: 0, y: 0 }
    dragStartRef.current = {
      x: e.clientX,
      y: e.clientY,
      posX: currentPos.x,
      posY: currentPos.y,
    }
    e.preventDefault()
  }

  // Latest-ref wrappers
  const positionRef = useRef(position)
  useEffect(() => {
    positionRef.current = position
  }, [position])
  const savePositionRef = useRef(savePosition)
  useEffect(() => {
    savePositionRef.current = savePosition
  }, [savePosition])

  useEffect(() => {
    if (!isDragging) return

    const handleMouseMove = (e: MouseEvent) => {
      if (!dragStartRef.current) return
      const deltaX = e.clientX - dragStartRef.current.x
      const deltaY = e.clientY - dragStartRef.current.y
      setPosition({
        x: dragStartRef.current.posX + deltaX,
        y: dragStartRef.current.posY + deltaY,
      })
    }

    const handleMouseUp = () => {
      setIsDragging(false)
      if (positionRef.current) {
        savePositionRef.current(positionRef.current)
      }
      dragStartRef.current = null
    }

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [isDragging])

  if (!isOpen) return null

  const modalStyle: React.CSSProperties = {
    position: 'fixed',
    left: position ? `calc(50% + ${position.x}px)` : '50%',
    top: position ? `calc(50% + ${position.y}px)` : '50%',
    transform: 'translate(-50%, -50%)',
    zIndex: 9999,
  }

  const modalContent = (
    <div
      style={modalStyle}
      className={cn(
        'w-full max-w-lg max-h-[80vh] overflow-hidden flex flex-col rounded-2xl',
        'bg-card/95 backdrop-blur-sm border border-white/10 shadow-2xl',
        isDragging ? 'select-none' : ''
      )}
    >
      {/* Top accent */}
      <div className="absolute inset-x-0 top-0 h-px bg-primary/30 z-10" />

      {/* Draggable header */}
      <div className="relative flex items-center justify-between px-5 py-4 border-b border-border/50 bg-muted/30 rounded-t-2xl cursor-grab active:cursor-grabbing">
        <button
          type="button"
          className="absolute inset-0 z-0"
          aria-label="拖动"
          onMouseDown={handleMouseDown}
        />
        <div className="relative z-10 flex items-center gap-3">
          <div className={`p-2 rounded-lg ${config.bgColor}`}>
            <Icon className={`size-5 ${config.color}`} />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-foreground flex items-center gap-2">
              {config.label}
              {isCached && (
                <span className="text-xs font-normal text-green-600 bg-green-500/10 px-2 py-0.5 rounded-full border border-green-500/20">
                  已购买
                </span>
              )}
            </h3>
            <p className="text-xs text-muted-foreground">{config.description}</p>
          </div>
          {isStreaming && !isCached && (
            <Loader2 className={`size-4 ${config.color} animate-spin ml-2`} />
          )}
        </div>
        <div className="relative z-10 flex items-center gap-2">
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <GripVertical className="size-4" />
            <span>拖动</span>
          </div>
          <CloseButton onClick={onClose} ariaLabel="关闭" />
        </div>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto px-5 py-4">
        <HintMessage
          content={hintContent}
          emptyState={
            <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
              <div className="relative">
                <div className="size-12 rounded-full bg-purple-500/10 flex items-center justify-center">
                  <Sparkles className="size-6 text-purple-500" />
                </div>
                <div className="absolute -bottom-1 -right-1 size-5 rounded-full bg-card flex items-center justify-center shadow border border-border/50">
                  <Loader2 className="size-3 text-purple-500 animate-spin" />
                </div>
              </div>
              <p className="mt-4 text-sm">AI 正在思考...</p>
            </div>
          }
        />
      </div>

      {/* Footer */}
      <div className="px-5 py-4 border-t border-border/50 bg-muted/30 rounded-b-2xl">
        <div className="flex items-center justify-between">
          <CostLabel level={level} isCached={isCached} />
          <ModalFooterAction
            isStreaming={isStreaming}
            isCached={isCached}
            onClose={onClose}
          />
        </div>
      </div>
    </div>
  )

  return createPortal(modalContent, document.body)
}
