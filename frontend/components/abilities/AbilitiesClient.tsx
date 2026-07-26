'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { isAuthenticated } from '@/lib/api'
import { getAbilityMap } from '@/lib/api/deck/abilities'
import type { AbilityMapDetail, AxisKey, KnowledgePoint } from '@/lib/api/deck/types'
import { DeckShell } from '../deck/DeckShell'
import { CountUp, PanelTag, SectionHead, Segments } from '../deck/kit'

const AXIS_META: Record<AxisKey, { label: string; en: string }> = {
  review: { label: '审阅', en: 'Review' },
  debug: { label: '调试', en: 'Debug' },
  implement: { label: '实现', en: 'Implement' },
}

const TREND_MARK = { up: '▲', flat: '—', down: '▼' } as const
const TREND_CLASS = { up: 'text-signal', flat: 'text-faint', down: 'text-deck-red' } as const

/** 掌握度条颜色：<0.5 琥珀，0.5-0.8 半透绿，>0.8 实绿 */
function barClass(p: number): string {
  if (p < 0.5) return 'bg-amber'
  if (p < 0.8) return 'bg-signal/50'
  return 'bg-signal'
}

function KnowledgeRow({ kp }: { kp: KnowledgePoint }) {
  const weak = kp.p_l < 0.62
  return (
    <div className="group flex items-center gap-4 border-t border-line py-2.5 first:border-t-0">
      <div className="w-44 shrink-0">
        <div className="text-[13px] text-text">{kp.name}</div>
        <div className="text-[11px] text-faint">{kp.category} · {kp.level}</div>
      </div>
      <div className="h-2 flex-1 overflow-hidden rounded-[2px] bg-panel-raised">
        <div
          className={`h-full ${barClass(kp.p_l)}`}
          style={{ width: `${Math.round(kp.p_l * 100)}%` }}
        />
      </div>
      <span className="w-10 shrink-0 text-right font-mono text-[11px] text-dim">
        {Math.round(kp.p_l * 100)}%
      </span>
      <span className={`w-4 shrink-0 font-mono text-[11px] ${TREND_CLASS[kp.trend]}`}>
        {TREND_MARK[kp.trend]}
      </span>
      {weak && (
        <Link
          href={`/tutor?topic=${encodeURIComponent(kp.name)}`}
          className="shrink-0 rounded-[3px] border border-line px-2.5 py-1 font-mono text-[11px] text-dim opacity-35 transition-all hover:border-signal hover:text-signal group-hover:opacity-100"
        >
          针对训练
        </Link>
      )}
    </div>
  )
}

/** 能力图谱：三轴详情 + 知识点掌握度网格 */
export function AbilitiesClient() {
  const { push } = useRouter()
  const [data, setData] = useState<AbilityMapDetail | null>(null)

  useEffect(() => {
    if (!isAuthenticated()) {
      push('/login')
      return
    }
    getAbilityMap().then(setData)
  }, [push])

  return (
    <DeckShell>
      <div className="deck-boot deck-boot-1">
        <PanelTag label="ABILITY MAP · 能力图谱" variant="on" />
        <h1 className="mt-3 text-xl font-semibold">三根能力轴，一张全景图</h1>
      </div>

      {!data ? (
        <div className="deck-panel mt-6 p-8 font-mono text-sm text-dim">
          同步掌握度数据<span className="deck-cursor ml-2" />
        </div>
      ) : (
        <>
          {!data.has_placement && (
            <div className="deck-boot deck-boot-1 mt-4 rounded border border-amber bg-amber/10 px-4 py-3 font-mono text-[11px] text-amber">
              还没有定级数据 ——{' '}
              <Link href="/certification?placement=1" className="underline underline-offset-2 hover:text-text">
                完成 5 分钟定级测试
              </Link>{' '}
              后这里才会亮起。
            </div>
          )}

          {/* 三轴大卡 */}
          <section className="deck-boot deck-boot-2 mt-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
            {data.axes.map((axis) => (
              <div key={axis.key} className="deck-panel deck-panel-hoverable p-[20px_22px]">
                <div className="flex items-baseline justify-between">
                  <span className="text-[15px] font-semibold">
                    {axis.label}
                    <span className="ml-2 font-mono text-[10px] uppercase tracking-[1.5px] text-faint">
                      {AXIS_META[axis.key].en}
                    </span>
                  </span>
                  <span className="font-mono text-xs text-signal">LV.{axis.level}</span>
                </div>
                <div className="mt-3.5">
                  <Segments filled={Math.round((axis.xp_current / axis.xp_next) * 10)} />
                </div>
                <div className="mt-2.5 font-mono text-[11px] text-dim">
                  <CountUp value={axis.xp_current} /> / {axis.xp_next.toLocaleString('en-US')} 至 LV.
                  {axis.level + 1}
                </div>
                {axis.weakest_focus && (
                  <div className="mt-1 text-xs text-dim">
                    短板：<b className="font-medium text-amber">{axis.weakest_focus}</b>
                  </div>
                )}
              </div>
            ))}
          </section>

          {/* 知识点网格：按轴分组 */}
          {data.axes.map((axis) => (
            <div key={axis.key} className="deck-boot deck-boot-3">
              <SectionHead
                title={`${axis.label}轴 / ${AXIS_META[axis.key].en}`}
                note={`${data.knowledge_points.filter((k) => k.axis === axis.key).length} 个知识点`}
              />
              <div className="deck-panel p-[18px_20px]">
                {data.knowledge_points
                  .filter((k) => k.axis === axis.key)
                  .map((kp) => (
                    <KnowledgeRow key={kp.name} kp={kp} />
                  ))}
              </div>
            </div>
          ))}
        </>
      )}
    </DeckShell>
  )
}
