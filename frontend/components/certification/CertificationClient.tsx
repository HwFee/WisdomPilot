'use client'

import { useCallback, useEffect, useState, type CSSProperties } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { isAuthenticated } from '@/lib/api'
import { getCertificationHome, getExam, submitExam } from '@/lib/api/deck/certification'
import { placementLevels } from '@/lib/api/deck/mock/certification'
import type {
  BadgeInfo,
  CertAnswer,
  CertExam,
  CertResult,
  CertificationHome,
} from '@/lib/api/deck/types'
import { DeckShell } from '../deck/DeckShell'
import { CountUp, PanelTag, SectionHead } from '../deck/kit'
import { BadgeIcon } from '../deck/BadgeIcon'
import { useBadgeCelebration } from '../deck/BadgeUnlockCelebration'
import { TIER_COLOR, TIER_LABEL, TIER_ORDER, TIER_TEXT_CLASS } from '../deck/badge-meta'

type Phase = 'loading' | 'home' | 'exam' | 'result'

function formatClock(sec: number): string {
  return `${String(Math.floor(sec / 60)).padStart(2, '0')}:${String(sec % 60).padStart(2, '0')}`
}

/* ── HOME：徽章墙 + 可考列表 ── */

/** 徽章墙：按 tier 分组；未解锁 60% 透明 + 虚线边框；hidden 未解锁由数据脱敏为 ??? */
function BadgeWall({
  badges,
  newBadgeIds,
}: {
  badges: BadgeInfo[]
  /** 本次会话新解锁的徽章 id：首次进入视图边框 pulse 一次 */
  newBadgeIds: string[]
}) {
  const unlockedCount = badges.filter((b) => b.unlocked).length
  return (
    <>
      <div className="deck-boot deck-boot-3">
        <SectionHead title="徽章墙 / Badges" note={`已解锁 ${unlockedCount} / ${badges.length}`} />
      </div>
      <div className="deck-boot deck-boot-3 space-y-4">
        {TIER_ORDER.map((tier) => (
          <div key={tier}>
            <div className={`mb-2 font-mono text-[10px] tracking-[1.5px] ${TIER_TEXT_CLASS[tier]}`}>
              {TIER_LABEL[tier]}
            </div>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
              {badges
                .filter((b) => b.tier === tier)
                .map((b) => {
                  const isNew = newBadgeIds.includes(b.id)
                  return (
                    <div
                      key={b.id}
                      className={`flex items-center gap-3 rounded border p-3 ${
                        b.unlocked ? 'border-line bg-panel' : 'border-dashed border-line opacity-60'
                      } ${isNew ? 'badge-wall-new' : ''}`}
                      style={
                        isNew
                          ? ({ '--badge-color': TIER_COLOR[b.tier] } as CSSProperties)
                          : undefined
                      }
                    >
                      <BadgeIcon id={b.id} tier={b.tier} size={36} locked={!b.unlocked} />
                      <div className="min-w-0">
                        <div className="truncate text-[13px] font-medium text-text">{b.title}</div>
                        <div className="truncate font-mono text-[10px] text-faint">
                          {b.condition_desc}
                        </div>
                        {b.unlocked && (
                          <div className="font-mono text-[10px] text-signal">+{b.reward_cores}</div>
                        )}
                      </div>
                    </div>
                  )
                })}
            </div>
          </div>
        ))}
      </div>
    </>
  )
}

