"use client"

import { createPortal } from "react-dom"
import { AlertCircle } from "lucide-react"

interface KnowledgeOrbToastProps {
  visible: boolean
}

export function KnowledgeOrbToast({ visible }: KnowledgeOrbToastProps) {
  if (!visible) return null

  return createPortal(
    <div
      className="fixed z-[10000] pointer-events-none"
      style={{
        bottom: '180px',
        left: '50%',
        transform: 'translateX(-50%)',
      }}
    >
      <div className="bg-amber-100 dark:bg-amber-900/80 text-amber-700 dark:text-amber-200 px-4 py-2 rounded-lg shadow-md text-sm font-medium flex items-center gap-2 animate-fade-in border border-amber-500/30">
        <AlertCircle className="size-3.5" strokeWidth={1.5} />
        先试试自己的智慧吧！
      </div>
    </div>,
    document.body
  )
}
