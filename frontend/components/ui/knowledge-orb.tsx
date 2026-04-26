"use client"

import React, { useState, useCallback, useRef, useEffect } from "react"
import { createPortal } from "react-dom"
import { useRouter } from "next/navigation"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { useAIContext, type KnowledgePointContext } from "@/contexts/AIContext"
import { cn } from "@/lib/utils"
import { createNoteFromQuestion } from "@/lib/api/notes"
import { getStoredToken } from "@/lib/api"
import { FileText } from "lucide-react"

// ── Dimensions ─────────────────────────────────────────────
const ORB_SIZE = 52
const PANEL_W = 453
const PANEL_H = 560

// ── Knowledge Point context parsing ───────────────────────
function parseKnowledgePoint(el: Element): KnowledgePointContext | null {
  const id = el.getAttribute("data-knowledge-point-id")
  const title = el.getAttribute("data-knowledge-point-title")
  const content = el.getAttribute("data-knowledge-point-content")
  const examplesStr = el.getAttribute("data-knowledge-point-examples")
  const difficulty = el.getAttribute("data-knowledge-point-difficulty")
  const index = el.getAttribute("data-knowledge-point-index")
  const adjacentStr = el.getAttribute("data-knowledge-point-adjacent")

  if (!id || !title || !content) return null

  let examples: string[] = []
  if (examplesStr) {
    try { examples = JSON.parse(examplesStr) } catch { examples = [] }
  }

  let adjacentPoints: Array<{ id: string; title: string }> = []
  if (adjacentStr) {
    try { adjacentPoints = JSON.parse(adjacentStr) } catch { adjacentPoints = [] }
  }

  return {
    id,
    title,
    content,
    examples,
    difficulty: difficulty ? parseInt(difficulty) || 1 : 1,
    index: index ? parseInt(index) || 0 : 0,
    adjacentPoints,
  }
}

// ── Question context parsing (for choice/fill_blank) ──────
interface QuestionCtx {
  type: "choice" | "fill_blank"
  id: string
  question: string
  options?: string[]
  answerStatus?: "unanswered" | "correct" | "wrong"
}

function parseQuestion(el: Element): QuestionCtx | null {
  const type = el.getAttribute("data-question-type")
  const id = el.getAttribute("data-question-id") || ""
  const question = el.getAttribute("data-question-text")
  if (!type || !question) return null

  const optionsStr = el.getAttribute("data-question-options")
  let options: string[] | undefined
  if (optionsStr) {
    try { options = JSON.parse(optionsStr) } catch { options = undefined }
  }
  const answerStatus = el.getAttribute("data-question-answer-status") as QuestionCtx["answerStatus"] | undefined
  return { type: type as "choice" | "fill_blank", id, question, options, answerStatus }
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
      {/* Book icon */}
      <svg
        width="60%"
        height="60%"
        viewBox="0 0 24 24"
        fill="none"
        stroke="rgba(14, 165, 233, 0.8)"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
        <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
      </svg>
    </div>
  )
}

// ── Message bubble with Markdown ─────────────────────────
interface MessageBubbleProps {
  role: "user" | "ai"
  content: string
  /** Context IDs for saving as note */
  courseId?: number
  chapterId?: number
  sectionId?: number
  exerciseId?: number
  knowledgePoints?: string[]
}

