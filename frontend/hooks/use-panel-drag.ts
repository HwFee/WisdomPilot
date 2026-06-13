"use client"

import { useCallback, useRef } from "react"
import type { KnowledgeOrbState, KnowledgeOrbAction } from "./use-knowledge-orb-state"

interface UsePanelDragArgs {
  state: KnowledgeOrbState
  dispatch: React.Dispatch<KnowledgeOrbAction>
}

export function usePanelDrag({ state, dispatch }: UsePanelDragArgs) {
  const panelRef = useRef<HTMLDivElement>(null)
  const dragOffsetRef = useRef({ x: 0, y: 0 })

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
    dispatch({ type: "START_PANEL_DRAG" })
    ;(e.currentTarget as HTMLDivElement).setPointerCapture(e.pointerId)
  }, [dispatch])

  const handlePanelDragMove = useCallback((e: React.PointerEvent<HTMLDivElement>) => {
    if (!state.isDraggingPanel) return
    dispatch({
      type: "SET_PANEL_POS",
      payload: { x: e.clientX - dragOffsetRef.current.x, y: e.clientY - dragOffsetRef.current.y },
    })
  }, [state.isDraggingPanel, dispatch])

  const handlePanelDragEnd = useCallback(() => {
    dispatch({ type: "STOP_PANEL_DRAG" })
  }, [dispatch])

  return {
    panelRef,
    handlePanelDragStart,
    handlePanelDragMove,
    handlePanelDragEnd,
  }
}
