'use client'

import { Award, BadgeCheck, Crosshair, TrendingUp, type LucideIcon } from 'lucide-react'
import type { TimelineEntry } from '@/lib/api/deck/types'
import { PanelTag } from '../deck/kit'

/* P-09 训练轨迹时间线：定级画像 → 能力轴升级 → 知识点里程碑 → 认证通过。
   条目由后端 GET /api/profile 的 timeline 字段提供（按时间升序），
   本组件只做展示：节点图标 + 日期 + 标题/详情。 */

/** 时间线条目类型 → 图标（lucide，统一 strokeWidth=1.5） */
const TYPE_ICON: Record<TimelineEntry['type'], LucideIcon> = {
  placement: Crosshair,     // 定级画像
  axis_upgrade: TrendingUp, // 能力轴升级
  mastery: Award,           // 知识点里程碑
  cert: BadgeCheck,         // 认证通过
}

/** 条目 → 标题与详情文案（纯展示逻辑，不依赖外部状态） */
function entryText(entry: TimelineEntry): { title: string; detail?: string } {
  switch (entry.type) {
    case 'placement':
      return {
        title: `完成定级测试 · ${entry.score} 分`,
        detail: `初始 审阅 LV.${entry.levels.review} · 调试 LV.${entry.levels.debug} · 实现 LV.${entry.levels.implement}`,
      }
    case 'axis_upgrade':
      return {
        title: `${entry.label}轴 LV.${entry.from_level} → LV.${entry.to_level}`,
        detail: '能力轴升级',
      }
    case 'mastery':
      return {
        title: `「${entry.kp_name}」达到${entry.level}`,
        detail: '知识点掌握里程碑',
      }
    case 'cert':
      return {
        title: `通过基本功认证「${entry.topic}」`,
        detail: `${entry.level} · ${entry.score} 分`,
      }
  }
}

/** 时间线视图：竖线串联节点，移动端单列不破版 */
export function TimelineTab({ entries }: { entries: TimelineEntry[] }) {
  return (
    <div className="deck-panel p-[18px_20px]">
      <PanelTag label={`TIMELINE · 训练轨迹 ${entries.length} 个节点`} variant="on" />
      {entries.length === 0 ? (
        <div className="mt-3 font-mono text-[11px] text-faint">
          还没有训练记录 —— 完成定级测试后，轨迹从这里开始。
        </div>
      ) : (
        <ol className="mt-4">
          {entries.map((entry, i) => {
            const Icon = TYPE_ICON[entry.type]
            const text = entryText(entry)
            const isLast = i === entries.length - 1
            return (
              <li key={`${entry.type}-${entry.date}-${i}`} className="relative flex gap-4 pb-5 last:pb-0">
                {/* 连接线（最后一个节点不画） */}
                {!isLast && (
                  <span
                    className="absolute left-[13px] top-7 h-full w-px bg-line"
                    aria-hidden="true"
                  />
                )}
                {/* 节点图标 */}
                <span className="relative z-10 flex size-7 shrink-0 items-center justify-center rounded-[3px] border border-line-bright bg-panel text-faint">
                  <Icon className="size-3.5" strokeWidth={1.5} aria-hidden="true" />
                </span>
                {/* 条目内容 */}
                <div className="min-w-0 flex-1 pt-0.5">
                  <div className="flex flex-wrap items-baseline gap-x-3 gap-y-0.5">
                    <span className="shrink-0 font-mono text-[11px] text-faint">{entry.date}</span>
                    <span className="text-[13px] font-medium text-text">{text.title}</span>
                  </div>
                  {text.detail && (
                    <div className="mt-0.5 font-mono text-[11px] text-dim">{text.detail}</div>
                  )}
                </div>
              </li>
            )
          })}
        </ol>
      )}
    </div>
  )
}
