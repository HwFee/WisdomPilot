"use client"

import { useCallback, useRef, useEffect } from "react"
import type { KnowledgePointContext } from "@/contexts/AIContext"
import type { ActiveKnowledgeQuestion } from "@/contexts/AIContext"
import { parseKnowledgePoint, parseQuestion, type QuestionCtx } from "@/lib/knowledge-orb"
import type { KnowledgeOrbState, KnowledgeOrbAction } from "./use-knowledge-orb-state"

const ORB_SIZE = 52
const HIT_INTERVAL_MS = 80

interface UseOrbDragArgs {
  state: KnowledgeOrbState
  dispatch: React.Dispatch<KnowledgeOrbAction>
  disabledForQuestion: boolean
  openKnowledgePanel: (question: ActiveKnowledgeQuestion, spawnPos?: { x: number; y: number }) => void
}

interface OrbSpawn {
  spawnX: number
  spawnY: number
}

function computeSpawn(orbEl: HTMLButtonElement | null, fallbackClient: { clientX: number; clientY: number }): OrbSpawn {
  const rect = orbEl?.getBoundingClientRect()
  return {
    spawnX: rect ? rect.left + ORB_SIZE / 2 : fallbackClient.clientX,
    spawnY: rect ? rect.top + ORB_SIZE / 2 : fallbackClient.clientY,
  }
}

function snapOrbToDefault(orbEl: HTMLButtonElement | null) {
  if (!orbEl) return
  Object.assign(orbEl.style, {
    position: "fixed",
    left: "",
    top: "",
    right: "24px",
    bottom: "24px",
  })
}

export function useOrbDrag({ state, dispatch, disabledForQuestion, openKnowledgePanel }: UseOrbDragArgs) {
  const orbRef = useRef<HTMLButtonElement>(null)
  const targetedKnowledgeRef = useRef<KnowledgePointContext | null>(null)
  const targetedQuestionRef = useRef<QuestionCtx | null>(null)
  const panelOpenedRef = useRef(false)
  const prevHighlightRef = useRef<Element | null>(null)
  const hitIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

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

  // Clear outline on unmount
  useEffect(() => {
    const highlightRef = prevHighlightRef
    return () => {
      stopHit()
      if (highlightRef.current) {
        (highlightRef.current as HTMLElement).style.outline = ""
      }
    }
  }, [stopHit])

  const handleOrbClick = useCallback((e: React.MouseEvent) => {
    // If we just finished a drag operation, don't open panel
    if (panelOpenedRef.current) return
    e.preventDefault()
    e.stopPropagation()

    const { spawnX, spawnY } = computeSpawn(orbRef.current, e)

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
    dispatch({ type: "SET_CONTEXT_MODE", payload: null })
    openKnowledgePanel(blankQuestion, { x: spawnX, y: spawnY })
  }, [openKnowledgePanel, dispatch])

  const handleOrbPointerDown = useCallback((e: React.PointerEvent<HTMLButtonElement>) => {
    if (e.button !== 0) return
    e.preventDefault()
    e.stopPropagation()

    const orbEl = orbRef.current
    if (!orbEl) return

    targetedKnowledgeRef.current = null
    targetedQuestionRef.current = null
    panelOpenedRef.current = false
    dispatch({ type: "START_ORB_DRAG" })

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
          Object.assign(el.style, {
            outline: '3px solid rgba(16, 185, 129, 0.9)',
            outlineOffset: '4px',
          })
          prevHighlightRef.current = kp
          targetedKnowledgeRef.current = ctx
          targetedQuestionRef.current = null
        }
      } else if (q) {
        const ctx = parseQuestion(q)
        if (ctx) {
          const el = q as HTMLElement
          Object.assign(el.style, {
            outline: '3px solid rgba(14, 165, 233, 0.9)',
            outlineOffset: '4px',
          })
          prevHighlightRef.current = q
          targetedQuestionRef.current = ctx
          targetedKnowledgeRef.current = null
        }
      } else {
        targetedKnowledgeRef.current = null
        targetedQuestionRef.current = null
      }
    }, HIT_INTERVAL_MS)

    ;(e.currentTarget as HTMLButtonElement).setPointerCapture(e.pointerId)
  }, [dispatch])

  const handleOrbPointerMove = useCallback((e: React.PointerEvent<HTMLButtonElement>) => {
    if (!state.isDraggingOrb) return
    const orbEl = orbRef.current
    if (!orbEl) return
    Object.assign(orbEl.style, {
      position: "fixed",
      left: `${e.clientX - ORB_SIZE / 2}px`,
      top: `${e.clientY - ORB_SIZE / 2}px`,
      right: "auto",
      bottom: "auto",
      touchAction: "none",
    })
  }, [state.isDraggingOrb])

  const handleOrbPointerUp = useCallback((e: React.PointerEvent<HTMLButtonElement>) => {
    if (!state.isDraggingOrb) return
    e.preventDefault()
    stopHit()
    dispatch({ type: "STOP_ORB_DRAG" })

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

      const { spawnX, spawnY } = computeSpawn(orbRef.current, e)

      dispatch({ type: "HIDE_ORB" })
      dispatch({ type: "SET_CONTEXT_MODE", payload: "knowledge" })

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
        dispatch({ type: "SHOW_DISABLED_TOAST" })
        setTimeout(() => dispatch({ type: "HIDE_DISABLED_TOAST" }), 2000)
        // Snap orb back to default position
        snapOrbToDefault(orbRef.current)
      } else {
        panelOpenedRef.current = true

        const { spawnX, spawnY } = computeSpawn(orbRef.current, e)

        dispatch({ type: "HIDE_ORB" })
        dispatch({ type: "SET_CONTEXT_MODE", payload: "question" })

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
      snapOrbToDefault(orbRef.current)
    }

    targetedKnowledgeRef.current = null
    targetedQuestionRef.current = null
  }, [state.isDraggingOrb, openKnowledgePanel, stopHit, disabledForQuestion, dispatch])

  return {
    orbRef,
    handleOrbClick,
    handleOrbPointerDown,
    handleOrbPointerMove,
    handleOrbPointerUp,
  }
}
