'use client'

import { useEffect } from 'react'
import { DeckShell } from '@/components/deck/DeckShell'
import { ErrorPanel } from '@/components/deck/ErrorPanel'

/** 全局路由级错误边界：页面渲染/请求抛错时兜底，避免整页白屏 */
export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error(error)
  }, [error])

  return (
    <DeckShell>
      <div className="deck-boot deck-boot-1 mt-10">
        <ErrorPanel message={error.message || '页面加载失败，请重试'} onRetry={reset} />
      </div>
    </DeckShell>
  )
}
