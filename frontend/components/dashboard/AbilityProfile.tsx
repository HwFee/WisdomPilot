'use client'

import type { AbilityAxis, AxisKey } from '@/lib/api/deck/types'
import { CountUp, SectionHead, Segments } from '../deck/kit'

const AXIS_EN: Record<AxisKey, string> = {
  review: 'Review',
  debug: 'Debug',
  implement: 'Implement',
}

function AxisCard({ axis }: { axis: AbilityAxis }) {
  const filled = Math.round((axis.xp_current / axis.xp_next) * 10)
  return (
    <div className="deck-panel deck-panel-hoverable p-[20px_22px]">
      <div className="flex items-baseline justify-between">
        <span className="text-[15px] font-semibold">
          {axis.label}
          <span className="ml-2 font-mono text-[10px] uppercase tracking-[1.5px] text-faint">
            {AXIS_EN[axis.key]}
          </span>
        </span>
        <span className="font-mono text-xs text-signal">LV.{axis.level}</span>
      </div>
      <div className="mt-3.5">
        <Segments filled={filled} />
      </div>
      <div className="mt-2.5 font-mono text-[11px] text-dim">
        <CountUp value={axis.xp_current} /> / {axis.xp_next.toLocaleString('en-US')} 至 LV.{axis.level + 1}
      </div>
      {axis.weakest_focus && (
        <div className="mt-1 text-xs text-dim">
          短板：<b className="font-medium text-amber">{axis.weakest_focus}</b>
        </div>
      )}
    </div>
  )
}

/** 能力图谱：三根能力轴（审阅 / 调试 / 实现），HLR 掌握度驱动 */
export function AbilityProfile({ axes }: { axes: AbilityAxis[] }) {
  return (
    <>
      <div className="deck-boot deck-boot-2">
        <SectionHead title="能力图谱 / Ability Profile" note="由 HLR 掌握度驱动 · 实时" />
      </div>
      <section className="deck-boot deck-boot-2 grid grid-cols-1 gap-4 lg:grid-cols-3">
        {axes.map((axis) => (
          <AxisCard key={axis.key} axis={axis} />
        ))}
      </section>
    </>
  )
}