function HomeView({
  home,
  newBadgeIds,
  onStart,
}: {
  home: CertificationHome
  newBadgeIds: string[]
  onStart: (examId: string) => void
}) {
  return (
    <div className="space-y-4">
      {/* 无 AI 环境说明 */}
      <div className="deck-boot deck-boot-1 rounded border border-amber bg-amber/10 px-4 py-3 font-mono text-[11px] leading-relaxed text-amber">
        NO-AI ZONE —— 考试期间没有提示、没有 AI、没有补考。通过，就是你不靠 AI 也会的证据。
      </div>

      {/* 徽章墙 */}
      <div className="deck-boot deck-boot-2">
        <SectionHead title="已认证 / Certified" note={`${home.certified.length} 项`} />
      </div>
      <div className="deck-boot deck-boot-2 grid grid-cols-1 gap-4 sm:grid-cols-2">
        {home.certified.map((c) => (
          <div key={c.verify_code} className="deck-panel deck-panel-hoverable p-[18px_20px]">
            <div className="flex items-baseline justify-between">
              <span className="text-[15px] font-semibold">{c.topic}</span>
              <span className="font-mono text-xs text-signal">{c.level}</span>
            </div>
            <div className="mt-2 font-mono text-[11px] text-dim">
              {c.score} 分 · {c.date}
            </div>
            <div className="mt-1.5 font-mono text-[10px] text-faint">VERIFY: {c.verify_code}</div>
          </div>
        ))}
        {home.certified.length === 0 && (
          <div className="deck-panel p-[18px_20px] text-[13px] text-dim">
            还没有认证。通过第一场，把名字刻上这面墙。
          </div>
        )}
      </div>

      {/* 徽章墙 */}
      <BadgeWall badges={home.badges} newBadgeIds={newBadgeIds} />

      {/* 可考列表 */}
      <div className="deck-boot deck-boot-4">
        <SectionHead
          title="可参加认证 / Available"
          note={home.next_available_days ? `冷却期 ${home.next_available_days} 天` : undefined}
        />
      </div>
      <div className="deck-boot deck-boot-4 space-y-3">
        {home.available_exams.map((e) => {
          const cooling = home.next_available_days !== null && home.next_available_days > 0
          return (
            <div
              key={e.id}
              className="deck-panel flex flex-wrap items-center gap-4 px-5 py-4"
            >
              <span className="text-[15px] font-semibold">{e.topic}</span>
              <span className="font-mono text-[11px] text-dim">
                {e.question_count} 题 · 限时 {e.time_limit_min} 分钟 · {e.pass_score} 分通过
              </span>
              <button
                className="deck-btn-primary ml-auto !px-5 !py-2 text-xs"
                disabled={cooling}
                onClick={() => onStart(e.id)}
              >
                {cooling ? `${home.next_available_days} 天后可考` : '开始认证'}
              </button>
            </div>
          )
        })}
      </div>
    </div>
  )
}

/* ── EXAM：限时作答 ── */

function ExamView({
  exam,
  isPlacement,
  onSubmit,
}: {
  exam: CertExam
  isPlacement: boolean
  onSubmit: (answers: CertAnswer[]) => void
}) {
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [secondsLeft, setSecondsLeft] = useState(exam.info.time_limit_min * 60)
  const [confirming, setConfirming] = useState(false)

  const collect = useCallback(
    (): CertAnswer[] =>
      exam.questions.map((q) => ({ question_id: q.id, answer: answers[q.id] ?? '' })),
    [exam, answers]
  )

  // 倒计时，到 0 自动交卷
  useEffect(() => {
    if (secondsLeft <= 0) {
      onSubmit(collect())
      return
    }
    const timer = setTimeout(() => setSecondsLeft((s) => s - 1), 1000)
    return () => clearTimeout(timer)
  }, [secondsLeft, collect, onSubmit])

  const answered = exam.questions.filter((q) => (answers[q.id] ?? '').trim() !== '').length

  return (
    <div className="space-y-4">
      {/* 顶条：倒计时 + 进度（不吸附，避免滚动时盖住题目） */}
      <div className="deck-panel flex items-center gap-4 px-5 py-3">
        <PanelTag
          label={isPlacement ? 'PLACEMENT · 定级测试' : `EXAM · ${exam.info.topic}认证`}
          variant="warn"
        />
        <span className="font-mono text-[11px] text-dim">
          {answered}/{exam.questions.length} 已答
        </span>
        <span
          className={`ml-auto font-mono text-xl font-medium ${
            secondsLeft < 60 ? 'text-deck-red' : 'text-signal'
          }`}
        >
          {formatClock(secondsLeft)}
        </span>
      </div>

      {/* 题目 */}
      {exam.questions.map((q, idx) => (
        <div key={q.id} className="deck-panel p-[18px_20px]">
          <div className="font-mono text-[10px] tracking-[1.5px] text-faint">
            Q{idx + 1} · {q.kind === 'mcq' ? '选择' : '手写'}
          </div>
          <p className="mt-2 text-[14px] leading-relaxed text-text">{q.prompt}</p>
          {q.kind === 'mcq' ? (
            <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2">
              {q.options?.map((opt) => (
                <button
                  key={opt}
                  onClick={() => setAnswers((prev) => ({ ...prev, [q.id]: opt }))}
                  className={`rounded border px-3.5 py-2.5 text-left text-[13px] transition-colors ${
                    answers[q.id] === opt
                      ? 'border-signal bg-signal/10 text-signal'
                      : 'border-line text-dim hover:border-line-bright hover:text-text'
                  }`}
                >
                  {opt}
                </button>
              ))}
            </div>
          ) : (
            <textarea
              value={answers[q.id] ?? q.starter_code ?? ''}
              onChange={(e) => setAnswers((prev) => ({ ...prev, [q.id]: e.target.value }))}
              onFocus={() => {
                if (!(q.id in answers)) setAnswers((prev) => ({ ...prev, [q.id]: q.starter_code ?? '' }))
              }}
              rows={6}
              spellCheck={false}
              className="mt-3 w-full rounded border border-line bg-bg p-3 font-mono text-[13px] leading-[1.7] text-text outline-none focus:border-signal"
            />
          )}
        </div>
      ))}

      {/* 交卷 */}
      <div className="deck-panel flex items-center gap-4 px-5 py-4">
        {confirming ? (
          <>
            <span className="font-mono text-[11px] text-amber">
              {exam.questions.length - answered > 0
                ? `还有 ${exam.questions.length - answered} 题未答，确定交卷？`
                : '确定交卷？提交后不可修改。'}
            </span>
            <button className="deck-btn-primary ml-auto !px-5 !py-2 text-xs" onClick={() => onSubmit(collect())}>
              确认交卷
            </button>
            <button className="deck-btn-ghost" onClick={() => setConfirming(false)}>
              再想想
            </button>
          </>
        ) : (
          <>
            <span className="font-mono text-[11px] text-dim">到 0 自动交卷</span>
            <button className="deck-btn-primary ml-auto !px-6 !py-2.5" onClick={() => setConfirming(true)}>
              交卷
            </button>
          </>
        )}
      </div>
    </div>
  )
}

