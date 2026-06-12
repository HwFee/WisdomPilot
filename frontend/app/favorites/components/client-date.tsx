'use client'

export function ClientDate({ dateStr }: { dateStr: string }) {
  const formatted = new Date(dateStr).toLocaleDateString('zh-CN')
  return <span suppressHydrationWarning>{formatted}</span>
}
