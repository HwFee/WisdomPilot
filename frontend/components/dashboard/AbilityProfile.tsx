'use client'

import { FingerprintPattern } from 'lucide-react'
import type { AbilityAxis, AxisKey } from '@/lib/api/deck/types'
import {
  dashboardFingerprint,
  orderFingerprintAxes,
} from '@/lib/api/deck/mock/dashboard'
import { CountUp, SectionHead, Segments } from '../deck/kit'

export const AXIS_EN: Record<AxisKey, string> = {
  review: 'Review',
  debug: 'Debug',
  implement: 'Implement',
}

/** 单轴卡：LV + 分段格 + XP + 短板 */
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

/** 能力图谱：三张独立轴卡 + 指纹码，HLR 掌握度驱动 */
export function AbilityProfile({
  axes,
  hasPlacement,
}: {
  axes: AbilityAxis[]
  hasPlacement: boolean
}) {
  const fingerprint = hasPlacement
    ? dashboardFingerprint(orderFingerprintAxes(axes))
    : null

  return (
    <>
      <div className="deck-boot deck-boot-2">
        <SectionHead
          title="能力图谱 / Ability Profile"
          note={
            fingerprint ? (
              <span className="flex items-center gap-3">
                <span
                  className="flex items-center gap-1.5 font-mono text-[11px] tracking-[1px] text-signal"
                  title="能力指纹：定级后三轴等级的个人化编码"
                >
                  <FingerprintPattern className="size-3.5" strokeWidth={1.5} aria-hidden="true" />
                  {fingerprint}
                </span>
                <span className="text-faint">由 HLR 掌握度驱动 · 实时</span>
              </span>
            ) : (
              '由 HLR 掌握度驱动 · 实时'
            )
          }
        />
      </div>
      <section className="deck-boot deck-boot-2 grid grid-cols-1 gap-4 lg:grid-cols-3">
        {axes.map((axis) => (
          <AxisCard key={axis.key} axis={axis} />
        ))}
      </section>
    </>
  )
}
