'use client'

/* 徽章解锁仪式：提交响应含非空 new_badges 时全屏播放
   规格：docs/superpowers/specs/2026-07-27-badge-system-design.md §6.3
   红线：遮罩无 blur、无渐变；粒子为 tier 色 2px 像素方块（CSS 手写，无新依赖）；
   prefers-reduced-motion 下静态呈现、零动画 */

import {
  useCallback,
  useEffect,
  useState,
  type CSSProperties,
  type ReactNode,
} from 'react'
import type { BadgeUnlock } from '@/lib/api/deck/types'
import { BadgeIcon } from './BadgeIcon'
import { HIDDEN_BADGE_IDS, TIER_COLOR, TIER_LABEL } from './badge-meta'
import { CountUp } from './kit'

const CELEBRATION_DURATION_MS = 2200      // 单枚总时长
const DECODE_DELAY_MS = 400               // 隐藏徽章 ??? → 真名解码延迟
const PARTICLE_COUNT = 10                 // 8–12 个像素粒子
const BADGE_SIZE = 112

/** 确定性粒子落点：绕徽章一圈散开，距离分三档（渲染期稳定，不用随机数） */
function particleOffset(index: number): { dx: number; dy: number } {
  const angle = (index / PARTICLE_COUNT) * Math.PI * 2 + 0.4
  const radius = 64 + (index % 3) * 16
  return { dx: Math.round(Math.cos(angle) * radius), dy: Math.round(Math.sin(angle) * radius) }
}

function CelebrationOverlay({
  badge,
  total,
  onDone,
}: {
  badge: BadgeUnlock
  total: number
  onDone: () => void
}) {
  const hidden = HIDDEN_BADGE_IDS.has(badge.id)
  const [reducedMotion, setReducedMotion] = useState(false)
  const [decoded, setDecoded] = useState(false)

  useEffect(() => {
    setReducedMotion(window.matchMedia('(prefers-reduced-motion: reduce)').matches)
  }, [])

  // 单枚 ~2.2s 后自动播放下一枚；点击任意处立即跳过
  useEffect(() => {
    const timer = setTimeout(onDone, CELEBRATION_DURATION_MS)
    return () => clearTimeout(timer)
  }, [onDone])

  // 隐藏徽章：先 ??? 轮廓，~400ms 后解码翻出真名（reduced-motion 直接显示真名）
  useEffect(() => {
    if (!hidden || reducedMotion) return
    const timer = setTimeout(() => setDecoded(true), DECODE_DELAY_MS)
    return () => clearTimeout(timer)
  }, [hidden, reducedMotion])

  const title = hidden && !decoded && !reducedMotion ? '???' : badge.title

  return (
    <div
      className="fixed inset-0 z-[200] flex items-center justify-center bg-topbar"
      onClick={onDone}
      role="dialog"
      aria-label={`解锁徽章 ${badge.title}`}
    >
      <div
        className="flex flex-col items-center px-6 text-center"
        style={{ '--badge-color': TIER_COLOR[badge.tier] } as CSSProperties}
      >
        <div className="relative">
          <div className={reducedMotion ? undefined : 'badge-pop badge-pulse-once'}>
            <BadgeIcon id={badge.id} tier={badge.tier} size={BADGE_SIZE} draw={!reducedMotion} />
          </div>
          {!reducedMotion &&
            Array.from({ length: PARTICLE_COUNT }, (_, i) => {
              const { dx, dy } = particleOffset(i)
              return (
                <i
                  key={i}
                  className="badge-particle"
                  style={{ '--dx': `${dx}px`, '--dy': `${dy}px` } as CSSProperties}
                />
              )
            })}
        </div>

        <div className="deck-boot deck-boot-1 mt-7 font-mono text-[11px] tracking-[3px] text-faint">
          BADGE UNLOCKED
        </div>
        <div className="deck-boot deck-boot-2 mt-2 text-2xl font-semibold text-text">{title}</div>
        <div className="deck-boot deck-boot-2 mt-1.5 font-mono text-[11px] tracking-[1.5px] text-dim">
          {TIER_LABEL[badge.tier]}
        </div>
        <div className="deck-boot deck-boot-3 mt-3 font-mono text-lg font-medium text-signal">
          +<CountUp value={badge.reward_cores} delay={800} /> 智核
        </div>

        <div className="mt-6 font-mono text-[10px] text-faint">
          {total > 1 ? `还有 ${total - 1} 枚 · ` : ''}点击任意处跳过
        </div>
      </div>
    </div>
  )
}

/** 四模块 Client 共用：把 submit 响应的 new_badges 喂进来，多枚自动排队播放 */
export function useBadgeCelebration(): {
  celebrate: (badges: BadgeUnlock[] | undefined) => void
  celebrationElement: ReactNode
} {
  const [queue, setQueue] = useState<BadgeUnlock[]>([])

  const celebrate = useCallback((badges: BadgeUnlock[] | undefined) => {
    if (badges && badges.length > 0) setQueue((prev) => [...prev, ...badges])
  }, [])

  const advance = useCallback(() => setQueue((prev) => prev.slice(1)), [])

  const celebrationElement =
    queue.length > 0 ? (
      <CelebrationOverlay
        key={queue[0].id}
        badge={queue[0]}
        total={queue.length}
        onDone={advance}
      />
    ) : null

  return { celebrate, celebrationElement }
}
