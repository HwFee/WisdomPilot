'use client'

import type { DefectType, InjectedDefect, ReviewMark, ReviewVerdict } from '@/lib/api/deck/types'
import { DEFECT_TYPES, defectMeta } from './defect-meta'

/** 行状态：审查中（已标注）或揭示后（命中/漏报/误报） */
type LineVerdict = 'hit' | 'missed' | 'false-alarm'

function verdictForLine(line: number, verdict: ReviewVerdict): LineVerdict | null {
  if (verdict.hits.some((d) => d.line === line)) return 'hit'
  if (verdict.missed.some((d) => d.line === line)) return 'missed'
  if (verdict.false_alarms.some((m) => m.line === line)) return 'false-alarm'
  return null
}

const VERDICT_STYLE: Record<LineVerdict, string> = {
  hit: 'border-l-2 border-signal bg-signal/5',
  missed: 'border-l-2 border-amber bg-amber/5',
  'false-alarm': 'border-l-2 border-deck-red bg-deck-red/5',
}

const VERDICT_TAG: Record<LineVerdict, { label: string; className: string }> = {
  hit: { label: '命中', className: 'text-signal' },
  missed: { label: '漏掉', className: 'text-amber' },
  'false-alarm': { label: '误报', className: 'text-deck-red' },
}

export function CodeViewer({
  code,
  marks,
  verdict,
  activeLine,
  onLineClick,
  onPickType,
  revealed,
}: {
  code: string
  marks: ReviewMark[]
  verdict: ReviewVerdict | null
  activeLine: number | null
  onLineClick: (line: number) => void
  onPickType: (line: number, type: DefectType) => void
  revealed: boolean
}) {
  const lines = code.split('\n')

  return (
    <div className="deck-panel overflow-hidden">
      <div className="border-b border-line px-4 py-2 font-mono text-[11px] text-faint">
        SOURCE · 点击行号标注缺陷
      </div>
      <div className="overflow-x-auto py-2 font-mono text-[13px] leading-[1.7]">
        {lines.map((text, i) => {
          const lineNo = i + 1
          const mark = marks.find((m) => m.line === lineNo)
          const lineVerdict = verdict ? verdictForLine(lineNo, verdict) : null
          return (
            <div key={lineNo}>
              <div
                onClick={() => !revealed && onLineClick(lineNo)}
                className={`flex cursor-pointer items-stretch transition-colors hover:bg-panel-raised ${
                  lineVerdict ? VERDICT_STYLE[lineVerdict] : ''
                } ${activeLine === lineNo ? 'bg-panel-raised' : ''}`}
              >
                <span className="w-12 shrink-0 select-none pr-4 text-right text-faint">
                  {lineNo}
                </span>
                <span className="w-4 shrink-0">
                  {mark && !revealed && (
                    <i
                      className={`mt-[9px] inline-block h-2 w-2 rounded-[1px] ${defectMeta(mark.type).dotClass}`}
                    />
                  )}
                </span>
                <span className="whitespace-pre text-text">{text || ' '}</span>
                {lineVerdict && (
                  <span
                    className={`ml-auto shrink-0 pl-4 pr-3 text-[11px] ${VERDICT_TAG[lineVerdict].className}`}
                  >
                    {VERDICT_TAG[lineVerdict].label}
                  </span>
                )}
              </div>
              {/* 缺陷类型选择行 */}
              {activeLine === lineNo && !revealed && (
                <div className="flex flex-wrap items-center gap-2 border-y border-line bg-panel-raised px-16 py-2">
                  <span className="text-[11px] text-faint">第 {lineNo} 行：</span>
                  {DEFECT_TYPES.map((d) => (
                    <button
                      key={d.type}
                      onClick={() => onPickType(lineNo, d.type)}
                      className={`rounded-[3px] border border-line px-2 py-0.5 text-[11px] transition-colors hover:border-current ${d.textClass}`}
                    >
                      {d.label}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

/** 揭示态下每处注入缺陷的说明列表 */
export function DefectExplanations({ verdict }: { verdict: ReviewVerdict }) {
  const all: Array<{ defect: InjectedDefect; hit: boolean }> = [
    ...verdict.hits.map((defect) => ({ defect, hit: true })),
    ...verdict.missed.map((defect) => ({ defect, hit: false })),
  ].sort((a, b) => a.defect.line - b.defect.line)

  return (
    <div className="mt-4 space-y-3">
      {all.map(({ defect, hit }) => (
        <div key={defect.line} className="border-t border-line pt-3 first:border-t-0 first:pt-0">
          <div className="flex items-center gap-2 font-mono text-[11px]">
            <span className={hit ? 'text-signal' : 'text-amber'}>{hit ? '● 命中' : '● 漏掉'}</span>
            <span className="text-faint">第 {defect.line} 行</span>
            <span className={defectMeta(defect.type).textClass}>
              {defectMeta(defect.type).label}
            </span>
          </div>
          <p className="mt-1.5 text-xs leading-relaxed text-dim">{defect.explanation}</p>
        </div>
      ))}
    </div>
  )
}
