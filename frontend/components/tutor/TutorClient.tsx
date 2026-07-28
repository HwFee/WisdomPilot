'use client'

import { useEffect, useRef, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { isAuthenticated } from '@/lib/api'
import { getTutorState, sendTutorMessage, startFeynman, submitFeynman } from '@/lib/api/deck/tutor'
import type { MasteryUpdate, TutorMessage, TutorMode, TutorReply } from '@/lib/api/deck/types'
import { DeckShell } from '../deck/DeckShell'
import { PanelTag } from '../deck/kit'
import { useBadgeCelebration } from '../deck/BadgeUnlockCelebration'

const GRADE_STYLE: Record<string, string> = {
  优秀: 'text-signal',
  良好: 'text-amber',
  待加强: 'text-deck-red',
}

interface DisplayMessage extends TutorMessage {
  grade?: string
  mastery?: MasteryUpdate
}

/** 单条消息 */
function MessageBubble({ msg }: { msg: DisplayMessage }) {
  if (msg.role === 'user') {
    return (
      <div className="flex justify-end">
        <div className="max-w-[75%] rounded border border-line-bright bg-signal/10 px-4 py-2.5 text-[13px] leading-relaxed text-text">
          {msg.text}
        </div>
      </div>
    )
  }
  return (
    <div className="flex justify-start">
      <div className="deck-panel max-w-[85%] px-4 py-3">
        <div className="mb-1 font-mono text-[10px] tracking-[1.5px] text-faint">
          SOCRATES{msg.mode === 'feynman' ? ' · FEYNMAN' : ''}
          {msg.grade && (
            <span className={`ml-2 ${GRADE_STYLE[msg.grade] ?? ''}`}>理解度 · {msg.grade}</span>
          )}
        </div>
        <p className="text-[13px] leading-relaxed text-text">{msg.text}</p>
        {msg.mastery && (
          <div className="mt-1.5 font-mono text-[11px] text-faint">
            掌握度 {Math.round(msg.mastery.p_l_before * 100)}% →{' '}
            <span
              className={
                msg.mastery.p_l_after >= msg.mastery.p_l_before ? 'text-signal' : 'text-deck-red'
              }
            >
              {Math.round(msg.mastery.p_l_after * 100)}%
            </span>
            {' · '}
            <span className="text-dim">{msg.mastery.kp_name}</span>
            {msg.mastery.level && (
              <>
                {' · '}
                <span className="text-dim">{msg.mastery.level}</span>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

/** 苏格拉底导师：追问模式 + 费曼「考考我」模式 */
export function TutorClient() {
  const { push } = useRouter()
  const searchParams = useSearchParams()
  const [messages, setMessages] = useState<DisplayMessage[]>([])
  const [mode, setMode] = useState<TutorMode>('socratic')
  const [balance, setBalance] = useState<number | null>(null)
  const [cost, setCost] = useState(2)
  const [topics, setTopics] = useState<string[]>([])
  const [input, setInput] = useState('')
  const [thinking, setThinking] = useState(false)
  const [loaded, setLoaded] = useState(false)
  const [feynmanSessionId, setFeynmanSessionId] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const topicHandled = useRef(false)
  const { celebrate, celebrationElement } = useBadgeCelebration()

  useEffect(() => {
    if (!isAuthenticated()) {
      push('/login')
      return
    }
    getTutorState().then((s) => {
      setMessages(s.messages)
      setBalance(s.cores_balance)
      setCost(s.cost_per_question)
      setTopics(s.suggested_topics)
      setLoaded(true)
      // 从仪表盘「针对训练」跳入：直接进入费曼模式
      const topic = searchParams.get('topic')
      if (topic && !topicHandled.current) {
        topicHandled.current = true
        setMode('feynman')
        startFeynman(topic).then((r) => {
          setFeynmanSessionId(r.feynman_session_id ?? null)
          setMessages((prev) => [...prev, r.message])
        })
      }
    })
  }, [push, searchParams])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, thinking])

  const handleSend = () => {
    const text = input.trim()
    if (!text || balance === null || balance < cost || thinking) return
    const userMsg: DisplayMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      mode,
      text,
    }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setThinking(true)

    const call: Promise<TutorReply> =
      mode === 'feynman'
        ? submitFeynman(feynmanSessionId ?? '', text, balance, cost)
        : sendTutorMessage(text, mode, messages.length, balance, cost)

    // 模拟导师思考延迟
    setTimeout(() => {
      call.then((r) => {
        setMessages((prev) => [...prev, { ...r.message, grade: r.grade, mastery: r.mastery_update }])
        setBalance(r.cores_balance)
        setThinking(false)
        celebrate(r.new_badges)
      })
    }, 900)
  }

  const handleTopic = (topic: string) => {
    if (thinking) return
    startFeynman(topic).then((r) => {
      setFeynmanSessionId(r.feynman_session_id ?? null)
      setMessages((prev) => [...prev, r.message])
    })
  }

  const insufficient = balance !== null && balance < cost

  return (
    <DeckShell>
      {celebrationElement}
      <div className="deck-boot deck-boot-1 flex flex-wrap items-center gap-4">
        <PanelTag label="AI TUTOR · 苏格拉底导师" variant="on" />
        {/* 模式切换 */}
        <div className="flex rounded border border-line font-mono text-[11px]">
          {(
            [
              { key: 'socratic', label: '追问模式' },
              { key: 'feynman', label: '考考我' },
            ] as const
          ).map((m) => (
            <button
              key={m.key}
              onClick={() => setMode(m.key)}
              className={`px-3.5 py-1.5 transition-colors ${
                mode === m.key ? 'bg-signal/10 text-signal' : 'text-dim hover:text-text'
              }`}
            >
              {m.label}
            </button>
          ))}
        </div>
        {balance !== null && (
          <span className="ml-auto rounded border border-line px-2.5 py-1 font-mono text-xs text-dim">
            ◈ {balance} · 每次提问 -{cost}
          </span>
        )}
      </div>

      {/* 消息流 */}
      <div className="deck-boot deck-boot-2 mt-4 space-y-3">
        {!loaded ? (
          <div className="deck-panel p-8 font-mono text-sm text-dim">
            导师接入中<span className="deck-cursor ml-2" />
          </div>
        ) : (
          <>
            {messages.map((m) => (
              <MessageBubble key={m.id} msg={m} />
            ))}
            {thinking && (
              <div className="flex justify-start">
                <div className="deck-panel px-4 py-3 font-mono text-xs text-faint">
                  SOCRATES 思考中<span className="deck-cursor ml-2" />
                </div>
              </div>
            )}
            {/* 费曼模式主题 chips */}
            {mode === 'feynman' && topics.length > 0 && (
              <div className="flex flex-wrap items-center gap-2 pt-1">
                <span className="font-mono text-[11px] text-faint">挑一个主题开讲：</span>
                {topics.map((t) => (
                  <button
                    key={t}
                    onClick={() => handleTopic(t)}
                    className="rounded border border-line px-2.5 py-1 font-mono text-[11px] text-dim transition-colors hover:border-signal hover:text-signal"
                  >
                    {t}
                  </button>
                ))}
              </div>
            )}
            <div ref={bottomRef} />
          </>
        )}
      </div>

      {/* 输入区 */}
      <div className="sticky bottom-4 mt-6">
        {insufficient && (
          <div className="mb-2 rounded border border-amber bg-amber/10 px-3 py-2 font-mono text-[11px] text-amber">
            智核不足 —— 通过基本功认证（+20）或等每日补充（+5）
          </div>
        )}
        <div className="deck-panel flex items-center gap-3 p-3">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            disabled={!loaded || insufficient}
            placeholder={
              mode === 'feynman' ? '用你的话解释这个知识点……' : '说说你卡住的地方……'
            }
            className="flex-1 bg-transparent font-mono text-[13px] text-text outline-none placeholder:text-faint disabled:opacity-50"
          />
          <button
            className="deck-btn-primary !px-5 !py-2 text-xs"
            disabled={!loaded || insufficient || !input.trim() || thinking}
            onClick={handleSend}
          >
            发送
          </button>
        </div>
      </div>
    </DeckShell>
  )
}
