'use client'

import Link from 'next/link'
import type { CSSProperties } from 'react'
import type { FeedItem, RhythmDay, WeakPoint } from '@/lib/api/deck/types'
import { PanelTag, SectionHead } from '../deck/kit'

/* ── 待攻克弱点 ── */

function WeakPointsPanel({ points }: { points: WeakPoint[] }) {
  return (
    <div className="deck-panel p-[18px_20px]">
      <PanelTag label="WEAK POINTS · 待攻克弱点" variant="warn" />
      <div className="mt-3">
        {points.map((p) => (
          <div
            key={p.name}
            className="group flex items-center justify-between border-t border-line py-[9px] first:border-t-0"
          >
            <span className="text-[13px] text-text">
              {p.name}
              <small className="block text-[11px] text-faint">{p.category}</small>
              {p.source && (
                <small className="mt-0.5 block font-mono text-[10px] text-dim">{p.source}</small>
              )}
            </span>
            <span className="ml-auto font-mono text-xs text-amber">
              掌握 {Math.round(p.p_l * 100)}%
            </span>
            <Link
              href={`/tutor?topic=${encodeURIComponent(p.name)}`}
              className="ml-3 translate-x-1 rounded-[3px] border border-line px-2.5 py-1 font-mono text-[11px] text-dim opacity-35 transition-all duration-200 hover:border-signal hover:text-signal group-hover:translate-x-0 group-hover:opacity-100"
            >
              针对训练
            </Link>
          </div>
        ))}
      </div>
    </div>
  )
}

/* ── 本周节奏 ── */

function RhythmPanel({
  days,
  streakDays,
  reviewDue,
}: {
  days: RhythmDay[]
  streakDays: number
  reviewDue: { total: number; due_today: number }
}) {
  const max = Math.max(...days.map((d) => d.minutes), 1)
  return (
    <div className="deck-panel p-[18px_20px]">
      <PanelTag label="RHYTHM · 本周节奏" />
      <div className="mt-1 grid h-14 grid-cols-7 items-end gap-1.5 px-0 pb-0.5 pt-1.5">
        {days.map((d, i) => (
          <div
            key={d.label}
            title={`${d.is_today ? '今天' : `周${d.label}`} · ${d.minutes} 分钟`}
            style={{ '--i': i, height: `${Math.max(8, (d.minutes / max) * 100)}%` } as CSSProperties}
            className={d.is_today ? 'deck-rhythm-bar deck-rhythm-bar-today' : 'deck-rhythm-bar'}
          />
        ))}
      </div>
      <div className="mb-2.5 grid grid-cols-7 gap-1.5 text-center font-mono text-[9px] text-faint">
        {days.map((d) => (
          <span key={d.label} className={d.is_today ? 'text-signal' : undefined}>
            {d.label}
          </span>
        ))}
      </div>
      <div className="flex justify-between border-t border-line py-2 text-[13px]">
        <span className="text-dim">连续训练</span>
        <span className="font-mono text-text">
          <em className="not-italic text-signal">{streakDays}</em> 天
        </span>
      </div>
      <Link
        href="/review"
        title="去复盘队列清掉它们"
        className="group -mx-1.5 flex justify-between rounded-[3px] border-t border-line px-1.5 py-2 text-[13px] transition-colors hover:bg-panel-raised"
      >
        <span className="text-dim">复盘待清</span>
        <span className="font-mono text-text">
          {reviewDue.total} 道
          <span className="ml-1.5 text-[11px] text-amber">{reviewDue.due_today} 道今日到期</span>{' '}
          <span className="text-faint transition-all duration-200 group-hover:translate-x-[3px] group-hover:text-signal">
            →
          </span>
        </span>
      </Link>
    </div>
  )
}

/* ── 最近动态 ── */

function FeedPanel({ feed }: { feed: FeedItem[] }) {
  return (
    <div className="deck-panel p-[18px_20px]">
      <PanelTag label="FEED · 最近动态" />
      <div className="mt-3">
        {feed.map((item, i) => (
          <div
            key={i}
            className="-mx-1.5 flex cursor-pointer gap-3 rounded-[3px] border-t border-line px-1.5 py-2 text-xs transition-colors first:border-t-0 hover:bg-panel-raised"
          >
            <span className="shrink-0 font-mono text-faint">{item.time}</span>
            <span className="text-dim">
              {item.segments.map((seg, j) => (
                <span
                  key={j}
                  className={
                    seg.tone === 'strong'
                      ? 'font-medium text-text'
                      : seg.tone === 'ok'
                        ? 'text-signal'
                        : seg.tone === 'bad'
                          ? 'text-deck-red'
                          : undefined
                  }
                >
                  {seg.t}
                </span>
              ))}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

/** 情报区：弱点 / 节奏 / 动态 三栏 */
export function IntelPanels({
  weakPoints,
  rhythmDays,
  streakDays,
  reviewDue,
  feed,
}: {
  weakPoints: WeakPoint[]
  rhythmDays: RhythmDay[]
  streakDays: number
  reviewDue: { total: number; due_today: number }
  feed: FeedItem[]
}) {
  return (
    <>
      <div className="deck-boot deck-boot-4">
        <SectionHead title="情报 / Intel" />
      </div>
      <section className="deck-boot deck-boot-4 grid grid-cols-1 gap-4 lg:grid-cols-[5fr_3fr_4fr]">
        <WeakPointsPanel points={weakPoints} />
        <RhythmPanel days={rhythmDays} streakDays={streakDays} reviewDue={reviewDue} />
        <FeedPanel feed={feed} />
      </section>
    </>
  )
}
