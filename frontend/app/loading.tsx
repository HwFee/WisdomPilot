import { DeckShell } from '@/components/deck/DeckShell'

/** 全局路由级加载兜底：导航切换时展示 deck 风格骨架，避免白屏 */
export default function Loading() {
  return (
    <DeckShell>
      <div className="deck-panel p-8 font-mono text-sm text-dim">
        载入中<span className="deck-cursor ml-2" />
      </div>
    </DeckShell>
  )
}
