'use client'

import { PanelTag } from '../deck/kit'
import { DEFECT_TYPES } from './defect-meta'

/** 缺陷类型图例：右侧栏常驻说明五种缺陷长什么样、怎么判断 */
export function DefectLegend() {
  return (
    <div className="deck-panel h-fit p-[18px_20px]">
      <PanelTag label="LEGEND · 缺陷类型" />
      <div className="mt-3 space-y-2.5">
        {DEFECT_TYPES.map((d) => (
          <div key={d.type} className="flex items-start gap-2.5">
            <i className={`mt-[5px] h-2 w-2 shrink-0 rounded-[1px] ${d.dotClass}`} aria-hidden="true" />
            <div className="min-w-0">
              <div className={`text-xs font-medium ${d.textClass}`}>{d.label}</div>
              <p className="mt-0.5 text-[11px] leading-relaxed text-dim">{d.description}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
