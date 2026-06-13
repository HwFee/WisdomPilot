"use client"

import { BookOpen } from "lucide-react"

interface PanelOrbProps {
  size?: number
}

export function PanelOrb({ size = 22 }: PanelOrbProps) {
  return (
    <div
      className="rounded-full flex items-center justify-center shrink-0 bg-primary text-primary-foreground"
      style={{
        width: size,
        height: size,
      }}
    >
      <BookOpen className="size-[60%]" strokeWidth={1.5} />
    </div>
  )
}
