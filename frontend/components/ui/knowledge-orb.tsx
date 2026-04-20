"use client"

import React, { useState, useCallback, useRef, useEffect } from "react"
import { createPortal } from "react-dom"
import { useRouter } from "next/navigation"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { FileText } from "lucide-react"
import { useAIContext } from "@/contexts/AIContext"
import { cn } from "@/lib/utils"
import { getStoredToken } from "@/lib/api"
import { createNoteFromQuestion } from "@/lib/api/notes"

// ── Dimensions ─────────────────────────────────────────────
const ORB_SIZE = 52
const PANEL_W = 453
const PANEL_H = 560

// ── Knowledge Point context parsing ───────────────────────
interface KnowledgePointCtx {
  id: string
  title: string
  content: string
  examples: string[]
  difficulty: number
  index: number
  adjacentPoints: Array<{ id: string; title: string }>
}

function parseKnowledgePoint(el: Element): KnowledgePointCtx | null {
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
          style={{ position: "absolute", top: "20%", left: "20%" }}
        >
          <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
          <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
        </svg>
      </div>
    </div>
  )
}

// ── Message bubble with Markdown ─────────────────────────
function MessageBubble({ role, content, onSaveAsNote }: { role: "user" | "ai"; content: string; onSaveAsNote?: (content: string) => void }) {
  const isUser = role === "user"
  const [isSaving, setIsSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  const handleSaveAsNote = async () => {
    if (!content || isSaving || saved) return
    const token = getStoredToken()
    if (!token) return

    setIsSaving(true)
    try {
      await createNoteFromQuestion(token, {
        title: "AI 回答笔记",
        content: content,
        source: "ai_answer",
      })
      setSaved(true)
      onSaveAsNote?.(content)
    } catch (error) {
      console.error("[笔记] 保存失败:", error)
    } finally {
      setIsSaving(false)
    }
  }

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
        <>
          <div className="markdown-body" style={{ fontSize: "inherit" }}>
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
          {/* Save as Note button */}
          {!isUser && (
            <button
              onClick={handleSaveAsNote}
              disabled={isSaving || saved}
              className="flex items-center gap-1 mt-2 px-2 py-1 text-xs rounded-lg transition-colors hover:bg-black/10 disabled:opacity-50"
              style={{ color: saved ? "hsl(var(--success))" : "hsl(var(--primary))" }}
              title="将AI回答保存为笔记"
            >
              <FileText className="w-3 h-3" />
              {saved ? "已保存" : isSaving ? "保存中..." : "记为笔记"}
            </button>
          )}
        </>
      )}
    </div>
  )
}

// ── Main KnowledgeOrb ─────────────────────────────────────
interface ChatMessage {
  role: "user" | "ai"
  content: string
}

interface ActiveKnowledgeQuestion {
  type: "knowledge"
  knowledgePoint: KnowledgePointCtx
}

export function KnowledgeOrb() {
  const router = useRouter()
  const { activeKnowledgeQuestion, isKnowledgePanelOpen, knowledgePanelSpawnPos, openKnowledgePanel, closeKnowledgePanel } = useAIContext()

  // Orb state
  const orbRef = useRef<HTMLDivElement>(null)
  const [isHovered, setIsHovered] = useState(false)
  const [isDraggingOrb, setIsDraggingOrb] = useState(false)
  const targetedKnowledgeRef = useRef<KnowledgePointCtx | null>(null)
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
  const prevPanelSpawnPosRef = useRef<typeof knowledgePanelSpawnPos>(null)

  // ── Orb: hide when panel open, show when panel closed ──
  const [orbVisible, setOrbVisible] = useState(true)
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
    if (isDraggingOrb) return
    e.preventDefault()
    e.stopPropagation()

    const orbEl = orbRef.current
    const orbRect = orbEl?.getBoundingClientRect()
    const spawnX = orbRect ? orbRect.left + ORB_SIZE / 2 : e.clientX
    const spawnY = orbRect ? orbRect.top + ORB_SIZE / 2 : e.clientY

    // Expand panel with no knowledge context (free questioning)
    const blankQuestion: ActiveKnowledgeQuestion = {
      type: "knowledge",
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
    openKnowledgePanel(blankQuestion, { x: spawnX, y: spawnY })
  }, [isDraggingOrb, openKnowledgePanel])

  // ── Orb: drag start ────────────────────────────────────
  const handleOrbPointerDown = useCallback((e: React.PointerEvent<HTMLDivElement>) => {
    if (e.button !== 0) return
    e.preventDefault()
    e.stopPropagation()

    const orbEl = orbRef.current
    if (!orbEl) return

    targetedKnowledgeRef.current = null
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

      const kp = hit?.closest("[data-knowledge-point]")

      if (prevHighlightRef.current && prevHighlightRef.current !== kp) {
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
        }
      } else {
        targetedKnowledgeRef.current = null
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
    if (kp && !panelOpenedRef.current) {
      panelOpenedRef.current = true

      const orbEl = orbRef.current
      const orbRect = orbEl?.getBoundingClientRect()
      const spawnX = orbRect ? orbRect.left + ORB_SIZE / 2 : e.clientX
      const spawnY = orbRect ? orbRect.top + ORB_SIZE / 2 : e.clientY

      setOrbVisible(false)

      const question: ActiveKnowledgeQuestion = {
        type: "knowledge",
        knowledgePoint: kp,
      }
      openKnowledgePanel(question, { x: spawnX, y: spawnY })
    } else {
      // Snap orb back to default position (bottom-right corner)
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
  }, [isDraggingOrb, openKnowledgePanel, stopHit])

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
    kp: KnowledgePointCtx,
    userMessage: string
  ) => {
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
    const hasKnowledgeContext = kp && kp.id !== ""

    const prompt = hasKnowledgeContext
      ? buildPrompt(kp, userMessage)
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
      setMessages(prev => [...prev, { role: "ai", content: fullText }])
    } catch (err) {
      setMessages(prev => [...prev, { role: "ai", content: `抱歉，AI 服务暂时不可用: ${err instanceof Error ? err.message : String(err)}` }])
    } finally {
      setIsStreaming(false)
      setStreamingText("")
    }
  }, [inputValue, isStreaming, activeKnowledgeQuestion, buildPrompt])

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
                  {activeKnowledgeQuestion?.knowledgePoint?.id ? "已关联当前知识点" : "随时提问"}
                </p>
              </div>
            </div>
            <button
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
            {activeKnowledgeQuestion?.knowledgePoint?.id ? (
              /* Has knowledge context */
              [
                { label: "详细解释", prompt: "请详细解释这个知识点的含义和应用场景" },
                { label: "示例讲解", prompt: "请结合示例代码详细讲解这个知识点的用法" },
                { label: "注意事项", prompt: "使用这个知识点有什么需要注意的地方？" },
                { label: "相关知识点", prompt: "有哪些相关的知识点需要一起学习？" },
              ].map(qp => (
                <button
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
                <button
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
            {/* Streaming bubble */}
            {isStreaming && (
              <div className="flex" style={{ justifyContent: "flex-start" }}>
                <div
                  className="rounded-2xl rounded-bl-sm px-3 py-2"
                  style={{ background: "hsl(var(--secondary))", maxWidth: "88%", fontSize: "0.75rem" }}
                >
                  {streamingText ? (
                    <div className="markdown-body" style={{ fontSize: "inherit" }}>
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
                placeholder="针对知识点继续提问..."
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
