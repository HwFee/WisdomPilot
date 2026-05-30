"use client"

import React, { useState, useCallback, useRef, useEffect } from "react"
import { cx } from "class-variance-authority"
import { LazyMotion, domAnimation, m, useDragControls, AnimatePresence } from "framer-motion"

import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

const EXPANDED_WIDTH = 420
const EXPANDED_HEIGHT = 380
const ORB_SIZE = 44

// ============================================================
// ColorOrb — inline animated gradient (no globals.css needed)
// ============================================================

interface OrbProps {
  dimension?: string
  className?: string
  tones?: {
    accent1?: string
    accent2?: string
    accent3?: string
    glow?: string
  }
}

const ColorOrb: React.FC<OrbProps> = ({
  dimension = "192px",
  className,
  tones,
}) => {
  const fallback = {
    accent1: "#c084fc",
    accent2: "#60a5fa",
    accent3: "#a78bfa",
    glow: "rgba(139, 92, 246, 0.5)",
  }
  const p = { ...fallback, ...tones }

  return (
    <div
      className={cn("rounded-full overflow-hidden", className)}
      style={{
        width: dimension,
        height: dimension,
        background: `
          radial-gradient(circle at 35% 45%, ${p.accent1} 0%, transparent 55%),
          radial-gradient(circle at 70% 65%, ${p.accent3} 0%, transparent 55%),
          conic-gradient(from 180deg at 50% 50%, ${p.accent1}, ${p.accent2}, ${p.accent3}, ${p.accent1})
        `,
        boxShadow: `0 0 14px 4px ${p.glow}, 0 2px 8px rgba(0,0,0,0.15)`,
        flexShrink: 0,
      }}
      aria-hidden="true"
    />
  )
}

// ============================================================
// Types
// ============================================================

export interface QuestionContext {
  type: "choice" | "programming"
  id: string
  question: string
  options?: string[]
  code?: string
  language?: string
}

interface AIChatPanelProps {
  className?: string
}

interface ChatMessage {
  role: "user:v1" | "ai"
  content: string
}

// ============================================================
// Parse question context from DOM dataset
// ============================================================

function parseQuestionContext(el: Element): QuestionContext | null {
  const type = el.getAttribute("data-question-type")
  const id = el.getAttribute("data-question-id") || ""
  const question = el.getAttribute("data-question-text") || ""
  if (!type || !question) return null

  const optionsStr = el.getAttribute("data-question-options")
  const options = optionsStr ? JSON.parse(optionsStr) : undefined
  const code = el.getAttribute("data-question-code") || undefined
  const language = el.getAttribute("data-question-language") || undefined

  return { type: type as "choice" | "programming", id, question, options, code, language }
}

// ============================================================
// KeyHint
// ============================================================

function KeyHint({ children, className }: { children: string; className?: string }) {
  return (
    <kbd className={cx("text-foreground flex h-6 w-fit items-center justify-center rounded-sm border px-[6px] font-sans", className)}>
      {children}
    </kbd>
  )
}

// ============================================================
// MorphPanel — 可拖动 AI 对话面板
// ============================================================

