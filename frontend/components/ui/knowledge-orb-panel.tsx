"use client"

import React from "react"
import { X, Send } from "lucide-react"
import type { ActiveKnowledgeQuestion } from "@/contexts/AIContext"
import type { ChatMessage, ContextMode } from "@/hooks/use-knowledge-orb-state"
import { PanelOrb } from "./knowledge-orb-panel-orb"
import { KnowledgeOrbMessageBubble } from "./knowledge-orb-message-bubble"
import { KnowledgeOrbStreamingBubble } from "./knowledge-orb-streaming-bubble"
import { KnowledgeOrbQuickPrompts } from "./knowledge-orb-quick-prompts"

const PANEL_W = 453
const PANEL_H = 560

interface KnowledgeOrbPanelProps {
  panelRef: React.RefObject<HTMLDivElement | null>
  pos: { x: number; y: number }
  isDraggingPanel: boolean
  activeKnowledgeQuestion: ActiveKnowledgeQuestion | null
  contextMode: ContextMode
  messages: ChatMessage[]
  isStreaming: boolean
  streamingText: string
  inputValue: string
  onInputChange: (value: string) => void
  onSend: () => void
  onKeyDown: (e: React.KeyboardEvent<HTMLTextAreaElement>) => void
  onQuickPrompt: (prompt: string) => void
  onClose: () => void
  onDragStart: (e: React.PointerEvent<HTMLDivElement>) => void
  onDragMove: (e: React.PointerEvent<HTMLDivElement>) => void
  onDragEnd: () => void
  courseId?: number
  chapterId?: number
  sectionId?: number
  exerciseId?: number
  knowledgePoints?: string[]
}

export function KnowledgeOrbPanel({
  panelRef,
  pos,
  isDraggingPanel,
  activeKnowledgeQuestion,
  contextMode,
  messages,
  isStreaming,
  streamingText,
  inputValue,
  onInputChange,
  onSend,
  onKeyDown,
  onQuickPrompt,
  onClose,
  onDragStart,
  onDragMove,
  onDragEnd,
  courseId,
  chapterId,
  sectionId,
  exerciseId,
  knowledgePoints,
}: KnowledgeOrbPanelProps) {
  const messagesRef = React.useRef<HTMLDivElement>(null)
  const textareaRef = React.useRef<HTMLTextAreaElement>(null)

  React.useEffect(() => {
    if (messagesRef.current) {
      messagesRef.current.scrollTop = messagesRef.current.scrollHeight
    }
  }, [messages, streamingText])

  const hasKnowledgePoint = !!activeKnowledgeQuestion?.knowledgePoint?.id

  const handleQuickPrompt = React.useCallback((prompt: string) => {
    onQuickPrompt(prompt)
    setTimeout(() => textareaRef.current?.focus(), 50)
  }, [onQuickPrompt])

  return (
    <div
      ref={panelRef}
      onPointerDown={onDragStart}
      onPointerMove={onDragMove}
      onPointerUp={onDragEnd}
      onPointerCancel={onDragEnd}
      className="fixed z-[9998] flex flex-col overflow-hidden animate-panel-slide-in rounded-lg select-none border border-border bg-card shadow-lg"
      style={{
        width: PANEL_W,
        height: PANEL_H,
        left: pos.x,
        top: pos.y,
        cursor: isDraggingPanel ? "grabbing" : "default",
      }}
    >
      {/* ── Header (drag handle) ── */}
      <div
        className="flex items-center justify-between px-4 py-3 border-b border-border shrink-0 cursor-grab active:cursor-grabbing select-none"
        data-drag-handle
      >
        <div className="flex items-center gap-2.5">
          <PanelOrb size={22} />
          <div>
            <p className="text-sm font-semibold text-foreground">AI 学习助手</p>
            <p className="text-xs text-muted-foreground">
              {hasKnowledgePoint
                ? contextMode === "question"
                  ? "已关联当前题目"
                  : "已关联当前知识点"
                : "随时提问"}
            </p>
          </div>
        </div>
        <button type="button"
          onClick={onClose}
          aria-label="关闭"
          className="size-7 flex items-center justify-center rounded-md transition-colors text-muted-foreground hover:bg-muted"
        >
          <X className="size-4" strokeWidth={1.5} />
        </button>
      </div>

      {/* ── Quick prompts ── */}
      <KnowledgeOrbQuickPrompts
        contextMode={contextMode}
        hasKnowledgePoint={hasKnowledgePoint}
        onPrompt={handleQuickPrompt}
      />

      {/* ── Messages ── */}
      <div
        ref={messagesRef}
        className="flex-1 overflow-y-auto px-3 py-2 flex flex-col gap-2 min-h-0"
      >
        {messages.length === 0 && !isStreaming && (
          <div className="h-full flex items-center justify-center">
            <p className="text-xs text-center leading-relaxed text-muted-foreground">
              选择上方快捷问题
              <br />或直接输入问题
            </p>
          </div>
        )}
        {messages.map((msg) => (
          <div
            key={`orb-${msg.role}-${msg.content.slice(0, 30)}`}
            className="flex"
            style={{ justifyContent: msg.role === "user" ? "flex-end" : "flex-start" }}
          >
            <KnowledgeOrbMessageBubble
              role={msg.role}
              content={msg.content}
              courseId={courseId}
              chapterId={chapterId}
              sectionId={sectionId}
              exerciseId={exerciseId}
              knowledgePoints={knowledgePoints}
            />
          </div>
        ))}
        {/* Streaming bubble */}
        {isStreaming && (
          <KnowledgeOrbStreamingBubble streamingText={streamingText} />
        )}
      </div>

      {/* ── Input ── */}
      <div className="px-3 pb-3 pt-2 shrink-0 border-t border-border">
        <div className="flex items-end gap-2">
          <textarea
            ref={textareaRef}
            value={inputValue}
            onChange={e => onInputChange(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder={contextMode === "question" ? "针对题目继续提问..." : "针对知识点继续提问..."}
            aria-label="提问输入"
            rows={4}
            className="flex-1 resize-none rounded-md border border-border bg-secondary/50 px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary disabled:opacity-60"
            disabled={isStreaming}
          />
          <button
            type="button"
            disabled={!inputValue.trim() || isStreaming}
            onClick={onSend}
            aria-label="发送"
            className="size-9 flex items-center justify-center rounded-md bg-primary text-primary-foreground transition-colors shrink-0 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-primary/90"
          >
            <Send className="size-4" strokeWidth={1.5} />
          </button>
        </div>
      </div>
    </div>
  )
}
