'use client'

import { useEffect, useRef, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { isAuthenticated } from '@/lib/api'
import {
  getTutorState,
  sendTutorMessage,
  startFeynman,
  submitFeynman,
  takeTutorQuestionContext,
} from '@/lib/api/deck/tutor'
import type {
  MasteryUpdate,
  TutorMessage,
  TutorMode,
  TutorQuestionContext,
  TutorReply,
} from '@/lib/api/deck/types'
import { DeckShell } from '../deck/DeckShell'
import { PanelTag } from '../deck/kit'
import { ErrorPanel } from '../deck/ErrorPanel'
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

/**
 * 按当前模式过滤消息流：苏格拉底与费曼各自看到各自的对话，
 * 切换 tab 即切换上下文（同屏会话内切回仍在）。
 */
export function filterMessagesByMode(
  messages: DisplayMessage[],
  mode: TutorMode
): DisplayMessage[] {
  return messages.filter((m) => m.mode === mode)
}

/** 各模式的自我介绍（模式 tab 行下方展示） */
export const MODE_INTRO: Record<TutorMode, string> = {
  socratic: '你提问，它不直接给答案——用一连串追问引导你自己想到答案。适合卡住的时候。',
  feynman: '换你当老师讲给它听——用自己的话解释一个知识点，它按理解度打分。讲明白才算真懂。',
}

/** 费曼讲解要求文案（主题卡展示，与后端原开场白语义一致） */
export const FEYNMAN_REQUIREMENT =
  '用你自己的话讲给我听——假装你在教一个完全不懂编程的人。不许用术语搪塞，讲到他能复述为止。'

/** 活跃费曼主题：存在时提交走 feynman/check，点评后清除 */
export interface ActiveTopic {
  topic: string
  sessionId: string
}

/** 对话区顶部卡片状态：费曼主题卡 + 苏格拉底当前问题卡（按模式各自管理） */
export interface TutorCards {
  activeTopic: ActiveTopic | null
  polishedQuestion: string | null
}

/**
 * 提交完成后更新卡片状态（纯函数）：
 * - 费曼主题卡固定：不随提交/点评清除，只由用户主动「取消主题」或选新主题改变
 * - 苏格拉底模式：仅当尚无问题卡且响应携带润色问题时，固定为「当前问题」卡
 */
export function cardsAfterSubmit(
  cards: TutorCards,
  mode: TutorMode,
  polishedQuestion: string | undefined
): TutorCards {
  const next: TutorCards = { ...cards }
  if (mode === 'socratic' && next.polishedQuestion === null && polishedQuestion) {
    next.polishedQuestion = polishedQuestion
  }
  return next
}

/** 费曼主题卡：固定在对话区顶部，UI 元素而非聊天消息 */
function TopicCard({ topic, onCancel }: { topic: string; onCancel: () => void }) {
  return (
    <div className="deck-panel mx-auto max-w-[560px] p-4">
      <div className="flex items-start justify-between gap-3">
        <PanelTag label="FEYNMAN · 费曼检验" variant="on" />
        <button onClick={onCancel} className="deck-btn-ghost !px-2.5 !py-1 text-[11px]">
          取消主题
        </button>
      </div>
      <p className="mt-2 text-base font-semibold text-text">{topic}</p>
      <p className="mt-1 text-[13px] leading-relaxed text-dim">{FEYNMAN_REQUIREMENT}</p>
    </div>
  )
}

/** 苏格拉底当前问题卡：固定在对话区顶部，本屏首次提问后生成 */
function QuestionCard({ question, onReset }: { question: string; onReset: () => void }) {
  return (
    <div className="deck-panel mx-auto max-w-[560px] p-4">
      <div className="flex items-start justify-between gap-3">
        <PanelTag label="SOCRATES · 当前问题" variant="on" />
        <button onClick={onReset} className="deck-btn-ghost !px-2.5 !py-1 text-[11px]">
          换个问题
        </button>
      </div>
      <p className="mt-2 text-sm leading-relaxed text-text">{question}</p>
    </div>
  )
}

/** 题目上下文卡：从题目页「问导师」跳入时固定展示，导师围绕该题追问 */
function QuestionContextCard({
  ctx,
  onDismiss,
}: {
  ctx: TutorQuestionContext
  onDismiss: () => void
}) {
  return (
    <div className="deck-panel mx-auto max-w-[560px] p-4">
      <div className="flex items-start justify-between gap-3">
        <PanelTag label="SOCRATES · 正在讨论的题" variant="on" />
        <button onClick={onDismiss} className="deck-btn-ghost !px-2.5 !py-1 text-[11px]">
          结束讨论
        </button>
      </div>
      <p className="mt-2 text-sm font-semibold text-text">{ctx.title}</p>
      <pre className="mt-1.5 max-h-32 overflow-auto whitespace-pre-wrap font-mono text-[11px] leading-relaxed text-dim">
        {ctx.content}
      </pre>
    </div>
  )
}

/** 苏格拉底导师：追问模式 + 费曼「考考我」模式 */
export function TutorClient() {
  const { push } = useRouter()
  const searchParams = useSearchParams()
  const [messages, setMessages] = useState<DisplayMessage[]>([])
  const [mode, setMode] = useState<TutorMode>('socratic')
  const [cards, setCards] = useState<TutorCards>({ activeTopic: null, polishedQuestion: null })
  const [questionCtx, setQuestionCtx] = useState<TutorQuestionContext | null>(null)
  const [balance, setBalance] = useState<number | null>(null)
  const [cost, setCost] = useState(2)
  const [topics, setTopics] = useState<string[]>([])
  const [input, setInput] = useState('')
  const [thinking, setThinking] = useState(false)
  const [loaded, setLoaded] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const topicHandled = useRef(false)
  const thinkingTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const { celebrate, celebrationElement } = useBadgeCelebration()

  // 卸载时清理未完成的思考计时器（性能审计修复：避免卸载后 setState）
  useEffect(() => {
    return () => {
      if (thinkingTimerRef.current) clearTimeout(thinkingTimerRef.current)
    }
  }, [])

  useEffect(() => {
    if (!isAuthenticated()) {
      push('/login')
      return
    }
    getTutorState()
      .then((s) => {
        setMessages(s.messages)
        setBalance(s.cores_balance)
        setCost(s.cost_per_question)
        setTopics(s.suggested_topics)
        setLoaded(true)
        // 题目页「问导师」跳入：取出一次性题目上下文，固定为讨论卡
        setQuestionCtx(takeTutorQuestionContext())
        // 从仪表盘「针对训练」跳入：静默创建费曼会话，出主题卡（不产生开场白消息）
        const topic = searchParams.get('topic')
        if (topic && !topicHandled.current) {
          topicHandled.current = true
          setMode('feynman')
          startFeynman(topic)
            .then((r) => {
              setCards((prev) => ({
                ...prev,
                activeTopic: { topic, sessionId: r.feynman_session_id },
              }))
            })
            .catch((e: Error) => {
              setError(e.message || '费曼会话创建失败')
            })
        }
      })
      .catch((e: Error) => {
        setError(e.message || '导师状态加载失败')
        setLoaded(true) // 从 loading 退出，交给错误面板渲染
      })
  }, [push, searchParams])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, thinking])

  // 按当前模式过滤：苏格拉底/费曼各自独立的对话流（渲染与 LLM 历史上下文共用）
  const currentModeMessages = filterMessagesByMode(messages, mode)

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
        ? submitFeynman(cards.activeTopic?.sessionId ?? '', text, balance, cost)
        : sendTutorMessage(
            text,
            mode,
            currentModeMessages.slice(-10).map((m) => ({ role: m.role, text: m.text })),
            balance,
            cost,
            questionCtx
          )

    // 模拟导师思考延迟（timer 存 ref，卸载时统一清理，避免卸载后 setState）
    thinkingTimerRef.current = setTimeout(() => {
      call
        .then((r) => {
          setMessages((prev) => [...prev, { ...r.message, grade: r.grade, mastery: r.mastery_update }])
          setBalance(r.cores_balance)
          setThinking(false)
          celebrate(r.new_badges)
          // 卡片状态：费曼点评后清主题卡；苏格拉底首次提问固定「当前问题」卡
          setCards((prev) => cardsAfterSubmit(prev, mode, r.polished_question))
        })
        .catch(() => {
          // 安全审计修复：请求失败（如后端余额不足 402 / 网络错误）时恢复输入
          setThinking(false)
          setInput(text)
          setMessages((prev) => [...prev, { id: `err-${Date.now()}`, role: 'tutor', mode, text: '请求失败，请稍后重试。' }])
        })
    }, 900)
  }

  const handleTopic = (topic: string) => {
    if (thinking) return
    startFeynman(topic)
      .then((r) => {
        setCards((prev) => ({ ...prev, activeTopic: { topic, sessionId: r.feynman_session_id } }))
      })
      .catch((e: Error) => {
        setError(e.message || '费曼会话创建失败')
      })
  }

  const insufficient = balance !== null && balance < cost

  return (
    <DeckShell>
      {celebrationElement}
      <div className="deck-boot deck-boot-1 flex flex-wrap items-center gap-4">
        <PanelTag label="AI TUTOR" variant="on" />
        {/* 模式切换：在剩余空间内水平居中 */}
        <div className="flex flex-1 justify-center">
          <div className="flex rounded border border-line font-mono text-[11px]">
            {(
              [
                { key: 'socratic', label: '苏格拉底' },
                { key: 'feynman', label: '费曼' },
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
        </div>
        {balance !== null && (
          <span className="rounded border border-line px-2.5 py-1 font-mono text-xs text-dim">
            ◈ {balance} · 每次提问 -{cost}
          </span>
        )}
      </div>

      {/* 当前模式介绍（tab 行下方） */}
      <p className="mt-2.5 text-center font-mono text-[11px] leading-relaxed text-faint">
        {MODE_INTRO[mode]}
      </p>

      {/* 卡片区：苏格拉底问题卡 / 题目上下文卡 / 费曼主题卡（按模式各自显示，消息流上方） */}
      {mode === 'socratic' && questionCtx && (
        <div className="mt-2.5">
          <QuestionContextCard ctx={questionCtx} onDismiss={() => setQuestionCtx(null)} />
        </div>
      )}
      {mode === 'socratic' && cards.polishedQuestion && (
        <div className="mt-2.5">
          <QuestionCard
            question={cards.polishedQuestion}
            onReset={() => setCards((prev) => ({ ...prev, polishedQuestion: null }))}
          />
        </div>
      )}
      {mode === 'feynman' && cards.activeTopic && (
        <div className="mt-2.5">
          <TopicCard
            topic={cards.activeTopic.topic}
            onCancel={() => setCards((prev) => ({ ...prev, activeTopic: null }))}
          />
        </div>
      )}

      {/* 消息流 */}
      <div className="deck-boot deck-boot-2 mt-4 space-y-3">
        {!loaded ? (
          <div className="deck-panel p-8 font-mono text-sm text-dim">
            导师接入中<span className="deck-cursor ml-2" />
          </div>
        ) : (
          <>
            {error && <ErrorPanel message={error} onRetry={() => setError(null)} />}
            {currentModeMessages.map((m) => (
              <MessageBubble key={m.id} msg={m} />
            ))}
            {thinking && (
              <div className="flex justify-start">
                <div className="deck-panel px-4 py-3 font-mono text-xs text-faint">
                  SOCRATES 思考中<span className="deck-cursor ml-2" />
                </div>
              </div>
            )}
            {/* 费曼模式主题 chips：主题卡激活期间隐藏（取消/点评后再出现） */}
            {mode === 'feynman' && topics.length > 0 && !cards.activeTopic && (
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
