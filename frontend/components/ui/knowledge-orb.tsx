"use client"

import React, { useEffect } from "react"
import { createPortal } from "react-dom"
import { useRouter } from "next/navigation"
import { useAIContext } from "@/contexts/AIContext"
import { useKnowledgeOrbState } from "@/hooks/use-knowledge-orb-state"
import { useOrbDrag } from "@/hooks/use-orb-drag"
import { usePanelDrag } from "@/hooks/use-panel-drag"
import { useKnowledgeOrbChat } from "@/hooks/use-knowledge-orb-chat"
import { KnowledgeOrbButton } from "./knowledge-orb-button"
import { KnowledgeOrbPanel } from "./knowledge-orb-panel"
import { KnowledgeOrbToast } from "./knowledge-orb-toast"

// ── Dimensions ─────────────────────────────────────────────
const PANEL_W = 453
const PANEL_H = 560

// ── Main KnowledgeOrb ─────────────────────────────────────
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
  knowledgePoints,
}: KnowledgeOrbProps) {
  const { push } = useRouter()
  const {
    activeKnowledgeQuestion,
    isKnowledgePanelOpen,
    knowledgePanelSpawnPos,
    openKnowledgePanel,
    closeKnowledgePanel,
  } = useAIContext()

  const [state, dispatch] = useKnowledgeOrbState()

  const {
    orbRef,
    handleOrbClick,
    handleOrbPointerDown,
    handleOrbPointerMove,
    handleOrbPointerUp,
  } = useOrbDrag({
    state,
    dispatch,
    disabledForQuestion,
    openKnowledgePanel,
  })

  const { panelRef, handlePanelDragStart, handlePanelDragMove, handlePanelDragEnd } = usePanelDrag({
    state,
    dispatch,
  })

  const { sendMessage, handleQuickPrompt, handleKeyDown, handleClose } = useKnowledgeOrbChat({
    state,
    dispatch,
    activeKnowledgeQuestion,
    push,
    closeKnowledgePanel,
  })

  // ── Orb: hide when panel open, show when panel closed ──
  useEffect(() => {
    if (isKnowledgePanelOpen) {
      dispatch({ type: "HIDE_ORB" })
    } else {
      dispatch({ type: "SHOW_ORB" })
    }
  }, [isKnowledgePanelOpen, dispatch])

  // ── Panel: set position from spawnPos ──────────────────
  const prevSpawnPosRef = React.useRef<typeof knowledgePanelSpawnPos>(null)
  useEffect(() => {
    if (!knowledgePanelSpawnPos) return
    if (prevSpawnPosRef.current === knowledgePanelSpawnPos) return
    prevSpawnPosRef.current = knowledgePanelSpawnPos
    const vw = window.innerWidth
    const vh = window.innerHeight
    const x = Math.min(Math.max(knowledgePanelSpawnPos.x - PANEL_W / 2, 24), vw - PANEL_W - 24)
    const y = Math.min(Math.max(knowledgePanelSpawnPos.y - 60, 24), vh - PANEL_H - 24)
    dispatch({ type: "SET_PANEL_POS", payload: { x, y } })
  }, [knowledgePanelSpawnPos, isKnowledgePanelOpen, activeKnowledgeQuestion, dispatch])

  // ── Render ─────────────────────────────────────────────
  return (
    <>
      <KnowledgeOrbToast visible={state.showDisabledToast} />

      {state.orbVisible && createPortal(
        <KnowledgeOrbButton
          orbRef={orbRef}
          isHovered={state.isHovered}
          isDraggingOrb={state.isDraggingOrb}
          orbVisible={state.orbVisible}
          onPointerDown={handleOrbPointerDown}
          onPointerMove={handleOrbPointerMove}
          onPointerUp={handleOrbPointerUp}
          onClick={handleOrbClick}
          onHoverChange={(hovered) => dispatch({ type: "SET_HOVERED", payload: hovered })}
        />,
        document.body
      )}

      {isKnowledgePanelOpen && createPortal(
        <KnowledgeOrbPanel
          panelRef={panelRef}
          pos={state.pos}
          isDraggingPanel={state.isDraggingPanel}
          activeKnowledgeQuestion={activeKnowledgeQuestion}
          contextMode={state.contextMode}
          messages={state.messages}
          isStreaming={state.isStreaming}
          streamingText={state.streamingText}
          inputValue={state.inputValue}
          onInputChange={(value) => dispatch({ type: "SET_INPUT_VALUE", payload: value })}
          onSend={sendMessage}
          onKeyDown={handleKeyDown}
          onQuickPrompt={handleQuickPrompt}
          onClose={handleClose}
          onDragStart={handlePanelDragStart}
          onDragMove={handlePanelDragMove}
          onDragEnd={handlePanelDragEnd}
          courseId={courseId}
          chapterId={chapterId}
          sectionId={sectionId}
          exerciseId={exerciseId}
          knowledgePoints={knowledgePoints}
        />,
        document.body
      )}
    </>
  )
}
