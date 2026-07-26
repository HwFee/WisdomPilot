'use client'

import type { ReactNode } from 'react'
import { DeckHeader } from './DeckHeader'

/** 训练舱页面外壳：全局头部 + 网格底 + 内容容器 */
export function DeckShell({ children }: { children: ReactNode }) {
  return (
    <div className="deck-grid-bg min-h-screen">
      <DeckHeader />
      <main className="mx-auto max-w-[1120px] px-7 pb-16 pt-9">{children}</main>
    </div>
  )
}
