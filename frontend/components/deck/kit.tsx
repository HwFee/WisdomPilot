'use client'

import { useEffect, useRef, useState, type ReactNode, type CSSProperties } from 'react'

/* ============================================
   训练舱共享组件（Deck Kit）
   ============================================ */

/** 面板标记：mono 大写小标签 + 方块 */
export function PanelTag({
  label,
  variant = 'default',
}: {
  label: string
  variant?: 'default' | 'on' | 'warn'
}) {
  const cls = variant === 'on' ? 'deck-tag deck-tag-on' : variant === 'warn' ? 'deck-tag deck-tag-warn' : 'deck-tag'
  return <span className={cls}>{label}</span>
}

/** 区块标题：mono 大写 + 发丝分隔线 + 右侧备注 */
export function SectionHead({
  title,
  note,
}: {
  title: string
  note?: ReactNode
}) {
  return (
    <div className="mt-10 mb-4 flex items-center gap-3.5">
      <h2 className="font-mono text-xs font-medium tracking-[2px] uppercase text-dim shrink-0">
        {title}
      </h2>
      <div className="flex-1 h-px bg-line" />
      {note ? <span className="font-mono text-[11px] text-faint shrink-0">{note}</span> : null}
    </div>
  )
}

/** kbd 提示 */
export function Kbd({ children }: { children: ReactNode }) {
  return <kbd className="deck-kbd">{children}</kbd>
}

/** 能力分段格：10 格，filled 格点亮 */
export function Segments({ filled }: { filled: number }) {
  const count = Math.max(0, Math.min(10, Math.round(filled)))
  return (
    <div className="deck-segments">
      {Array.from({ length: 10 }, (_, i) =>
        i < count ? (
          <i key={i} className="deck-seg-fill" style={{ '--i': i } as CSSProperties} />
        ) : (
          <i key={i} />
        )
      )}
    </div>
  )
}

/** 数字滚动计数（easeOutCubic，尊重减动效） */
export function CountUp({
  value,
  duration = 900,
  delay = 550,
}: {
  value: number
  duration?: number
  delay?: number
}) {
  const [display, setDisplay] = useState(0)
  const rafRef = useRef<number>(0)

  useEffect(() => {
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (reduceMotion) {
      setDisplay(value)
      return
    }
    let start: number | null = null
    const timer = setTimeout(() => {
      const frame = (ts: number) => {
        if (start === null) start = ts
        const p = Math.min((ts - start) / duration, 1)
        const eased = 1 - Math.pow(1 - p, 3)
        setDisplay(Math.round(value * eased))
        if (p < 1) rafRef.current = requestAnimationFrame(frame)
      }
      rafRef.current = requestAnimationFrame(frame)
    }, delay)
    return () => {
      clearTimeout(timer)
      cancelAnimationFrame(rafRef.current)
    }
  }, [value, duration, delay])

  return <>{display.toLocaleString('en-US')}</>
}

/** 状态栏：系统状态 + 实时时钟 + 闪烁光标 */
export function StatusBar() {
  const [now, setNow] = useState('')

  useEffect(() => {
    const pad = (n: number) => String(n).padStart(2, '0')
    const tick = () => {
      const d = new Date()
      setNow(
        `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ` +
          `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
      )
    }
    tick()
    const timer = setInterval(tick, 1000)
    return () => clearInterval(timer)
  }, [])

  return (
    <footer className="mt-11 pt-2.5 border-t border-line flex items-center gap-6 font-mono text-[11px] text-faint">
      <span className="text-signal">● SYSTEM ONLINE</span>
      <span className="hidden sm:inline">HLR ENGINE: ACTIVE</span>
      <span className="hidden sm:inline">JUDGE: CONNECTED</span>
      <span>{now || '--'}</span>
      <span className="deck-cursor" />
    </footer>
  )
}
