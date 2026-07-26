'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { isAuthenticated } from '@/lib/api'
import { getReviewQueue } from '@/lib/api/deck/review'
import type { ReviewQueue, ReviewQueueKind } from '@/lib/api/deck/types'
import { DeckShell } from '../deck/DeckShell'
import { PanelTag } from '../deck/kit'

const KIND_META: Record<ReviewQueueKind, { label: string; hint: string }> = {
  'review-gym': { label: '审查室', hint: '漏报/误报的关，重审全中后出队' },
  arena: { label: '竞技场', hint: '尚未攻克的挑战，让测试全绿后出队' },
  knowledge: { label: '知识点', hint: '掌握度低于 60%，费曼检验讲清楚后出队' },
}
const KIND_ORDER: ReviewQueueKind[] = ['review-gym', 'arena', 'knowledge']

/** 复盘：错题/失败项聚合队列。与导师对话相互独立——这里是内容驱动的重练 */
export function ReviewClient() {
  const { push } = useRouter()
  const [queue, setQueue] = useState<ReviewQueue | null>(null)

  useEffect(() => {
    if (!isAuthenticated()) {
      push('/login')
      return
    }
    getReviewQueue().then(setQueue).catch(() => setQueue({ items: [], total: 0 }))
  }, [push])

  return (
    <DeckShell>
      <div className="deck-boot deck-boot-1">
        <PanelTag label="REVIEW · 复盘" variant="warn" />
        <h1 className="mt-3 text-xl font-semibold">错题不会因为遗忘而消失</h1>
        <p className="mt-1.5 font-mono text-[11px] text-dim">
          你搞砸过的东西都排在这里。清掉一项，它才会出队。
        </p>
      </div>

      <div className="mt-6 space-y-6">
        {!queue && (
          <div className="deck-panel p-8 font-mono text-sm text-dim">
            载入中<span className="deck-cursor ml-2" />
          </div>
        )}

        {queue && queue.total === 0 && (
          <div className="deck-panel p-[26px_28px] text-center">
            <div className="font-mono text-[13px] text-signal">队列是空的</div>
            <p className="mt-2 text-[13px] text-dim">
              没有漏报的审查、没有未攻克的挑战、没有薄弱知识点——去首页领今天的主任务。
            </p>
            <Link href="/dashboard" className="deck-btn-primary mt-4 inline-block !px-5 !py-2 text-xs">
              回首页 →
            </Link>
          </div>
        )}

        {queue &&
          KIND_ORDER.map((kind) => {
            const items = queue.items.filter((i) => i.kind === kind)
            if (items.length === 0) return null
            const meta = KIND_META[kind]
            return (
              <section key={kind} className="deck-boot deck-boot-2">
                <div className="mb-3 flex items-baseline gap-3">
                  <span className="font-mono text-[11px] tracking-[1.5px] text-faint">
                    {meta.label} · {items.length}
                  </span>
                  <span className="font-mono text-[10px] text-faint">{meta.hint}</span>
                </div>
                <div className="space-y-3">
                  {items.map((i) => (
                    <div key={i.id} className="deck-panel deck-panel-hoverable flex flex-wrap items-center gap-4 px-5 py-4">
                      <div className="min-w-0 flex-1">
                        <div className="text-[14px] font-medium">{i.title}</div>
                        <div className="mt-1 font-mono text-[11px] text-dim">
                          {i.detail}
                          {i.last_at && <span className="ml-3 text-faint">上次 {i.last_at}</span>}
                        </div>
                      </div>
                      <Link href={i.target_url} className="deck-btn-primary !px-4 !py-1.5 text-xs">
                        {i.cta_label}
                      </Link>
                    </div>
                  ))}
                </div>
              </section>
            )
          })}
      </div>
    </DeckShell>
  )
}
