'use client'

import { useState, type ReactNode } from 'react'
import { useRouter } from 'next/navigation'
import type { MainTask } from '@/lib/api/deck/types'
import { PanelTag } from '../deck/kit'

function difficultyStars(level: number): string {
  return '★'.repeat(level) + '☆'.repeat(Math.max(0, 5 - level))
}

/** 标题高亮：把 highlight 片段包成 signal 色 em */
function renderTitle(title: string, highlight: string | null): ReactNode {
  if (!highlight || !title.includes(highlight)) return title
  const [before, after] = title.split(highlight, 2)
  return (
    <>
      {before}
      <em className="not-italic text-signal">{highlight}</em>
      {after}
    </>
  )
}

/** 今日主任务 HERO：自适应分发，「换一个任务」在 alternates 中轮换 */
export function MissionHero({ task }: { task: MainTask }) {
  const { push } = useRouter()
  // 轮换序列：主任务 + 备选；索引推进即换任务
  const [rotation] = useState<MainTask[]>(() => [task, ...task.alternates])
  const [index, setIndex] = useState(0)
  const current = rotation[index % rotation.length]

  return (
    <section className="deck-panel deck-boot deck-boot-1 relative grid grid-cols-1 items-center gap-8 p-[34px_38px] lg:grid-cols-[1fr_auto]">
      <div className="deck-scanline" />
      <div>
        <PanelTag label="TODAY'S MISSION · 今日主任务" variant="on" />
        <div className="mt-2.5 font-mono text-[11px] tracking-wide text-faint">
          {current.id} · {current.module_label} · {current.stage_label}
        </div>
        <h1 className="mt-2 text-[26px] font-semibold leading-snug">
          {renderTitle(current.title, current.highlight)}
        </h1>
        <p className="mt-2.5 max-w-[520px] text-[13px] text-dim">{current.desc}</p>
        <div className="mt-4 flex flex-wrap gap-5 font-mono text-[11px] text-dim">
          <span>
            预计 <b className="font-medium text-text">{current.eta_minutes} 分钟</b>
          </span>
          <span>
            难度 <b className="font-medium text-text">{difficultyStars(current.difficulty)}</b>
          </span>
          {current.related_weakness && (
            <span>
              关联弱点 <b className="font-medium text-text">{current.related_weakness}</b>
            </span>
          )}
        </div>
      </div>
      <div className="flex flex-col items-start gap-3 lg:items-end">
        <button className="deck-btn-primary" onClick={() => push(current.target_url)}>
          {current.cta_label}
        </button>
        {rotation.length > 1 && (
          <button className="deck-btn-ghost" onClick={() => setIndex((i) => i + 1)}>
            换一个任务
          </button>
        )}
      </div>
    </section>
  )
}

/** 未定级引导：完成定级测试后才生成专属任务 */
export function PlacementHero() {
  const { push } = useRouter()
  return (
    <section className="deck-panel deck-boot deck-boot-1 relative grid grid-cols-1 items-center gap-8 p-[34px_38px] lg:grid-cols-[1fr_auto]">
      <div className="deck-scanline" />
      <div>
        <PanelTag label="PLACEMENT · 定级测试" variant="warn" />
        <h1 className="mt-2 text-[26px] font-semibold leading-snug">
          先花 <em className="not-italic text-signal">5 分钟</em>，让系统认识你。
        </h1>
        <p className="mt-2.5 max-w-[520px] text-[13px] text-dim">
          读两段代码找 bug + 手写一个小函数，定出审阅 / 调试 / 实现三根能力轴的初始等级。之后每天的主任务都按你的能力图谱分发。
        </p>
      </div>
      <div className="flex flex-col items-start gap-3 lg:items-end">
        <button className="deck-btn-primary" onClick={() => push('/certification?placement=1')}>
          开始定级 →
        </button>
      </div>
    </section>
  )
}
