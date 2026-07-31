'use client'

import { useRouter } from 'next/navigation'
import type { CertResult } from '@/lib/api/deck/types'
import {
  fingerprintFromPlacement,
  placementLevels,
} from '@/lib/api/deck/mock/certification'
import { PanelTag, Segments } from '../deck/kit'
import { FingerprintChip } from './FingerprintChip'

/** 三轴展示顺序固定：审阅 → 调试 → 实现（与 placementLevels / 指纹顺序一致） */
const AXES: Array<{ key: 'review' | 'debug' | 'implement'; label: string }> = [
  { key: 'review', label: '审阅' },
  { key: 'debug', label: '调试' },
  { key: 'implement', label: '实现' },
]

/* 每轴一句话（基于三轴等级差推导，文案遵守 §3.5 约束 3：说"基于你的能力数据"，不说"AI 生成"） */
const NOTE_BALANCED = '均衡起步，后续按训练反馈调整'
const NOTE_TOP = '起点最高，系统在这一轴上安排进阶任务'
const NOTE_LOW = '起点偏低，系统优先安排这一轴的基础训练'
const NOTE_MID = '随训练推进，逐步加深'

/**
 * 定级测试结果仪式页（§3.5 P-03 入舱画像）：
 * 提交 placement 后展示三轴初始等级 + 专属路径说明 + 训练指纹，
 * 从第一天建立「系统在为我个人定制路径」的认知。
 * placement 永不返回 passed=true，故本视图只消费 score。
 */
export function PlacementResultView({ result }: { result: CertResult }) {
  const { push } = useRouter()
  const levels = placementLevels(result.score)
  const fingerprint = fingerprintFromPlacement(levels)

  const lvList = AXES.map((a) => levels[a.key])
  const maxLv = Math.max(...lvList)
  const minLv = Math.min(...lvList)
  const balanced = maxLv === minLv
  const lowestLabel = balanced ? null : AXES.find((a) => levels[a.key] === minLv)?.label

  const noteFor = (lv: number): string => {
    if (balanced) return NOTE_BALANCED
    if (lv === maxLv) return NOTE_TOP
    if (lv === minLv) return NOTE_LOW
    return NOTE_MID
  }

  return (
    <div className="space-y-4">
      {/* 入舱画像主卡：三轴初始等级 + 指纹 */}
      <div className="deck-panel deck-boot deck-boot-1 p-[26px_28px]">
        <PanelTag label="PLACEMENT COMPLETE · 入舱画像已生成" variant="on" />
        <h2 className="mt-3 text-lg font-semibold">你的专属训练路径已生成</h2>
        <p className="mt-1.5 text-[13px] leading-relaxed text-dim">
          系统基于你的定级作答数据，生成了专属训练路径——你的起点与全站多数用户不同。
        </p>

        <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
          {AXES.map((a) => (
            <div key={a.key} className="rounded border border-line bg-panel p-4">
              <div className="flex items-baseline justify-between gap-2">
                <span className="text-[14px] font-semibold">{a.label}</span>
                <span className="font-mono text-xs text-signal">LV.{levels[a.key]}</span>
              </div>
              <div className="mt-3">
                <Segments filled={levels[a.key] * 2} />
              </div>
              <p className="mt-2.5 text-[12px] leading-relaxed text-dim">
                {noteFor(levels[a.key])}
              </p>
            </div>
          ))}
        </div>

        <div className="mt-6 flex justify-center">
          <FingerprintChip code={fingerprint} />
        </div>
      </div>

      {/* 专属路径说明：按最低轴给起始建议 */}
      <div className="deck-panel deck-boot deck-boot-2 p-[22px_24px]">
        <PanelTag label="YOUR PATH · 专属路径" variant="on" />
        <p className="mt-3 text-[13px] leading-relaxed text-text">
          {balanced
            ? '三轴均衡起步。基于你的能力数据，系统将在后续训练中根据你的表现动态调整每根轴的任务强度。'
            : `基于你的能力数据，系统会优先安排「${lowestLabel}」轴的基础训练，把起点补齐；其余两轴随进度逐步进阶。`}
        </p>
        <p className="mt-2 text-[13px] leading-relaxed text-dim">
          后续的主任务推荐、复盘队列与导师追问，都会从你的三轴等级出发——每个人看到的推荐都不一样。
        </p>
      </div>

      {/* 底部：分数小注（定级不计通过/失败）+ 进舱 CTA */}
      <div className="deck-boot deck-boot-3 flex flex-wrap items-center justify-between gap-3">
        <span className="font-mono text-[11px] text-faint">
          定级得分 {result.score} / 100 · 定级不计通过/失败
        </span>
        <button
          className="deck-btn-primary !px-6 !py-2.5"
          onClick={() => push('/dashboard')}
        >
          进入训练舱 →
        </button>
      </div>
    </div>
  )
}
