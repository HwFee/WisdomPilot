'use client'

import { useCallback, useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { isAuthenticated } from '@/lib/api'
import { getReviewSession, submitReview } from '@/lib/api/deck/review-gym'
import { NEXT_SESSION } from '@/lib/api/deck/mock/review-gym'
import type { DefectType, ReviewMark, ReviewSession, ReviewVerdict } from '@/lib/api/deck/types'
import { DeckShell } from '../deck/DeckShell'
import { CountUp, PanelTag } from '../deck/kit'
import { useBadgeCelebration } from '../deck/BadgeUnlockCelebration'
import { CodeViewer, DefectExplanations } from './CodeViewer'
import { defectMeta } from './defect-meta'

type Phase = 'loading' | 'reviewing' | 'revealed'

function difficultyStars(level: number): string {
  return '★'.repeat(level) + '☆'.repeat(Math.max(0, 5 - level))
}

/** 右侧面板：会话信息 + 已标注清单 + 提交 */
function ReviewPanel({
  session,
  marks,
  submitting,
  onRemove,
  onSubmit,
}: {
  session: ReviewSession
  marks: ReviewMark[]
  submitting: boolean
  onRemove: (line: number) => void
  onSubmit: () => void
}) {
  return (
    <div className="deck-panel h-fit p-[18px_20px]">
      <PanelTag label="MISSION · 任务信息" variant="on" />
      <div className="mt-3 space-y-2 font-mono text-[11px] text-dim">
        <div className="flex justify-between">
          <span>关卡</span>
          <b className="font-medium text-text">{session.id}</b>
        </div>
        <div className="flex justify-between">
          <span>难度</span>
          <b className="font-medium text-text">{difficultyStars(session.difficulty)}</b>
        </div>
        <div className="flex justify-between">
          <span>预计</span>
          <b className="font-medium text-text">{session.eta_minutes} 分钟</b>
        </div>
        <div className="flex justify-between border-t border-line pt-2">
          <span>注入缺陷</span>
          <b className="font-medium text-amber">{session.defect_count} 处</b>
        </div>
      </div>

      <div className="mt-4 border-t border-line pt-3">
        <PanelTag label={`MARKS · 已标注 ${marks.length}`} />
        <div className="mt-2 space-y-1.5">
          {marks.length === 0 && (
            <p className="text-xs text-faint">还没有标注。点击左侧代码行，指出你怀疑的地方。</p>
          )}
          {marks.map((m) => (
            <div
              key={m.line}
              className="flex items-center gap-2 font-mono text-[11px] text-dim"
            >
              <i className={`h-2 w-2 rounded-[1px] ${defectMeta(m.type).dotClass}`} />
              <span>
                第 {m.line} 行 · {defectMeta(m.type).label}
              </span>
              <button
                onClick={() => onRemove(m.line)}
                className="ml-auto text-faint transition-colors hover:text-deck-red"
                aria-label={`删除第 ${m.line} 行标注`}
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      </div>

      <button
        className="deck-btn-primary mt-5 w-full"
        disabled={marks.length === 0 || submitting}
        onClick={onSubmit}
      >
        {submitting ? '判定中…' : '提交审查'}
      </button>
      <p className="mt-2 text-center font-mono text-[10px] text-faint">
        误报会扣分，宁缺毋滥
      </p>
    </div>
  )
}

/** 结算面板 */
function VerdictPanel({
  session,
  verdict,
  onNext,
}: {
  session: ReviewSession
  verdict: ReviewVerdict
  onNext: () => void
}) {
  const { push } = useRouter()
  return (
    <div className="deck-panel h-fit p-[18px_20px]">
      <PanelTag label="VERDICT · 审查结算" variant={verdict.missed.length === 0 ? 'on' : 'warn'} />
      <div className="mt-4 text-center">
        <div className="font-mono text-[42px] font-medium leading-none text-signal">
          <CountUp value={verdict.score} delay={200} />
        </div>
        <div className="mt-1 font-mono text-[11px] text-faint">REVIEW SCORE</div>
      </div>
      <div className="mt-4 space-y-2 font-mono text-[11px] text-dim">
        <div className="flex justify-between">
          <span>命中</span>
          <b className="font-medium text-signal">{verdict.hits.length} 处</b>
        </div>
        <div className="flex justify-between">
          <span>漏报</span>
          <b className="font-medium text-amber">{verdict.missed.length} 处</b>
        </div>
        <div className="flex justify-between">
          <span>误报</span>
          <b className="font-medium text-deck-red">{verdict.false_alarms.length} 处</b>
        </div>
        <div className="flex justify-between border-t border-line pt-2">
          <span>标注准确率</span>
          <b className="font-medium text-text">{Math.round(verdict.accuracy * 100)}%</b>
        </div>
      </div>
      <div className="mt-5 flex flex-col gap-2">
        <button className="deck-btn-primary w-full" onClick={onNext}>
          下一关 · {NEXT_SESSION[session.id]} →
        </button>
        <button className="deck-btn-ghost w-full" onClick={() => push('/dashboard')}>
          返回训练舱
        </button>
      </div>
    </div>
  )
}

/** 代码审查室：状态机 loading → reviewing → revealed */
export function ReviewGymClient() {
  const { push } = useRouter()
  const searchParams = useSearchParams()
  const [phase, setPhase] = useState<Phase>('loading')
  const [session, setSession] = useState<ReviewSession | null>(null)
  const [marks, setMarks] = useState<ReviewMark[]>([])
  const [activeLine, setActiveLine] = useState<number | null>(null)
  const [verdict, setVerdict] = useState<ReviewVerdict | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const { celebrate, celebrationElement } = useBadgeCelebration()

  const loadSession = useCallback((id?: string) => {
    setPhase('loading')
    setMarks([])
    setVerdict(null)
    setActiveLine(null)
    getReviewSession(id).then((s) => {
      setSession(s)
      setPhase('reviewing')
    })
  }, [])

  useEffect(() => {
    if (!isAuthenticated()) {
      push('/login')
      return
    }
    loadSession(searchParams.get('session') ?? undefined)
  }, [push, searchParams, loadSession])

  const handleLineClick = (line: number) => {
    // 已标注行 → 取消标注；否则展开类型选择
    if (marks.some((m) => m.line === line)) {
      setMarks((prev) => prev.filter((m) => m.line !== line))
      setActiveLine(null)
      return
    }
    setActiveLine((prev) => (prev === line ? null : line))
  }

  const handlePickType = (line: number, type: DefectType) => {
    setMarks((prev) => [...prev.filter((m) => m.line !== line), { line, type }])
    setActiveLine(null)
  }

  const handleSubmit = () => {
    if (!session) return
    setSubmitting(true)
    submitReview(session.id, marks).then((v) => {
      setVerdict(v)
      setSubmitting(false)
      setPhase('revealed')
      celebrate(v.new_badges)
    })
  }

  return (
    <DeckShell>
      {celebrationElement}
      <div className="deck-boot deck-boot-1">
        <PanelTag label="REVIEW GYM · 代码审查室" variant="on" />
        <h1 className="mt-3 text-xl font-semibold">
          {session ? `${session.title} —— 找出全部 ${session.defect_count} 处注入缺陷` : '载入中…'}
        </h1>
        {session?.related_weakness && (
          <p className="mt-1 font-mono text-[11px] text-dim">
            关联弱点 <b className="font-medium text-amber">{session.related_weakness}</b>
          </p>
        )}
      </div>

      <div className="deck-boot deck-boot-2 mt-6 grid grid-cols-1 gap-4 lg:grid-cols-[1fr_340px]">
        {phase === 'loading' || !session ? (
          <div className="deck-panel p-8 font-mono text-sm text-dim">
            正在载入代码<span className="deck-cursor ml-2" />
          </div>
        ) : (
          <>
            <div>
              <CodeViewer
                code={session.code}
                marks={marks}
                verdict={verdict}
                activeLine={activeLine}
                onLineClick={handleLineClick}
                onPickType={handlePickType}
                revealed={phase === 'revealed'}
              />
              {phase === 'revealed' && verdict && (
                <div className="deck-panel mt-4 p-[18px_20px]">
                  <PanelTag label="ANALYSIS · 缺陷解析" />
                  <DefectExplanations verdict={verdict} />
                </div>
              )}
            </div>
            {phase === 'reviewing' ? (
              <ReviewPanel
                session={session}
                marks={marks}
                submitting={submitting}
                onRemove={(line) => setMarks((prev) => prev.filter((m) => m.line !== line))}
                onSubmit={handleSubmit}
              />
            ) : (
              verdict && (
                <VerdictPanel
                  session={session}
                  verdict={verdict}
                  onNext={() => loadSession(NEXT_SESSION[session.id])}
                />
              )
            )}
          </>
        )}
      </div>
    </DeckShell>
  )
}
