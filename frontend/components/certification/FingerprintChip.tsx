'use client'

import { FingerprintPattern } from 'lucide-react'

/**
 * 训练指纹短码（§3.5 P-11 路径唯一性标识）：
 * 「训练指纹 R3-D1-I4 · 你的能力分布独一无二」。
 * 只暴露三轴等级粗粒度信息，不含具体弱点知识点（隐私约束 4）。
 * 仅作展示，无交互；用于认证页头部与定级仪式页。
 */
export function FingerprintChip({ code }: { code: string }) {
  return (
    <div className="inline-flex flex-wrap items-center gap-x-2 gap-y-0.5 rounded border border-line bg-panel px-3.5 py-2.5">
      <FingerprintPattern
        className="size-4 shrink-0 text-signal"
        strokeWidth={1.5}
        aria-hidden="true"
      />
      <span className="font-mono text-xs tracking-[1px] text-text">
        训练指纹 <b className="font-medium text-signal">{code}</b>
      </span>
      <span className="font-mono text-[10px] text-faint">· 你的能力分布独一无二</span>
    </div>
  )
}