export function MorphPanel({ className }: AIChatPanelProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const messagesRef = useRef<HTMLDivElement>(null)

  const dragControls = useDragControls()

  // Panel state: initial is collapsed (orb only)
  const [viewState, setViewState] = useState({ isCollapsed: true, isExpanded: false })
  const [dragState, setDragState] = useState<{ isDragging: boolean; target: { id: string | null; question: QuestionContext | null } }>({
    isDragging: false,
    target: { id: null, question: null },
  })

  // Track orb screen position during drag for hit detection
  const orbScreenPosRef = useRef({ x: 0, y: 0 })
  const highlightIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Question context
  const activeQuestion = dragState.target.question
  const highlightedId = dragState.target.id

  // Chat state
  const [chatState, setChatState] = useState<{ messages: ChatMessage[]; inputValue: string }>({
    messages: [],
    inputValue: '',
  })
  const [streamState, setStreamState] = useState({ isStreaming: false, streamingText: '' })
  const { isCollapsed, isExpanded } = viewState
  const { isDragging } = dragState
  const { messages, inputValue } = chatState
  const { isStreaming, streamingText } = streamState

  // Open panel
  const openPanel = useCallback(() => {
    setViewState(prev => ({ ...prev, isExpanded: true }))
    setTimeout(() => textareaRef.current?.focus(), 100)
  }, [])

  // Close panel
  const closePanel = useCallback(() => {
    setViewState(prev => ({ ...prev, isExpanded: false }))
    textareaRef.current?.blur()
  }, [])

  // Collapse to orb
  const collapseToOrb = useCallback(() => {
    setViewState({ isCollapsed: true, isExpanded: false })
  }, [])

  // Expand from orb
  const expandFromOrb = useCallback(() => {
    setViewState(prev => ({ ...prev, isCollapsed: false }))
    if (activeQuestion) {
      openPanel()
    }
  }, [activeQuestion, openPanel])

  // Build system prompt with question context
  const buildPrompt = useCallback((question: QuestionContext, userMessage: string) => {
    const optsStr = question.options
      ? "\n选项：\n" + question.options.map((o, i) => `${String.fromCharCode(65 + i)}. ${o}`).join("\n")
      : ""

    const codeStr = question.code ? `\n代码：\n\`\`\`${question.language || ""}\n${question.code}\n\`\`\`` : ""

    return `你是学生的编程学习助手。学生正在学习数据结构与算法。

当前题目信息：
- 类型：${question.type === "choice" ? "选择题" : "编程题"}
- 题目：${question.question}${optsStr}${codeStr}

学生问题：${userMessage}

请根据以上题目信息，用中文给出有帮助的回答。`
  }, [])

  // Send message
  const sendMessage = useCallback(async () => {
    const text = chatState.inputValue.trim()
    if (!text || streamState.isStreaming) return

    const userMessage = text
    setChatState(prev => ({ ...prev, inputValue: '' }))
    setChatState(prev => ({ ...prev, messages: [...prev.messages, { role: "user:v1", content: userMessage }] }))
    setStreamState({ isStreaming: true, streamingText: '' })

    const prompt = activeQuestion
      ? buildPrompt(activeQuestion, userMessage)
      : `你是一位耐心的编程老师。学生的问题是：\n\n${userMessage}\n\n请给出简洁、有帮助的回答。`

    try {
      const token = localStorage.getItem("token:v1")
      if (!token) return

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/ai/chat/stream`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            message: prompt,
            context: activeQuestion || null,
          }),
        }
      )

      if (!response.ok) throw new Error("请求失败")
      if (!response.body) throw new Error("无响应体")

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let fullText = ""

      setChatState(prev => ({ ...prev, messages: [...prev.messages, { role: "ai", content: "" }] }))

      while (true) {
        // react-doctor-disable-next-line async-await-in-loop, react-doctor/async-await-in-loop
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value, { stream: true })
        const lines = chunk.split("\n")

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6)
            if (data === "[DONE]") continue
            try {
              const parsed = JSON.parse(data)
              if (parsed.content) {
                fullText += parsed.content
                setStreamState(prev => ({ ...prev, streamingText: fullText }))
                setChatState(prev => {
                  const updated = [...prev.messages]
                  updated[updated.length - 1] = { role: "ai", content: fullText }
                  return { ...prev, messages: updated }
                })
              }
            } catch {}
          }
        }
      }
    } catch (err) {
      setChatState(prev => ({ ...prev, messages: [...prev.messages, { role: "ai", content: "抱歉，AI 服务暂时不可用。" }] }))
    } finally {
      setStreamState({ isStreaming: false, streamingText: '' })
    }
  }, [chatState.inputValue, streamState.isStreaming, activeQuestion, buildPrompt])

  // Clear chat — collapse back to orb
  const clearChat = useCallback(() => {
    setChatState(prev => ({ ...prev, messages: [] }))
    setDragState(prev => ({ ...prev, target: { id: null, question: null } }))
    collapseToOrb()
  }, [collapseToOrb])

  // Hit detection: poll orb screen position during drag
  // react-doctor-disable-next-line no-cascading-set-state, react-doctor/no-cascading-set-state
  useEffect(() => {
    if (!isDragging) {
      if (highlightIntervalRef.current) {
        clearInterval(highlightIntervalRef.current)
        highlightIntervalRef.current = null
      }
      setDragState(prev => ({ ...prev, target: { id: null, question: null } }))
      return
    }

    highlightIntervalRef.current = setInterval(() => {
      const { x, y } = orbScreenPosRef.current
      const el = document.elementFromPoint(x, y)
      const q = el?.closest("[data-question-context]")
      const ctx = q ? parseQuestionContext(q) : null
      setDragState(prev => {
        if (ctx) return { ...prev, target: { id: ctx.id, question: ctx } }
        return prev.target.id !== null ? { ...prev, target: { ...prev.target, id: null } } : prev
      })
    }, 80)

    return () => {
      if (highlightIntervalRef.current) {
        clearInterval(highlightIntervalRef.current)
      }
    }
  }, [dragState.isDragging])

  // Apply highlight outline to the question element when highlightedId changes
  useEffect(() => {
    if (!highlightedId) return
    const el = document.querySelector(`[data-question-id="${CSS.escape(highlightedId)}"]`)
    if (!el) return
    el.setAttribute("data-temp-highlight", "true")
    const prevOutline = el.getAttribute("data-prev-outline")
    const prevOffset = el.getAttribute("data-prev-offset")
    if (!prevOutline) {
      el.setAttribute("data-prev-outline", (el as HTMLElement).style.outline || "")
      el.setAttribute("data-prev-offset", (el as HTMLElement).style.outlineOffset || "")
      Object.assign((el as HTMLElement).style, {
        outline: "2px solid rgb(37 99 235 / 0.5)",
        outlineOffset: "2px",
        borderRadius: "8px",
      })
    }
    return () => {
      const el2 = document.querySelector(`[data-question-id="${CSS.escape(highlightedId)}"]`)
      if (el2) {
        const prev = el2.getAttribute("data-prev-outline")
        const prevOff = el2.getAttribute("data-prev-offset")
        Object.assign((el2 as HTMLElement).style, {
          outline: prev || "",
          outlineOffset: prevOff || "",
        })
        el2.removeAttribute("data-temp-highlight")
      }
    }
  }, [highlightedId])

  // Pointer down on the orb — start drag via controls
  const handlePointerDown: React.PointerEventHandler = useCallback((e) => {
    if (e.button !== 0) return
    e.preventDefault()
    e.stopPropagation()

    // Get the orb element's center in screen coords
    const orbEl = e.currentTarget as HTMLElement
    const rect = orbEl.getBoundingClientRect()
    const centerX = rect.left + rect.width / 2
    const centerY = rect.top + rect.height / 2
    orbScreenPosRef.current = { x: centerX, y: centerY }

    // Collapse and close panel, start drag
    setDragState(prev => ({ ...prev, isDragging: true }))
    collapseToOrb()
    closePanel()

    // Start the drag control — this initiates framer-motion drag
    dragControls.start(e, { snapToCursor: true })
  }, [dragControls, collapseToOrb, closePanel])

  // Called on any drag frame — update orb screen position for hit detection
  const handleDrag = useCallback((_: MouseEvent | TouchEvent | PointerEvent, info: { point: { x: number; y: number } }) => {
    orbScreenPosRef.current = { x: info.point.x, y: info.point.y }
  }, [])

  const handleDragEnd = useCallback(() => {
    setDragState(prev => ({ ...prev, isDragging: false }))
    if (activeQuestion) {
      expandFromOrb()
    }
  }, [activeQuestion, expandFromOrb])

  // Click on collapsed orb (not dragging) — expand it
  const handleOrbClick = useCallback(() => {
    if (!isDragging) {
      setViewState(prev => ({ ...prev, isCollapsed: false }))
      openPanel()
    }
  }, [dragState.isDragging, openPanel])

  // Keyboard shortcuts
  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Escape") {
      if (isExpanded) closePanel()
    }
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      e.preventDefault()
      sendMessage()
    }
  }, [viewState.isExpanded, closePanel, sendMessage])

  // Auto-scroll messages
  useEffect(() => {
    if (messagesRef.current) {
      messagesRef.current.scrollTop = messagesRef.current.scrollHeight
    }
  }, [chatState.messages, streamState.streamingText])

  const isPanelVisible = viewState.isExpanded && !viewState.isCollapsed

  return (
    <div
      className={cn("fixed z-[9999]", className)}
      style={{
        right: 24,
        bottom: 24,
        pointerEvents: "auto",
      }}
    >
      <LazyMotion features={domAnimation}>
      <m.div
        ref={containerRef}
        dragControls={dragControls}
        drag={true}
        dragSnapToOrigin={false}
        dragElastic={0}
        dragConstraints={{ left: -3000, right: 3000, top: -3000, bottom: 3000 }}
        onDrag={handleDrag}
        onDragEnd={handleDragEnd}
        style={{
          cursor: isDragging ? "grabbing" : isCollapsed ? "grab" : "default",
          width: isCollapsed ? ORB_SIZE : EXPANDED_WIDTH,
          height: isCollapsed ? ORB_SIZE : EXPANDED_HEIGHT,
          borderRadius: isCollapsed ? "50%" : 16,
          // DEBUG: temporary outline to verify visibility
          outline: isCollapsed ? "2px solid rgba(59,130,246,0.6)" : undefined,
          background: isCollapsed ? "rgba(59,130,246,0.08)" : undefined,
        }}
        transition={{
          type: "spring",
          stiffness: 550,
          damping: 45,
          mass: 0.7,
        }}
        className={cx(
          "bg-background border border-border overflow-hidden",
          "flex flex-col",
          "shadow-xl shadow-black/10",
          "relative"
        )}
      >
        {/* Collapsed: just the ColorOrb orb — click to expand, drag to find questions */}
        {isCollapsed && (
          <div
            className="w-full h-full flex items-center justify-center rounded-full overflow-hidden"
            style={{
              boxShadow: "0 0 0 2px rgba(37, 99, 235, 0.3), 0 4px 20px rgba(37, 99, 235, 0.25), 0 8px 30px rgba(0, 0, 0, 0.12)",
            }}
            onPointerDown={handlePointerDown}
            onClick={handleOrbClick}
            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); handleOrbClick() } }}
            role="button"
            tabIndex={0}
            aria-label="AI 输入"
            data-drag-handle
          >
            <ColorOrb dimension={`${ORB_SIZE - 8}px`} tones={{
              accent1: "#c084fc",
              accent2: "#60a5fa",
              accent3: "#a78bfa",
              glow: "rgba(37, 99, 235, 0.4)",
            }} />
          </div>
        )}

        {/* Expanded: full chat panel */}
        <AnimatePresence>
          {isPanelVisible && (
            <m.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.15 }}
              className="absolute inset-0 flex flex-col bg-background"
              style={{ width: EXPANDED_WIDTH, height: EXPANDED_HEIGHT }}
            >
              {/* Header */}
              <div className="flex items-center justify-between px-4 pt-3 pb-2 border-b border-border shrink-0">
                <div className="flex items-center gap-2">
                  <ColorOrb dimension="22px" />
                  <span className="text-sm font-semibold text-foreground">AI 学习助手</span>
                </div>
                <div className="flex items-center gap-1">
                  {/* Drag handle — allows dragging the expanded panel */}
                  <div
                    className="p-1 cursor-grab active:cursor-grabbing text-muted-foreground hover:text-foreground mr-1"
                    onPointerDown={handlePointerDown}
                    data-drag-handle
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" className="rounded">
                      <circle cx="9" cy="5" r="1.5" />
                      <circle cx="15" cy="5" r="1.5" />
                      <circle cx="9" cy="12" r="1.5" />
                      <circle cx="15" cy="12" r="1.5" />
                      <circle cx="9" cy="19" r="1.5" />
                      <circle cx="15" cy="19" r="1.5" />
                    </svg>
                  </div>
                  <button type="button"
                    onClick={clearChat}
                    className="text-xs text-muted-foreground hover:text-foreground px-2 py-1 rounded transition-colors"
                  >
                    清除
                  </button>
                  <button type="button"
                    onClick={closePanel}
                    className="text-muted-foreground hover:text-foreground p-1 rounded transition-colors"
                  >
                    ✕
                  </button>
                </div>
              </div>

              {/* Active question context */}
              {activeQuestion && (
                <div className="mx-3 my-2 px-3 py-2 bg-primary/5 rounded-lg border border-primary/10 shrink-0">
                  <p className="text-xs text-primary font-medium mb-0.5">
                    {activeQuestion.type === "choice" ? "选择题" : "编程题"}
                  </p>
                  <p className="text-xs text-foreground line-clamp-2">{activeQuestion.question}</p>
                </div>
              )}

              {/* Messages — scrollable */}
              <div
                ref={messagesRef}
                className="flex-1 overflow-y-auto px-3 gap-y-2 min-h-0"
              >
                {messages.length === 0 && !activeQuestion && (
                  <div className="h-full flex items-center justify-center">
                    <p className="text-sm text-muted-foreground text-center">
                      拖动到题目上获取上下文
                      <br />
                      或直接输入问题
                    </p>
                  </div>
                )}
                {messages.map((msg) => (
                  <div
                    key={`${msg.role}-${msg.content.slice(0, 30)}`}
                    className={cx(
                      "rounded-2xl px-4 py-2.5 max-w-[88%] text-sm",
                      msg.role === "user:v1"
                        ? "bg-primary text-primary-foreground ml-auto rounded-br-sm"
                        : "bg-muted text-foreground mr-auto rounded-bl-sm"
                    )}
                  >
                    <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                  </div>
                ))}
                {isStreaming && streamingText && (
                  <div className="bg-muted rounded-2xl rounded-bl-sm px-4 py-2.5 mr-auto max-w-[88%]">
                    <p className="whitespace-pre-wrap leading-relaxed text-sm text-foreground">{streamingText}</p>
                    <span className="inline-block w-1.5 h-4 bg-primary animate-pulse ml-1 align-middle" />
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Input area */}
              <div className="px-3 pb-3 pt-2 shrink-0 border-t border-border bg-background">
                <div
                  className="flex items-end gap-2"
                >
                  <textarea
                    ref={textareaRef}
                    value={inputValue}
                    onChange={e => setChatState(prev => ({ ...prev, inputValue: e.target.value }))}
                    onKeyDown={handleKeyDown}
                    placeholder="问我任何事..."
                    rows={2}
                    className="flex-1 resize-none rounded-xl border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                    disabled={isStreaming}
                  />
                  <Button
                    type="button"
                    size="sm"
                    disabled={!inputValue.trim() || isStreaming}
                    onClick={sendMessage}
                    className="shrink-0 size-9 p-0 flex items-center justify-center"
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <line x1="22" y1="2" x2="11" y2="13" />
                      <polygon points="22 2 15 22 11 13 2 9 22 2" />
                    </svg>
                  </Button>
                </div>
                <p className="text-[10px] text-muted-foreground mt-1 text-center">
                  <KeyHint>⌘</KeyHint>
                  <KeyHint className="ml-0.5">Enter</KeyHint>
                  <span className="ml-1">发送</span>
                  <span className="mx-2 text-border">·</span>
                  <span>Esc</span>
                  <span className="ml-1">关闭</span>
                </p>
              </div>
            </m.div>
          )}
        </AnimatePresence>
      </m.div>
      </LazyMotion>

      {/* Highlighted question indicator — applied via useEffect to avoid styled-jsx Turbopack issues */}
      {highlightedId && null}
    </div>
  )
}

export default MorphPanel
