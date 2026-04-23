"use client"

import React, { useState, useCallback, useRef, useEffect } from "react"
import { createPortal } from "react-dom"
import { useRouter } from "next/navigation"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { useAIContext } from "@/contexts/AIContext"
import { getActiveEditorRef } from "@/lib/editor-registry"
import { cn } from "@/lib/utils"

// ── Dimensions ─────────────────────────────────────────────
const ORB_SIZE = 52
// ~1/3 larger than old panel (340x420)
const PANEL_W = 453
const PANEL_H = 560

// ── Question context parsing ──────────────────────────────
interface QuestionCtx {
  type: "choice" | "programming"
  id: string
  chapterId: number
  subsectionIndex: number
  exerciseId: string
  question: string
  options?: string[]
  code?: string
  language?: string
  answerStatus?: "unanswered" | "correct" | "wrong"
}

function parseQuestion(el: Element): QuestionCtx | null {
  const type = el.getAttribute("data-question-type")
  const compositeId = el.getAttribute("data-question-id")
  const exerciseId = el.getAttribute("data-exercise-id")
  const question = el.getAttribute("data-question-text")
  if (!type || !question) return null
  // compositeId is "${chapterId}-${subsectionIndex}-${exerciseId}", extract both
  const parts = compositeId?.split("-")
  const chapterId = parts && parts[0] ? parseInt(parts[0]) || 1 : 1
  const subsectionIndex = parts && parts[1] ? parseInt(parts[1]) || 0 : 0
  const optionsStr = el.getAttribute("data-question-options")
  let options: string[] | undefined
  if (optionsStr) {
    try { options = JSON.parse(optionsStr) } catch { options = undefined }
  }
  const code = el.getAttribute("data-question-code") || undefined
  const language = el.getAttribute("data-question-language") || undefined
  const answerStatus = el.getAttribute("data-question-answer-status") as QuestionCtx["answerStatus"] | undefined
  return { type: type as "choice" | "programming", id: compositeId || "", chapterId, subsectionIndex, exerciseId: exerciseId || "", question, options, code, language, answerStatus }
}

// ── Mini Orb (shown in panel header) ─────────────────────
function PanelOrb({ size = 22 }: { size?: number }) {
  return (
    <div
      style={{
        width: size,
        height: size,
        borderRadius: "50%",
        background: "radial-gradient(circle at 38% 32%, rgba(186, 230, 253, 0.98), rgba(56, 189, 248, 0.9) 38%, rgba(14, 165, 233, 0.78) 65%, rgba(3, 105, 161, 0.6) 100%)",
        boxShadow: "0 2px 6px rgba(0,0,0,0.1), inset 0 1px 2px rgba(255,255,255,0.4)",
        flexShrink: 0,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <div style={{ position: "relative", width: size * 0.72, height: size * 0.72 }}>
        <svg width="50%" height="50%" viewBox="0 0 8 10" style={{ position: "absolute", top: "15%", left: "12%" }}>
          <ellipse cx="4" cy="5" rx="3" ry="4" fill="rgba(14, 165, 233, 0.7)" />
          <circle cx="4" cy="4" r="1.5" fill="white" />
        </svg>
        <svg width="50%" height="50%" viewBox="0 0 8 10" style={{ position: "absolute", top: "15%", right: "12%" }}>
          <ellipse cx="4" cy="5" rx="3" ry="4" fill="rgba(14, 165, 233, 0.7)" />
          <circle cx="4" cy="4" r="1.5" fill="white" />
        </svg>
        <svg width="60%" height="40%" viewBox="0 0 14 9" style={{ position: "absolute", bottom: "5%", left: "50%", transform: "translateX(-50%)" }}>
          <path d="M2 2 Q7 9 12 2" fill="none" stroke="rgba(14, 165, 233, 0.7)" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
      </div>
    </div>
  )
}

// ── Message bubble with Markdown ─────────────────────────
function MessageBubble({ role, content }: { role: "user" | "ai"; content: string }) {
  const isUser = role === "user"
  return (
    <div
      className="rounded-2xl px-3 py-2 leading-relaxed"
      style={{
        maxWidth: "88%",
        background: isUser ? "hsl(var(--primary))" : "hsl(var(--secondary))",
        color: isUser ? "hsl(var(--primary-foreground))" : "hsl(var(--foreground))",
        fontSize: "0.75rem",
      }}
    >
      {isUser ? (
        <span className="whitespace-pre-wrap">{content}</span>
      ) : (
        <div className="prose prose-xs prose-slate max-w-none" style={{ fontSize: "inherit" }}>
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              p: ({ children }) => <p className="mb-1 last:mb-0 whitespace-pre-wrap">{children}</p>,
              code: ({ children }) => (
                <code className="px-1 py-0.5 rounded text-[0.85em] font-mono" style={{ background: "hsl(var(--muted))", color: "hsl(var(--primary))" }}>
                  {children}
                </code>
              ),
              pre: ({ children }) => (
                <pre className="p-2 rounded-lg overflow-x-auto mb-1 last:mb-0" style={{ background: "hsl(var(--muted))" }}>
                  {children}
                </pre>
              ),
              ul: ({ children }) => <ul className="list-disc ml-3 mb-1 last:mb-0 space-y-0.5">{children}</ul>,
              ol: ({ children }) => <ol className="list-decimal ml-3 mb-1 last:mb-0 space-y-0.5">{children}</ol>,
              li: ({ children }) => <li className="leading-snug">{children}</li>,
              strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
              em: ({ children }) => <em>{children}</em>,
            }}
          >
            {content}
          </ReactMarkdown>
        </div>
      )}
    </div>
  )
}