/* ── RESULT：成绩 + 凭证 ── */

function ResultView({
  result,
  isPlacement,
  onBack,
}: {
  result: CertResult
  isPlacement: boolean
  onBack: () => void
}) {
  const { push } = useRouter()
  const [copied, setCopied] = useState(false)
  const levels = isPlacement ? placementLevels(result.score) : null

  const copyCode = (code: string) => {
    navigator.clipboard?.writeText(code).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    })
  }

  return (
    <div className="space-y-4">
      <div className="deck-panel p-[26px_28px] text-center">
        <PanelTag
          label={isPlacement ? 'PLACEMENT RESULT · 定级完成' : result.passed ? 'PASSED · 认证通过' : 'FAILED · 未通过'}
          variant={isPlacement || result.passed ? 'on' : 'warn'}
        />
        <div
          className={`mt-4 font-mono text-[52px] font-medium leading-none ${
            isPlacement || result.passed ? 'text-signal' : 'text-deck-red'
          }`}
        >
          <CountUp value={result.score} delay={200} />
        </div>
        <div className="mt-1 font-mono text-[11px] text-faint">SCORE / 100</div>
      </div>

      {/* 定级：三轴初始等级 */}
      {levels && (
        <div className="grid grid-cols-3 gap-4">
          {(
            [
              { label: '审阅', lv: levels.review },
              { label: '调试', lv: levels.debug },
              { label: '实现', lv: levels.implement },
            ] as const
          ).map((a) => (
            <div key={a.label} className="deck-panel p-4 text-center">
              <div className="text-[13px] text-dim">{a.label}</div>
              <div className="mt-1 font-mono text-lg text-signal">LV.{a.lv}</div>
            </div>
          ))}
        </div>
      )}

      {/* 凭证卡 */}
      {result.certificate && (
        <div className="deck-panel border-signal p-[22px_24px]">
          <PanelTag label="CERTIFICATE · 能力凭证" variant="on" />
          <div className="mt-3 flex flex-wrap items-baseline gap-x-6 gap-y-1">
            <span className="text-lg font-semibold">{result.certificate.topic}</span>
            <span className="font-mono text-xs text-signal">{result.certificate.level}</span>
            <span className="font-mono text-[11px] text-dim">
              {result.certificate.score} 分 · {result.certificate.date}
            </span>
          </div>
          <div className="mt-3 flex items-center gap-3">
            <code className="rounded border border-line bg-bg px-2.5 py-1 font-mono text-[11px] text-text">
              {result.certificate.verify_code}
            </code>
            <button className="deck-btn-ghost !px-3 !py-1 text-[11px]" onClick={() => copyCode(result.certificate!.verify_code)}>
              {copied ? '已复制 ✓' : '复制验证码'}
            </button>
          </div>
        </div>
      )}

      {/* 每题对错 */}
      <div className="deck-panel p-[18px_20px]">
        <PanelTag label="DETAIL · 逐题结果" />
        <div className="mt-3 space-y-1.5">
          {result.per_question.map((p, i) => (
            <div key={p.question_id} className="flex items-center gap-3 font-mono text-[11px]">
              <span className={p.correct ? 'text-signal' : 'text-deck-red'}>
                {p.correct ? '●' : '●'}
              </span>
              <span className="text-dim">
                第 {i + 1} 题 · {p.correct ? '正确' : '错误'}
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="flex gap-3">
        <button className="deck-btn-primary" onClick={() => (isPlacement ? push('/dashboard') : onBack())}>
          {isPlacement ? '进入训练舱 →' : '返回认证中心'}
        </button>
      </div>
    </div>
  )
}

/* ── 主组件：状态机 home → exam → result ── */

export function CertificationClient() {
  const { push } = useRouter()
  const searchParams = useSearchParams()
  const [phase, setPhase] = useState<Phase>('loading')
  const [home, setHome] = useState<CertificationHome | null>(null)
  const [exam, setExam] = useState<CertExam | null>(null)
  const [result, setResult] = useState<CertResult | null>(null)
  const [isPlacement, setIsPlacement] = useState(false)
  const [newBadgeIds, setNewBadgeIds] = useState<string[]>([])
  const { celebrate, celebrationElement } = useBadgeCelebration()

  useEffect(() => {
    if (!isAuthenticated()) {
      push('/login')
      return
    }
    if (searchParams.get('placement') === '1') {
      setIsPlacement(true)
      getExam('placement').then((e) => {
        setExam(e)
        setPhase('exam')
      })
      return
    }
    getCertificationHome().then((h) => {
      setHome(h)
      setPhase('home')
    })
  }, [push, searchParams])

  const startExam = (examId: string) => {
    setIsPlacement(false)
    getExam(examId).then((e) => {
      setExam(e)
      setPhase('exam')
    })
  }

  const handleSubmit = (answers: CertAnswer[]) => {
    if (!exam) return
    submitExam(exam.info.id, answers).then((r) => {
      setResult(r)
      setPhase('result')
      celebrate(r.new_badges)
      setNewBadgeIds(r.new_badges.map((b) => b.id))
    })
  }

  return (
    <DeckShell>
      {celebrationElement}
      <div className="deck-boot deck-boot-1">
        <PanelTag label="NO-AI ZONE · 基本功认证" variant="on" />
        <h1 className="mt-3 text-xl font-semibold">
          {phase === 'exam' && isPlacement
            ? '5 分钟定级测试 —— 确定你的三轴初始等级'
            : '证明你不靠 AI 也会'}
        </h1>
      </div>
      <div className="mt-6">
        {phase === 'loading' && (
          <div className="deck-panel p-8 font-mono text-sm text-dim">
            载入中<span className="deck-cursor ml-2" />
          </div>
        )}
        {phase === 'home' && home && (
          <HomeView home={home} newBadgeIds={newBadgeIds} onStart={startExam} />
        )}
        {phase === 'exam' && exam && (
          <ExamView exam={exam} isPlacement={isPlacement} onSubmit={handleSubmit} />
        )}
        {phase === 'result' && result && exam && (
          <ResultView
            result={result}
            isPlacement={isPlacement}
            onBack={() => {
              setPhase('loading')
              getCertificationHome().then((h) => {
                setHome(h)
                setResult(null)
                setPhase('home')
              })
            }}
          />
        )}
      </div>
    </DeckShell>
  )
}
