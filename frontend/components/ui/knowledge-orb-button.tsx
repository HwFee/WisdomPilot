"use client"

import React from "react"

const ORB_SIZE = 52

interface KnowledgeOrbButtonProps {
  orbRef: React.RefObject<HTMLButtonElement | null>
  isHovered: boolean
  isDraggingOrb: boolean
  orbVisible: boolean
  onPointerDown: (e: React.PointerEvent<HTMLButtonElement>) => void
  onPointerMove: (e: React.PointerEvent<HTMLButtonElement>) => void
  onPointerUp: (e: React.PointerEvent<HTMLButtonElement>) => void
  onClick: (e: React.MouseEvent<HTMLButtonElement>) => void
  onHoverChange: (hovered: boolean) => void
}

export function KnowledgeOrbButton({
  orbRef,
  isHovered,
  isDraggingOrb,
  orbVisible,
  onPointerDown,
  onPointerMove,
  onPointerUp,
  onClick,
  onHoverChange,
}: KnowledgeOrbButtonProps) {
  if (!orbVisible) return null

  return (
    <button
      type="button"
      ref={orbRef}
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={onPointerUp}
      onPointerCancel={onPointerUp}
      onClick={onClick}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onClick(e as unknown as React.MouseEvent<HTMLButtonElement>) } }}
      onMouseEnter={() => onHoverChange(true)}
      onMouseLeave={() => !isDraggingOrb && onHoverChange(false)}
      aria-label="AI 助手"
      className={`
        fixed right-6 bottom-6 select-none z-[9999] animate-orb-bob
        flex items-center justify-center touch-none pointer-events-auto
        border-none p-0 transition-all duration-200
        bg-primary text-primary-foreground shadow-lg hover:shadow-xl hover:bg-primary/90
        ${isDraggingOrb ? 'transition-none' : ''}
      `}
      style={{
        width: ORB_SIZE,
        height: ORB_SIZE,
        borderRadius: ORB_SIZE / 2,
        cursor: isDraggingOrb ? "grabbing" : "grab",
      }}
    >
      <span className="text-sm font-bold tracking-wide select-none">
        AI
      </span>
    </button>
  )
}
