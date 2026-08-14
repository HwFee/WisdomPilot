import { deckCall, LLM_TIMEOUT_MS } from './client'
import { awardMockBadges, isNightHour } from './mock/badges'
import {
  TUTOR_STATE_MOCK,
  mockStartFeynman,
  mockSubmitFeynman,
  socraticReply,
} from './mock/tutor'
import type { TutorMode, TutorQuestionContext, TutorReply, TutorState } from './types'

/** 题目上下文一次性交接键：题目页写入、导师页读取并清除 */
const QUESTION_CONTEXT_KEY = 'deck:tutor_question_context'

/** 题目页「问导师」入口：把题目上下文写入 sessionStorage，随后跳转到导师页 */
export function askTutorAboutQuestion(ctx: TutorQuestionContext): void {
  if (typeof window !== 'undefined') {
    sessionStorage.setItem(QUESTION_CONTEXT_KEY, JSON.stringify(ctx))
  }
}

/** 导师页挂载时读取并清除题目上下文（一次性消费，避免陈旧上下文残留到后续会话） */
export function takeTutorQuestionContext(): TutorQuestionContext | null {
  if (typeof window === 'undefined') return null
  const raw = sessionStorage.getItem(QUESTION_CONTEXT_KEY)
  if (!raw) return null
  sessionStorage.removeItem(QUESTION_CONTEXT_KEY)
  try {
    const parsed = JSON.parse(raw) as Partial<TutorQuestionContext>
    if (
      typeof parsed.source !== 'string' ||
      typeof parsed.title !== 'string' ||
      typeof parsed.content !== 'string'
    ) {
      return null
    }
    return { source: parsed.source, title: parsed.title, content: parsed.content }
  } catch {
    return null
  }
}

let seq = 0
function nextId(): string {
  seq += 1
  return `msg-${Date.now()}-${seq}`
}

/** GET /api/tutor/state —— 导师初始状态（余额 + 欢迎消息 + 建议主题） */
export function getTutorState(): Promise<TutorState> {
  return deckCall('/tutor/state', () => TUTOR_STATE_MOCK)
}

/** 导师对话历史项：随 sendTutorMessage 请求携带（会话不持久化，后端注入 LLM 上下文） */
export interface TutorHistoryItem {
  role: string
  text: string
}

/** POST /api/tutor/message —— 发送消息，返回导师追问。余额不足时不扣费并提示。
 *  questionContext：学生正在询问的题目（来自题目页「问导师」入口），随请求携带注入导师 prompt。
 *  安全审计修复：后端 tutor 端点串行两次 LLM 调用（各 3 重试 × 60s+退避），
 *  最坏 ~366s。用 300s 超时，避免前端提前 abort 后后端仍在烧 LLM 费用。 */
export function sendTutorMessage(
  text: string,
  mode: TutorMode,
  history: TutorHistoryItem[],
  balance: number,
  costPerQuestion: number,
  questionContext?: TutorQuestionContext | null
): Promise<TutorReply> {
  return deckCall(
    '/tutor/message',
    () => {
      if (balance < costPerQuestion) {
        return {
          message: {
            id: nextId(),
            role: 'tutor' as const,
            mode,
            text: '你的智核余额不足了。去基本功认证通过一场考试，或者明天再来——每日登录会补充 5 智核。',
          },
          cores_balance: balance,
          // mock 直接回原文（真后端会走 LLM 润色，未配置/异常同样降级回原文）
          polished_question: text,
          new_badges: [],
        }
      }
      return {
        message: {
          id: nextId(),
          role: 'tutor' as const,
          mode,
          // mock 演示题目上下文效果：带上题目标题前缀（真后端由 LLM 围绕题目追问）
          text: questionContext
            ? `就着《${questionContext.title}》——${socraticReply(text, history.length)}`
            : socraticReply(text, history.length),
        },
        cores_balance: balance - costPerQuestion,
        // mock 直接回原文（真后端会走 LLM 润色，未配置/异常同样降级回原文）
        polished_question: text,
        new_badges: [],
      }
    },
    {
      method: 'POST',
      body: JSON.stringify({
        text,
        mode,
        history,
        question_context: questionContext ?? undefined,
      }),
    },
    LLM_TIMEOUT_MS
  )
}

/** POST /api/tutor/feynman —— 静默创建费曼会话，仅返回会话 id（开场白由前端主题卡呈现） */
export interface FeynmanStartResult {
  feynman_session_id: string
  cores_balance: number
}

export function startFeynman(topic: string): Promise<FeynmanStartResult> {
  return deckCall(
    '/tutor/feynman',
    () => {
      const { sessionId } = mockStartFeynman(topic)
      return { feynman_session_id: sessionId, cores_balance: TUTOR_STATE_MOCK.cores_balance }
    },
    { method: 'POST', body: JSON.stringify({ topic }) }
  )
}

/** POST /api/tutor/feynman/check —— 提交解释，返回盲区点评 + 评级 + 掌握度变化（扣一次提问费用）
 *  安全审计修复：同 sendTutorMessage，费曼评分走 LLM，用长超时避免前端 abort 后后端仍在烧费用。 */
export function submitFeynman(
  sessionId: string,
  text: string,
  balance: number,
  costPerQuestion: number
): Promise<TutorReply> {
  return deckCall(
    '/tutor/feynman/check',
    () => {
      const { verdict, grade, mastery } = mockSubmitFeynman(sessionId, text)
      const new_badges = awardMockBadges({ feynmanGrade: grade, isNight: isNightHour() })
      return {
        message: { id: nextId(), role: 'tutor' as const, mode: 'feynman' as const, text: verdict },
        cores_balance: Math.max(0, balance - costPerQuestion),
        grade,
        mastery_update: mastery,
        new_badges,
      }
    },
    { method: 'POST', body: JSON.stringify({ session_id: sessionId, text }) },
    LLM_TIMEOUT_MS
  )
}
