'use client'

/* ============================================
   训练舱共享错误面板（Deck Error Panel）
   各 Client 组件 API 失败时复用；app/error.tsx 全局兜底同样使用。
   ============================================ */

export function ErrorPanel({
  message = '请求失败，请稍后重试',
  onRetry,
}: {
  message?: string
  onRetry?: () => void
}) {
  return (
    <div className="deck-panel p-[18px_20px]">
      <div className="flex flex-wrap items-center gap-4">
        <span className="font-mono text-xs text-deck-red">● 连接异常</span>
        <p className="font-mono text-xs text-dim">{message}</p>
        {onRetry && (
          <button className="deck-btn-ghost ml-auto" onClick={onRetry}>
            重试
          </button>
        )}
      </div>
    </div>
  )
}