// ── Main MorphPanel ───────────────────────────────────────
interface ChatMessage {
  role: "user" | "ai"
  content: string
}

export function MorphPanel() {
  const router = useRouter()
  const { activeQuestion, isPanelOpen, panelSpawnPos, openPanel, closePanel } = useAIContext()

  // Orb state
  const orbRef = useRef<HTMLDivElement>(null)
  const [isHovered, setIsHovered] = useState(false)
  const [isDraggingOrb, setIsDraggingOrb] = useState(false)
  const targetedQuestionRef = useRef<QuestionCtx | null>(null)
  const panelOpenedRef = useRef(false)
  const prevHighlightRef = useRef<Element | null>(null)
  const hitIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Panel state
  const panelRef = useRef<HTMLDivElement>(null)
  const [pos, setPos] = useState({ x: 100, y: 100 })
  const [isDraggingPanel, setIsDraggingPanel] = useState(false)
  const dragOffsetRef = useRef({ x: 0, y: 0 })

  // Chat state
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputValue, setInputValue] = useState("")
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingText, setStreamingText] = useState("")
  const messagesRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const prevPanelSpawnPosRef = useRef<typeof panelSpawnPos>(null)

  // ── Orb: hide when panel open, show when panel closed ──
  const [orbVisible, setOrbVisible] = useState(true)
  useEffect(() => {
    if (isPanelOpen) {
      setOrbVisible(false)
    } else {
      setOrbVisible(true)
      panelOpenedRef.current = false
    }
  }, [isPanelOpen])

  // ── Panel: set position from spawnPos ──────────────────
  useEffect(() => {
    if (!panelSpawnPos) return
    if (prevPanelSpawnPosRef.current === panelSpawnPos) return
    prevPanelSpawnPosRef.current = panelSpawnPos
    const vw = window.innerWidth
    const vh = window.innerHeight
    const x = Math.min(Math.max(panelSpawnPos.x - PANEL_W / 2, 24), vw - PANEL_W - 24)
    const y = Math.min(Math.max(panelSpawnPos.y - 60, 24), vh - PANEL_H - 24)
    setPos({ x, y })
  }, [panelSpawnPos, isPanelOpen, activeQuestion])

  // ── Scroll messages ────────────────────────────────────
  useEffect(() => {
    if (messagesRef.current) {
      messagesRef.current.scrollTop = messagesRef.current.scrollHeight
    }
  }, [messages, streamingText])

  // ── Highlight helpers ──────────────────────────────────
  const clearHighlight = useCallback(() => {
    if (prevHighlightRef.current) {
      (prevHighlightRef.current as HTMLElement).style.outline = ""
      prevHighlightRef.current = null
    }
  }, [])

  const stopHit = useCallback(() => {
    clearHighlight()
    if (hitIntervalRef.current) {
      clearInterval(hitIntervalRef.current)
      hitIntervalRef.current = null
    }
  }, [clearHighlight])

  // ── Orb: expand panel on click ─────────────────────────
  const handleOrbClick = useCallback((e: React.MouseEvent) => {
    if (isDraggingOrb) return
    e.preventDefault()
    e.stopPropagation()

    const orbEl = orbRef.current
    const orbRect = orbEl?.getBoundingClientRect()
    const spawnX = orbRect ? orbRect.left + ORB_SIZE / 2 : e.clientX
    const spawnY = orbRect ? orbRect.top + ORB_SIZE / 2 : e.clientY

    // Expand panel (no question context, just blank panel)
    openPanel({ type: null, chapterId: 0, subsectionIndex: 0, exerciseId: 0, question: "" }, { x: spawnX, y: spawnY })
  }, [isDraggingOrb, openPanel])

  // ── Orb: drag start ────────────────────────────────────
  const handleOrbPointerDown = useCallback((e: React.PointerEvent<HTMLDivElement>) => {
    if (e.button !== 0) return
    e.preventDefault()
    e.stopPropagation()

    const orbEl = orbRef.current
    if (!orbEl) return

    const rect = orbEl.getBoundingClientRect()
    targetedQuestionRef.current = null
    panelOpenedRef.current = false
    setIsDraggingOrb(true)

    // Hide orb from hit detection
    hitIntervalRef.current = setInterval(() => {
      const el = orbRef.current
      if (!el) return
      const r = el.getBoundingClientRect()
      const cx = r.left + r.width / 2
      const cy = r.top + r.height / 2

      el.style.visibility = "hidden"
      const hit = document.elementFromPoint(cx, cy)
      el.style.visibility = "visible"

      const q = hit?.closest("[data-question-context]")

      if (prevHighlightRef.current && prevHighlightRef.current !== q) {
        (prevHighlightRef.current as HTMLElement).style.outline = ""
        prevHighlightRef.current = null
      }

      if (q) {
        const ctx = parseQuestion(q)
        if (ctx) {
          const el = q as HTMLElement
          el.style.outline = '3px solid rgba(14, 165, 233, 0.9)'
          el.style.outlineOffset = '4px'
          prevHighlightRef.current = q
          targetedQuestionRef.current = ctx
        }
      } else {
        targetedQuestionRef.current = null
      }
    }, 80)

    ;(e.currentTarget as HTMLDivElement).setPointerCapture(e.pointerId)
  }, [])

  const handleOrbPointerMove = useCallback((e: React.PointerEvent<HTMLDivElement>) => {
    if (!isDraggingOrb) return
    const orbEl = orbRef.current
    if (!orbEl) return
    orbEl.style.position = "fixed"
    orbEl.style.left = `${e.clientX - ORB_SIZE / 2}px`
    orbEl.style.top = `${e.clientY - ORB_SIZE / 2}px`
    orbEl.style.right = "auto"
    orbEl.style.bottom = "auto"
  }, [isDraggingOrb])

  const handleOrbPointerUp = useCallback((e: React.PointerEvent<HTMLDivElement>) => {
    if (!isDraggingOrb) return
    e.preventDefault()
    stopHit()
    setIsDraggingOrb(false)

    const q = targetedQuestionRef.current
    if (q && !panelOpenedRef.current) {
      panelOpenedRef.current = true

      const orbEl = orbRef.current
      const orbRect = orbEl?.getBoundingClientRect()
      const spawnX = orbRect ? orbRect.left + ORB_SIZE / 2 : e.clientX
      const spawnY = orbRect ? orbRect.top + ORB_SIZE / 2 : e.clientY

      setOrbVisible(false)

      // For programming questions, get live code from the IDE editor
      let code = q.code
      let language = q.language
      if (q.type === "programming") {
        const editorRef = getActiveEditorRef()
        if (editorRef?.current) {
          const ctx = editorRef.current.getExerciseContext()
          code = editorRef.current.getCode()
          language = ctx?.language ?? q.language ?? 'python'
          if (ctx) {
            q.question = ctx.question
            q.options = ctx.options
          }
        }
      }

      openPanel({
        type: q.type,
        chapterId: q.chapterId,
        subsectionIndex: q.subsectionIndex,
        exerciseId: q.exerciseId ? parseInt(q.exerciseId) || 0 : 0,
        question: q.question,
        options: q.options,
        code,
        language,
        answerStatus: q.answerStatus,
      }, { x: spawnX, y: spawnY })
    } else {
      // Snap orb back to corner
      const orbEl = orbRef.current
      if (orbEl) {
        orbEl.style.position = "fixed"
        orbEl.style.left = "auto"
        orbEl.style.top = "auto"
        orbEl.style.right = "24px"
        orbEl.style.bottom = "24px"
      }
    }

    targetedQuestionRef.current = null
  }, [isDraggingOrb, openPanel, stopHit])

  // ── Panel drag ─────────────────────────────────────────
  const handlePanelDragStart = useCallback((e: React.PointerEvent<HTMLDivElement>) => {
    const target = e.target as HTMLElement
    if (target.closest("button, input, textarea, select, a")) return
    const dragHandle = target.closest("[data-drag-handle]")
    if (!dragHandle) return
    e.preventDefault()
    e.stopPropagation()
    const rect = panelRef.current?.getBoundingClientRect()
    if (!rect) return
    dragOffsetRef.current = { x: e.clientX - rect.left, y: e.clientY - rect.top }
    setIsDraggingPanel(true)
    ;(e.currentTarget as HTMLDivElement).setPointerCapture(e.pointerId)
  }, [])

  const handlePanelDragMove = useCallback((e: React.PointerEvent<HTMLDivElement>) => {
    if (!isDraggingPanel) return
    setPos({ x: e.clientX - dragOffsetRef.current.x, y: e.clientY - dragOffsetRef.current.y })
  }, [isDraggingPanel])

  const handlePanelDragEnd = useCallback(() => {
    setIsDraggingPanel(false)
  }, [])

  // ── Chat ───────────────────────────────────────────────
  const buildPrompt = useCallback((
    question: string,
    options: string[] | undefined,
    userMessage: string,
    code?: string,
    language?: string,
    answerStatus?: "unanswered" | "correct" | "wrong"
  ) => {
    const optsStr = options
      ? "\n选项：\n" + options.map((o, i) => `${String.fromCharCode(65 + i)}. ${o}`).join("\n")
      : ""
    const codeStr = code && language
      ? `\n学生当前代码（语言：${language}）：\n\`\`\`${language}\n${code}\n\`\`\``
      : ""
    const isUnansweredChoice = !code && options && answerStatus === "unanswered"
    // Only redirect if user is directly asking for the answer
    const isAskingAnswer = /答案|选哪个|选什么|选A|选B|选C|选D|正确|对不对|对吗/.test(userMessage)
    const unansweredNote = isUnansweredChoice && isAskingAnswer
      ? "\n注意：学生尚未回答这道选择题。请先鼓励学生自己思考并给出答案，再酌情给予提示。不要直接告诉学生正确答案。"
      : ""
    return `你是学生的编程学习助手。当前题目：${question}${optsStr}${codeStr}${unansweredNote}\n学生问题：${userMessage}\n请根据以上题目信息，用中文给出有帮助的回答。`
  }, [])

  const sendMessage = useCallback(async () => {
    const text = inputValue.trim()
    if (!text || isStreaming) return

    const userMessage = text
    setInputValue("")
    setMessages(prev => [...prev, { role: "user", content: userMessage }])
    setIsStreaming(true)
    setStreamingText("")

    const prompt = activeQuestion?.question
      ? buildPrompt(
          activeQuestion.question || "",
          activeQuestion.options,
          userMessage,
          activeQuestion.code,
          activeQuestion.language,
          activeQuestion.answerStatus
        )
      : `你是一位耐心的编程老师。问题：\n\n${userMessage}\n\n请给出简洁、有帮助的回答。`

    try {
      const token = localStorage.getItem("token")
      if (!token) return

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
      const response = await fetch(
        `${apiUrl}/api/ai/chat/stream`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ message: prompt, context: null }),
        }
      )

      if (!response.ok) {
        const text = await response.text()
        if (response.status === 401) {
          localStorage.removeItem("token")
          localStorage.removeItem("user")
          router.push("/login")
          return
        }
        throw new Error(`请求失败: ${response.status} — ${text}`)
      }
      if (!response.body) throw new Error("无响应体")

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let fullText = ""

      while (true) {
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
                setStreamingText(fullText)
              }
            } catch { /* skip malformed */ }
          }
        }
      }
      // Streaming done — commit final text as AI message
      setMessages(prev => [...prev, { role: "ai", content: fullText }])
    } catch (err) {
      setMessages(prev => [...prev, { role: "ai", content: `抱歉，AI 服务暂时不可用: ${err instanceof Error ? err.message : String(err)}` }])
    } finally {
      setIsStreaming(false)
      setStreamingText("")
    }
  }, [inputValue, isStreaming, activeQuestion, buildPrompt])

  const handleQuickPrompt = useCallback((prompt: string) => {
    setInputValue(prompt)
    setTimeout(() => textareaRef.current?.focus(), 50)
  }, [])

  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      e.preventDefault()
      sendMessage()
    }
    if (e.key === "Escape") {
      closePanel()
    }
  }, [sendMessage, closePanel])

  const handleClose = useCallback(() => {
    closePanel()
    setMessages([])
  }, [closePanel])

  useEffect(() => {
    return () => { stopHit() }
  }, [stopHit])

  // ── Render ─────────────────────────────────────────────
  return (
    <>
      {/* ── Orb (always visible when not panel open) ── */}
      {orbVisible && createPortal(
        <div
          ref={orbRef}
          onPointerDown={handleOrbPointerDown}
          onPointerMove={handleOrbPointerMove}
          onPointerUp={handleOrbPointerUp}
          onPointerCancel={handleOrbPointerUp}
          onClick={handleOrbClick}
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => !isDraggingOrb && setIsHovered(false)}
          className="fixed select-none z-[9999] animate-orb-bob"
          style={{
            right: 24,
            bottom: 24,
            width: ORB_SIZE,
            height: ORB_SIZE,
            borderRadius: ORB_SIZE / 2,
            cursor: isDraggingOrb ? "grabbing" : "grab",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            background: isHovered
              ? "radial-gradient(circle at 38% 32%, rgba(186, 230, 253, 0.98), rgba(56, 189, 248, 0.9) 38%, rgba(14, 165, 233, 0.78) 65%, rgba(3, 105, 161, 0.6) 100%)"
              : "radial-gradient(circle at 38% 32%, rgba(224, 242, 254, 0.96), rgba(125, 211, 252, 0.88) 38%, rgba(56, 189, 248, 0.75) 65%, rgba(14, 165, 233, 0.55) 100%)",
            boxShadow: isHovered
              ? "0 4px 16px rgba(0,0,0,0.15), inset 0 1px 2px rgba(255,255,255,0.5)"
              : "0 2px 8px rgba(0,0,0,0.1), inset 0 1px 2px rgba(255,255,255,0.4)",
            pointerEvents: "auto",
            transition: isDraggingOrb ? "none" : "background 0.2s, box-shadow 0.2s",
          }}
        >
          {/* Cute face */}
          <div style={{ position: "relative", width: 36, height: 36 }}>
            <svg width="8" height="10" viewBox="0 0 8 10" style={{ position: "absolute", top: 8, left: 6 }}>
              <ellipse cx="4" cy="5" rx="3" ry="4" fill="rgba(14, 165, 233, 0.7)" />
              <circle cx="4" cy="4" r="1.5" fill="white" />
            </svg>
            <svg width="8" height="10" viewBox="0 0 8 10" style={{ position: "absolute", top: 8, right: 6 }}>
              <ellipse cx="4" cy="5" rx="3" ry="4" fill="rgba(14, 165, 233, 0.7)" />
              <circle cx="4" cy="4" r="1.5" fill="white" />
            </svg>
            <svg width="14" height="9" viewBox="0 0 14 9" style={{ position: "absolute", bottom: 5, left: "50%", transform: "translateX(-50%)" }}>
              <path d="M2 2 Q7 9 12 2" fill="none" stroke="rgba(14, 165, 233, 0.7)" strokeWidth="1.8" strokeLinecap="round" />
            </svg>
          </div>
        </div>,
        document.body
      )}

      {/* ── Panel portal ── */}
      {isPanelOpen && createPortal(
        <div
          ref={panelRef}
          onPointerDown={handlePanelDragStart}
          onPointerMove={handlePanelDragMove}
          onPointerUp={handlePanelDragEnd}
          onPointerCancel={handlePanelDragEnd}
          className="fixed z-[9998] flex flex-col overflow-hidden animate-panel-slide-in"
          style={{
            width: PANEL_W,
            height: PANEL_H,
            left: pos.x,
            top: pos.y,
            background: "hsl(var(--background) / 0.96)",
            border: "1px solid hsl(var(--border) / 0.7)",
            borderRadius: 16,
            boxShadow: "0 24px 64px hsl(var(--foreground) / 0.2), 0 0 0 1px hsl(var(--border) / 0.3)",
            backdropFilter: "blur(16px)",
            cursor: isDraggingPanel ? "grabbing" : "default",
            userSelect: "none",
          }}
        >

          {/* ── Header (drag handle) ── */}
          <div
            className="flex items-center justify-between px-4 py-3 border-b shrink-0 cursor-grab active:cursor-grabbing select-none"
            style={{ borderColor: "hsl(var(--border) / 0.5)" }}
            data-drag-handle
          >
            <div className="flex items-center gap-2.5">
              <PanelOrb size={22} />
              <div>
                <p className="text-sm font-semibold" style={{ color: "hsl(var(--foreground))" }}>AI 学习助手</p>
                <p className="text-xs" style={{ color: "hsl(var(--muted-foreground))" }}>
                  {activeQuestion?.question ? "已关联当前题目" : "随时提问"}
                </p>
              </div>
            </div>
            <button type="button"
              onClick={handleClose}
              className="w-7 h-7 flex items-center justify-center rounded-lg transition-colors hover:bg-black/5"
              style={{ color: "hsl(var(--muted-foreground))" }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>

          {/* ── Quick prompts ── */}
          <div className="flex flex-wrap gap-1.5 px-3 py-2.5 shrink-0">
            {activeQuestion?.type === "programming" ? (
              /* Programming questions — adapt based on answer status */
              (() => {
                const base = [
                  { label: "解释题意", prompt: "请详细解释这道编程题的题意和要求" },
                ]
                if (activeQuestion.answerStatus === "wrong") {
                  return [
                    ...base,
                    { label: "纠错", prompt: "请分析我的代码哪里出了问题，如何修复" },
                    { label: "检查代码", prompt: "请帮我检查代码的逻辑是否有问题" },
                    { label: "类似题", prompt: "请给我一道类似的编程练习题" },
                  ]
                }
                return [
                  ...base,
                  { label: "提示下一步", prompt: "这道题的解题思路是什么？请给我一个提示" },
                  { label: "类似题", prompt: "请给我一道类似的编程练习题" },
                ]
              })().map(qp => (
                <button type="button"
                  key={qp.label}
                  onClick={() => handleQuickPrompt(qp.prompt)}
                  className="px-2.5 py-1 rounded-full text-xs border transition-all hover:bg-black/5"
                  style={{
                    background: "hsl(var(--secondary) / 0.5)",
                    borderColor: "hsl(var(--border))",
                    color: "hsl(var(--foreground))",
                  }}
                >
                  {qp.label}
                </button>
              ))
            ) : (
              /* Choice questions — adapt based on answer status */
              (() => {
                const base: { label: string; prompt: string }[] = [
                  { label: "解释题意", prompt: "请详细解释这道题的题意和各个选项的含义，不要透露正确答案" },
                ]
                if (activeQuestion?.answerStatus === "wrong") {
                  return [
                    ...base,
                    { label: "分析错误", prompt: "请分析我选的答案哪里不对，为什么是错的（不要直接说正确答案是什么，引导学生自行思考）" },
                    { label: "类似题", prompt: "请给我一道类似的练习题" },
                  ]
                }
                if (activeQuestion?.answerStatus === "correct") {
                  return [
                    { label: "类似题", prompt: "请给我一道类似的练习题" },
                  ]
                }
                // unanswered
                return [
                  ...base,
                  { label: "提示思路", prompt: "这道题的解题思路是什么？" },
                ]
              })().map(qp => (
                <button type="button"
                  key={qp.label}
                  onClick={() => handleQuickPrompt(qp.prompt)}
                  className="px-2.5 py-1 rounded-full text-xs border transition-all hover:bg-black/5"
                  style={{
                    background: "hsl(var(--secondary) / 0.5)",
                    borderColor: "hsl(var(--border))",
                    color: "hsl(var(--foreground))",
                  }}
                >
                  {qp.label}
                </button>
              ))
            )}
          </div>

          {/* ── Messages ── */}
          <div
            ref={messagesRef}
            className="flex-1 overflow-y-auto px-3 py-2 flex flex-col gap-2 min-h-0"
          >
            {messages.length === 0 && !isStreaming && (
              <div className="h-full flex items-center justify-center">
                <p className="text-xs text-center leading-relaxed" style={{ color: "hsl(var(--muted-foreground))" }}>
                  选择上方快捷问题
                  <br />或直接输入问题
                </p>
              </div>
            )}
            {messages.map((msg, i) => (
              <div
                key={i}
                className="flex"
                style={{ justifyContent: msg.role === "user" ? "flex-end" : "flex-start" }}
              >
                <MessageBubble role={msg.role} content={msg.content} />
              </div>
            ))}
            {/* Streaming bubble — AI on left */}
            {isStreaming && (
              <div className="flex" style={{ justifyContent: "flex-start" }}>
                <div
                  className="rounded-2xl rounded-bl-sm px-3 py-2"
                  style={{ background: "hsl(var(--secondary))", maxWidth: "88%", fontSize: "0.75rem" }}
                >
                  {streamingText ? (
                    <div className="prose prose-xs prose-slate max-w-none" style={{ fontSize: "inherit" }}>
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                          p: ({ children }) => <p className="mb-1 last:mb-0 whitespace-pre-wrap">{children}</p>,
                          code: ({ children }) => (
                            <code className="px-1 py-0.5 rounded text-[0.85em] font-mono" style={{ background: "hsl(var(--muted))", color: "hsl(var(--primary))" }}>
                              {children}
                            </code>
                          ),
                          pre: ({ children }) => (
                            <pre className="p-2 rounded-lg overflow-x-auto mb-1 last:mb-0" style={{ background: "hsl(var(--muted))" }}>
                              {children}
                            </pre>
                          ),
                          ul: ({ children }) => <ul className="list-disc ml-3 mb-1 last:mb-0 space-y-0.5">{children}</ul>,
                          ol: ({ children }) => <ol className="list-decimal ml-3 mb-1 last:mb-0 space-y-0.5">{children}</ol>,
                          li: ({ children }) => <li className="leading-snug">{children}</li>,
                          strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                          em: ({ children }) => <em>{children}</em>,
                        }}
                      >
                        {streamingText}
                      </ReactMarkdown>
                    </div>
                  ) : (
                    /* Bouncing dots while waiting for first token */
                    <div className="flex items-center gap-1 py-1">
                      {[0, 1, 2].map(i => (
                        <span
                          key={i}
                          className={cn(
                            "block w-1.5 h-1.5 rounded-full animate-bounce-dot",
                            i === 0 ? "animate-bounce-dot-0" : i === 1 ? "animate-bounce-dot-1" : "animate-bounce-dot-2"
                          )}
                          style={{ background: "hsl(var(--muted-foreground))" }}
                        />
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* ── Input ── */}
          <div
            className="px-3 pb-3 pt-2 shrink-0"
            style={{ borderTop: "1px solid hsl(var(--border) / 0.4)" }}
          >
            <form
              onSubmit={e => { e.preventDefault(); sendMessage() }}
              className="flex items-end gap-2"
            >
              <textarea
                ref={textareaRef}
                value={inputValue}
                onChange={e => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="针对这道题继续提问..."
                rows={3}
                className="flex-1 resize-none rounded-xl border px-3 py-2 text-xs focus:outline-none focus:ring-2"
                style={{
                  background: "hsl(var(--secondary) / 0.5)",
                  borderColor: "hsl(var(--border))",
                  color: "hsl(var(--foreground))",
                }}
                disabled={isStreaming}
              />
              <button type="button"
                type="submit"
                disabled={!inputValue.trim() || isStreaming}
                className="w-8 h-8 flex items-center justify-center rounded-xl transition-colors shrink-0 disabled:opacity-40 disabled:cursor-not-allowed"
                style={{ background: "hsl(var(--primary))", color: "hsl(var(--primary-foreground))" }}
              >
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" />
                </svg>
              </button>
            </form>
          </div>
        </div>,
        document.body
      )}
    </>
  )
}

export default MorphPanel
