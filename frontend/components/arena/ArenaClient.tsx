'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import dynamic from 'next/dynamic'
import { useRouter } from 'next/navigation'
import { isAuthenticated } from '@/lib/api'
import { getArenaHome, runArenaCode } from '@/lib/api/deck/arena'
import type { ArenaHome, ArenaRunResult } from '@/lib/api/deck/types'
import { DeckShell } from '../deck/DeckShell'
import { PanelTag } from '../deck/kit'
import { useBadgeCelebration } from '../deck/BadgeUnlockCelebration'

const MonacoEditor = dynamic(() => import('@monaco-editor/react'), { ssr: false })

function formatClock(sec: number): string {
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

function difficultyStars(level: number): string {
  return '★'.repeat(level) + '☆'.repeat(Math.max(0, 5 - level))
}

/** 顶部状态条：段位 / 积分 / 排名 / 连对 */
function ProfileStrip({ profile }: { profile: ArenaHome['profile'] }) {
  const items: Array<{ k: string; v: string; accent?: boolean }> = [
    { k: '段位', v: profile.tier, accent: true },
    { k: '积分', v: String(profile.rating) },
    { k: '本周排名', v: `#${profile.week_rank} ▲${profile.rank_delta}` },
    { k: '连对', v: `${profile.win_streak} 场` },
  ]
  return (
    <div className="deck-panel flex flex-wrap items-center gap-x-8 gap-y-2 px-5 py-3.5">
      <PanelTag label="DEBUG ARENA · 调试竞技场" variant="on" />
      {items.map((it) => (
        <span key={it.k} className="font-mono text-[11px] text-dim">
          {it.k}{' '}
          <b className={`font-medium ${it.accent ? 'text-signal' : 'text-text'}`}>{it.v}</b>
        </span>
      ))}
    </div>
  )
}

/** 排行榜侧栏 */
function Leaderboard({ entries }: { entries: ArenaHome['leaderboard'] }) {
  const top = entries.filter((e) => !e.is_self)
  const self = entries.find((e) => e.is_self)
  const row = (e: ArenaHome['leaderboard'][number]) => (
    <div
      key={e.rank}
      className={`flex items-center gap-3 border-t border-line py-2 font-mono text-[11px] first:border-t-0 ${
        e.is_self ? 'text-signal' : 'text-dim'
      }`}
    >
      <span className="w-8 text-faint">#{e.rank}</span>
      <span className={e.is_self ? 'text-signal' : 'text-text'}>{e.name}</span>
      <span className="ml-auto">{e.rating}</span>
      <span className="w-10 text-right text-faint">+{e.solved_today}</span>
    </div>
  )
  return (
    <div className="deck-panel h-fit p-[18px_20px]">
      <PanelTag label="LEADERBOARD · 本周排行" />
      <div className="mt-3">{top.map(row)}</div>
      {self && (
        <div className="mt-2 border-t border-line-bright pt-2">
          <div className="mb-1 font-mono text-[10px] text-faint">你的位置</div>
          {row(self)}
        </div>
      )}
    </div>
  )
}

/** 调试竞技场主组件 */
export function ArenaClient() {
  const { push } = useRouter()
  const [home, setHome] = useState<ArenaHome | null>(null)
  const [code, setCode] = useState('')
  const [secondsLeft, setSecondsLeft] = useState(0)
  const [result, setResult] = useState<ArenaRunResult | null>(null)
  const [running, setRunning] = useState(false)
  const submittedRef = useRef(false)
  const { celebrate, celebrationElement } = useBadgeCelebration()

  useEffect(() => {
    if (!isAuthenticated()) {
      push('/login')
      return
    }
    getArenaHome().then((h) => {
      setHome(h)
      setCode(h.challenge.code)
      setSecondsLeft(h.challenge.time_limit_sec)
    })
  }, [push])

  const submit = useCallback(
    (currentCode: string) => {
      if (!home || submittedRef.current) return
      submittedRef.current = true
      setRunning(true)
      runArenaCode(home.challenge.id, currentCode).then((r) => {
        setResult(r)
        setRunning(false)
        celebrate(r.new_badges)
      })
    },
    [home, celebrate]
  )

  // 倒计时：到 0 自动交卷
  useEffect(() => {
    if (!home || result) return
    if (secondsLeft <= 0) {
      submit(code)
      return
    }
    const timer = setTimeout(() => setSecondsLeft((s) => s - 1), 1000)
    return () => clearTimeout(timer)
  }, [home, secondsLeft, result, code, submit])

  const resetRound = () => {
    if (!home) return
    submittedRef.current = false
    setResult(null)
    setCode(home.challenge.code)
    setSecondsLeft(home.challenge.time_limit_sec)
  }

  return (
    <DeckShell>
      {celebrationElement}
      {!home ? (
        <div className="deck-panel p-8 font-mono text-sm text-dim">
          正在接入竞技场<span className="deck-cursor ml-2" />
        </div>
      ) : (
        <div className="space-y-4">
          <div className="deck-boot deck-boot-1">
            <ProfileStrip profile={home.profile} />
          </div>

          <div className="deck-boot deck-boot-2 grid grid-cols-1 gap-4 lg:grid-cols-[1fr_340px]">
            <div className="space-y-4">
              {/* 题目 + 失败输出 */}
              <div className="deck-panel p-[18px_20px]">
                <div className="flex flex-wrap items-center gap-4">
                  <span className="text-[15px] font-semibold">{home.challenge.title}</span>
                  <span className="font-mono text-[11px] text-dim">
                    {home.challenge.id} · 难度 {difficultyStars(home.challenge.difficulty)}
                  </span>
                  <span
                    className={`ml-auto font-mono text-xl font-medium ${
                      secondsLeft < 60 && !result ? 'text-deck-red' : 'text-signal'
                    }`}
                  >
                    {formatClock(secondsLeft)}
                  </span>
                </div>
                <pre className="mt-3 overflow-x-auto rounded border border-line bg-bg p-3.5 font-mono text-xs leading-relaxed text-dim">
                  {result ? result.output : home.challenge.failing_output}
                </pre>
              </div>

              {/* 编辑器 */}
              <div className="deck-panel overflow-hidden">
                <div className="flex items-center border-b border-line px-4 py-2">
                  <span className="font-mono text-[11px] text-faint">
                    EDITOR · {home.challenge.language}
                  </span>
                  <button
                    className="deck-btn-primary ml-auto !px-5 !py-2 text-xs"
                    disabled={running || (result?.solved ?? false)}
                    onClick={() => submit(code)}
                  >
                    {running ? '判题中…' : '▶ 运行判题'}
                  </button>
                </div>
                <MonacoEditor
                  height="320px"
                  language={home.challenge.language}
                  theme="vs-dark"
                  value={code}
                  onChange={(v) => setCode(v ?? '')}
                  options={{
                    minimap: { enabled: false },
                    fontSize: 13,
                    fontFamily: "'JetBrains Mono', Consolas, monospace",
                    scrollBeyondLastLine: false,
                    padding: { top: 12 },
                  }}
                />
              </div>

              {/* 结果条 */}
              {result && (
                <div
                  className={`deck-panel flex flex-wrap items-center gap-4 px-5 py-4 ${
                    result.solved ? 'border-signal' : 'border-amber'
                  }`}
                >
                  <span
                    className={`font-mono text-sm font-medium ${
                      result.solved ? 'text-signal' : 'text-amber'
                    }`}
                  >
                    {result.solved ? '● SOLVED' : '● 未通过'} · {result.passed}/{result.total}
                  </span>
                  {result.solved && (
                    <span className="font-mono text-sm text-signal">+{result.score_delta} 分</span>
                  )}
                  <button className="deck-btn-ghost ml-auto" onClick={resetRound}>
                    {result.solved ? '下一场' : '再来一次'}
                  </button>
                </div>
              )}
            </div>

            <Leaderboard entries={home.leaderboard} />
          </div>
        </div>
      )}
    </DeckShell>
  )
}