function MessageBubble({ role, content, courseId, chapterId, sectionId, exerciseId, knowledgePoints }: MessageBubbleProps) {
  const isUser = role === "user"
  const [isSaving, setIsSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  const handleSaveAsNote = useCallback(async () => {
    if (!content || isSaving || saved) return
    const token = getStoredToken()
    if (!token) return

    setIsSaving(true)
    try {
      await createNoteFromQuestion(token, {
        title: "AI 回答笔记",
        content: content,
        course_id: courseId,
        chapter_id: chapterId,
        section_id: sectionId,
        exercise_id: exerciseId,
        source: "ai_answer",
        ai_answer_content: content,
        knowledge_points: knowledgePoints || [],
      })
      setSaved(true)
    } catch (error) {
      console.error("[笔记] 保存失败:", error)
      alert("笔记保存失败，请重试")
    } finally {
      setIsSaving(false)
    }
  }, [content, isSaving, saved, courseId, chapterId, sectionId, exerciseId, knowledgePoints])

  return (
    <div className="flex flex-col gap-1">
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
      {/* Save as note button for AI messages */}
      {!isUser && (
        <button type="button"
          onClick={handleSaveAsNote}
          disabled={isSaving || saved}
          className="flex items-center gap-1 px-2 py-1 text-xs rounded-lg transition-colors hover:bg-black/10 disabled:opacity-50 w-fit"
          style={{ color: saved ? "hsl(var(--success))" : "hsl(var(--primary))" }}
        >
          <FileText className="w-3 h-3" />
          {saved ? "已保存" : isSaving ? "保存中..." : "记为笔记"}
        </button>
      )}
    </div>
  )
}

// ── Main KnowledgeOrb ─────────────────────────────────────
interface ChatMessage {
  role: "user" | "ai"
  content: string
}

type ContextMode = "knowledge" | "question" | null

interface KnowledgeOrbProps {
  /** 如果为 true，拖动到题目时会显示提示而不是打开面板 */
  disabledForQuestion?: boolean
  /** Context IDs for saving AI answers as notes */
  courseId?: number
  chapterId?: number
  sectionId?: number
  exerciseId?: number
  knowledgePoints?: string[]
}

export function KnowledgeOrb({
  disabledForQuestion = false,
  courseId,
  chapterId,
  sectionId,
  exerciseId,
  knowledgePoints
}: KnowledgeOrbProps) {
  const router = useRouter()
  const {
    activeKnowledgeQuestion,
    isKnowledgePanelOpen,
    knowledgePanelSpawnPos,
    openKnowledgePanel,
    closeKnowledgePanel,
  } = useAIContext()

  // Orb state
  const orbRef = useRef<HTMLDivElement>(null)
  const [isHovered, setIsHovered] = useState(false)
  const [isDraggingOrb, setIsDraggingOrb] = useState(false)
  const targetedKnowledgeRef = useRef<KnowledgePointContext | null>(null)
  const targetedQuestionRef = useRef<QuestionCtx | null>(null)
  const panelOpenedRef = useRef(false)
  const prevHighlightRef = useRef<Element | null>(null)
  const hitIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Panel state
  const panelRef = useRef<HTMLDivElement>(null)
  const [pos, setPos] = useState({ x: 100, y: 100 })
  const [isDraggingPanel, setIsDraggingPanel] = useState(false)
  const dragOffsetRef = useRef({ x: 0, y: 0 })

  // Context mode
  const [contextMode, setContextMode] = useState<ContextMode>(null)

  // Chat state
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputValue, setInputValue] = useState("")
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingText, setStreamingText] = useState("")
  const messagesRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const prevPanelSpawnPosRef = useRef<typeof knowledgePanelSpawnPos>(null)

  // ── Orb: hide when panel open, show when panel closed ──
  const [orbVisible, setOrbVisible] = useState(true)

  // ── "Please answer first" toast state ──
  const [showDisabledToast, setShowDisabledToast] = useState(false)

  useEffect(() => {
    if (isKnowledgePanelOpen) {
      setOrbVisible(false)
    } else {
      setOrbVisible(true)
      panelOpenedRef.current = false
      // Reset orb to default position when panel closes
      if (orbRef.current) {
        orbRef.current.style.position = "fixed"
        orbRef.current.style.left = ""
        orbRef.current.style.top = ""
        orbRef.current.style.right = "24px"
        orbRef.current.style.bottom = "24px"
      }
    }
  }, [isKnowledgePanelOpen])

  // ── Panel: set position from spawnPos ──────────────────
  useEffect(() => {
    if (!knowledgePanelSpawnPos) return
    if (prevPanelSpawnPosRef.current === knowledgePanelSpawnPos) return
    prevPanelSpawnPosRef.current = knowledgePanelSpawnPos
    const vw = window.innerWidth
    const vh = window.innerHeight
    const x = Math.min(Math.max(knowledgePanelSpawnPos.x - PANEL_W / 2, 24), vw - PANEL_W - 24)
    const y = Math.min(Math.max(knowledgePanelSpawnPos.y - 60, 24), vh - PANEL_H - 24)
    setPos({ x, y })
  }, [knowledgePanelSpawnPos, isKnowledgePanelOpen, activeKnowledgeQuestion])

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
    // If we just finished a drag operation, don't open panel
    if (panelOpenedRef.current) return
    e.preventDefault()
    e.stopPropagation()

    const orbEl = orbRef.current
    const orbRect = orbEl?.getBoundingClientRect()
    const spawnX = orbRect ? orbRect.left + ORB_SIZE / 2 : e.clientX
    const spawnY = orbRect ? orbRect.top + ORB_SIZE / 2 : e.clientY

    // Expand panel with no context (free questioning)
    const blankQuestion = {
      type: "knowledge" as const,
      knowledgePoint: {
        id: "",
        title: "",
        content: "",
        examples: [],
        difficulty: 1,
        index: -1,
        adjacentPoints: [],
      },
    }
    setContextMode(null)
    openKnowledgePanel(blankQuestion, { x: spawnX, y: spawnY })
  }, [openKnowledgePanel])

  // ── Orb: drag start ────────────────────────────────────
  const handleOrbPointerDown = useCallback((e: React.PointerEvent<HTMLDivElement>) => {
    if (e.button !== 0) return
    e.preventDefault()
    e.stopPropagation()

    const orbEl = orbRef.current
    if (!orbEl) return

    targetedKnowledgeRef.current = null
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

      // Try knowledge point first
      const kp = hit?.closest("[data-knowledge-point]")
      const q = hit?.closest("[data-question-context]")

      if (prevHighlightRef.current && prevHighlightRef.current !== kp && prevHighlightRef.current !== q) {
        (prevHighlightRef.current as HTMLElement).style.outline = ""
        prevHighlightRef.current = null
      }

      if (kp) {
        const ctx = parseKnowledgePoint(kp)
        if (ctx) {
          const el = kp as HTMLElement
          el.style.outline = '3px solid rgba(16, 185, 129, 0.9)'
          el.style.outlineOffset = '4px'
          prevHighlightRef.current = kp
          targetedKnowledgeRef.current = ctx
          targetedQuestionRef.current = null
        }
      } else if (q) {
        const ctx = parseQuestion(q)
        if (ctx) {
          const el = q as HTMLElement
          el.style.outline = '3px solid rgba(14, 165, 233, 0.9)'
          el.style.outlineOffset = '4px'
          prevHighlightRef.current = q
          targetedQuestionRef.current = ctx
          targetedKnowledgeRef.current = null
        }
      } else {
        targetedKnowledgeRef.current = null
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
    orbEl.style.touchAction = "none"
  }, [isDraggingOrb])

  const handleOrbPointerUp = useCallback((e: React.PointerEvent<HTMLDivElement>) => {
    if (!isDraggingOrb) return
    e.preventDefault()
    stopHit()
    setIsDraggingOrb(false)

    const kp = targetedKnowledgeRef.current
    const q = targetedQuestionRef.current

    // Debug log
    console.log('[KnowledgeOrb] Pointer up:', {
      hasKp: !!kp,
      hasQ: !!q,
      disabledForQuestion,
      qType: q?.type,
      qId: q?.id
    })

    if (kp && !panelOpenedRef.current) {
      panelOpenedRef.current = true

      const orbEl = orbRef.current
      const orbRect = orbEl?.getBoundingClientRect()
      const spawnX = orbRect ? orbRect.left + ORB_SIZE / 2 : e.clientX
      const spawnY = orbRect ? orbRect.top + ORB_SIZE / 2 : e.clientY

      setOrbVisible(false)
      setContextMode("knowledge")

      openKnowledgePanel(
        {
          type: "knowledge",
          knowledgePoint: kp,
        },
        { x: spawnX, y: spawnY }
      )
    } else if (q && !panelOpenedRef.current) {
      // Check if question AI is disabled (user hasn't answered yet)
      if (disabledForQuestion) {
        // Show a brief toast message instead of opening panel
        console.log('[KnowledgeOrb] Disabled for question - showing toast, NOT opening panel')
        panelOpenedRef.current = true // Mark as handled to prevent click event from opening panel
        setShowDisabledToast(true)
        setTimeout(() => setShowDisabledToast(false), 2000)
        // Snap orb back to default position
        const orbEl = orbRef.current
        if (orbEl) {
          orbEl.style.position = "fixed"
          orbEl.style.left = ""
          orbEl.style.top = ""
          orbEl.style.right = "24px"
          orbEl.style.bottom = "24px"
        }
      } else {
        panelOpenedRef.current = true

        const orbEl = orbRef.current
        const orbRect = orbEl?.getBoundingClientRect()
        const spawnX = orbRect ? orbRect.left + ORB_SIZE / 2 : e.clientX
        const spawnY = orbRect ? orbRect.top + ORB_SIZE / 2 : e.clientY

        setOrbVisible(false)
        setContextMode("question")

        // For question mode, we still use knowledge panel but with question context
        openKnowledgePanel(
          {
            type: "knowledge",
            knowledgePoint: {
              id: q.id,
              title: q.question,
              content: `题目类型：${q.type === "choice" ? "选择题" : "填空题"}\n\n${q.options ? "选项：\n" + q.options.map((o, i) => `${String.fromCharCode(65 + i)}. ${o}`).join("\n") : ""}`,
              examples: [],
              difficulty: 1,
              index: 0,
              adjacentPoints: [],
            },
          },
          { x: spawnX, y: spawnY }
        )
      }
    } else {
      // Snap orb back to default position
      const orbEl = orbRef.current
      if (orbEl) {
        orbEl.style.position = "fixed"
        orbEl.style.left = ""
        orbEl.style.top = ""
        orbEl.style.right = "24px"
        orbEl.style.bottom = "24px"
      }
    }

    targetedKnowledgeRef.current = null
    targetedQuestionRef.current = null
  }, [isDraggingOrb, openKnowledgePanel, stopHit, disabledForQuestion])

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

  // ── Clear outline on unmount ────────────────────────────
  useEffect(() => {
    return () => {
      stopHit()
      if (prevHighlightRef.current) {
        (prevHighlightRef.current as HTMLElement).style.outline = ""
      }
    }
  }, [stopHit])

  // ── Chat ───────────────────────────────────────────────
  const buildPrompt = useCallback((
    kp: KnowledgePointContext,
    userMessage: string,
    mode: ContextMode
  ) => {
    if (mode === "question") {
      // Question mode: help with choice/fill_blank questions
      const optsStr = kp.examples && kp.examples.length > 0
        ? "\n选项：\n" + kp.examples.map((o, i) => `${String.fromCharCode(65 + i)}. ${o}`).join("\n")
        : ""
      return `你是学生的编程学习助手。当前题目：
${kp.title}${optsStr}

学生问题：${userMessage}
请根据以上题目信息，用中文给出有帮助的回答。`
    }

    // Knowledge mode
    const examplesStr = kp.examples && kp.examples.length > 0
      ? "\n示例代码：\n" + kp.examples.map((ex, i) => `\`\`\`\n${ex}\n\`\`\``).join("\n")
      : ""
    const adjacentStr = kp.adjacentPoints && kp.adjacentPoints.length > 0
      ? "\n相邻知识点：\n" + kp.adjacentPoints.map(p => `- ${p.title}`).join("\n")
      : ""

    return `你是学生的编程学习助手。当前正在学习知识点：
知识点 #${kp.index + 1}：${kp.title}
内容：${kp.content}${examplesStr}${adjacentStr}
学生问题：${userMessage}
请根据以上知识点内容，用中文给出有帮助的回答。`
  }, [])

  const sendMessage = useCallback(async () => {
    const text = inputValue.trim()
    if (!text || isStreaming) return

    const userMessage = text
    setInputValue("")
    setMessages(prev => [...prev, { role: "user", content: userMessage }])
    setIsStreaming(true)
    setStreamingText("")

    const kp = activeKnowledgeQuestion?.knowledgePoint
    const hasContext = kp && kp.id !== ""

    const prompt = hasContext
      ? buildPrompt(kp, userMessage, contextMode)
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
        const errorText = await response.text()
        if (response.status === 401) {
          localStorage.removeItem("token")
          localStorage.removeItem("user")
          router.push("/login")
          return
        }
        throw new Error(`请求失败: ${response.status} — ${errorText}`)
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
      setMessages(prev => [...prev, { role: "ai", content: fullText }])
    } catch (err) {
      setMessages(prev => [...prev, { role: "ai", content: `抱歉，AI 服务暂时不可用: ${err instanceof Error ? err.message : String(err)}` }])
    } finally {
      setIsStreaming(false)
      setStreamingText("")
    }
  }, [inputValue, isStreaming, activeKnowledgeQuestion, contextMode, buildPrompt, router])

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
      closeKnowledgePanel()
    }
  }, [sendMessage, closeKnowledgePanel])

  const handleClose = useCallback(() => {
    closeKnowledgePanel()
    setMessages([])
  }, [closeKnowledgePanel])

  // ── Render ─────────────────────────────────────────────
  return (
    <>
      {/* ── "Please answer first" toast ── */}
      {showDisabledToast && createPortal(
        <div
          className="fixed z-[10000] pointer-events-none"
          style={{
            bottom: '180px',
            left: '50%',
            transform: 'translateX(-50%)',
          }}
        >
          <div
            className="bg-amber-100 dark:bg-amber-900/80 text-amber-700 dark:text-amber-200 px-4 py-2 rounded-lg shadow-md text-sm font-medium flex items-center gap-2 animate-fade-in"
            style={{
              border: '1px solid rgba(245, 158, 11, 0.3)',
            }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            先试试自己的智慧吧！
          </div>
        </div>,
        document.body
      )}

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
            touchAction: "none",
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
          {/* Cute face with book icon */}
          <div style={{ position: "relative", width: 36, height: 36 }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="rgba(14, 165, 233, 0.8)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ position: "absolute", top: 9, left: 9 }}>
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
            </svg>
          </div>
        </div>,
        document.body
      )}

      {/* ── Panel portal ── */}
      {isKnowledgePanelOpen && createPortal(
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
                  {activeKnowledgeQuestion?.knowledgePoint?.id
                    ? contextMode === "question"
                      ? "已关联当前题目"
                      : "已关联当前知识点"
                    : "随时提问"}
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
            {contextMode === "question" ? (
              /* Question mode: choice/fill_blank */
              [
                { label: "解释题意", prompt: "请详细解释这道题的题意和要求" },
                { label: "提示思路", prompt: "这道题的解题思路是什么？" },
                { label: "类似题", prompt: "请给我一道类似的练习题" },
              ].map(qp => (
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
            ) : activeKnowledgeQuestion?.knowledgePoint?.id ? (
              /* Knowledge mode */
              [
                { label: "详细解释", prompt: "请详细解释这个知识点的含义和应用场景" },
                { label: "示例讲解", prompt: "请结合示例代码详细讲解这个知识点的用法" },
                { label: "注意事项", prompt: "使用这个知识点有什么需要注意的地方？" },
                { label: "相关知识点", prompt: "有哪些相关的知识点需要一起学习？" },
              ].map(qp => (
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
              /* Free questioning mode */
              [
                { label: "帮我解释", prompt: "请帮我解释这个概念" },
                { label: "举例说明", prompt: "请给我一个实际的应用例子" },
                { label: "常见问题", prompt: "这个知识点有哪些常见的问题？" },
              ].map(qp => (
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
                <MessageBubble
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
                placeholder={contextMode === "question" ? "针对题目继续提问..." : "针对知识点继续提问..."}
                rows={3}
                className="flex-1 resize-none rounded-xl border px-3 py-2 text-xs focus:outline-none focus:ring-2"
                style={{
                  background: "hsl(var(--secondary) / 0.5)",
                  borderColor: "hsl(var(--border))",
                  color: "hsl(var(--foreground))",
                }}
                disabled={isStreaming}
              />
              <button
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

export default KnowledgeOrb
