import { deckCall } from './client'
import { awardMockBadges, isNightHour } from './mock/badges'
import {
  TUTOR_STATE_MOCK,
  mockStartFeynman,
  mockSubmitFeynman,
  socraticReply,
} from './mock/tutor'
import type { TutorMode, TutorReply, TutorState } from './types'

let seq = 0
function nextId(): string {
  seq += 1
  return `msg-${Date.now()}-${seq}`
}

/** GET /api/tutor/state —— 导师初始状态（余额 + 欢迎消息 + 建议主题） */
export function getTutorState(): Promise<TutorState> {
  return deckCall('/tutor/state', () => TUTOR_STATE_MOCK)
}

/** POST /api/tutor/message —— 发送消息，返回导师追问。余额不足时不扣费并提示 */
export function sendTutorMessage(
  text: string,
  mode: TutorMode,
  historyLen: number,
  balance: number,
  costPerQuestion: number
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
          new_badges: [],
        }
      }
      return {
        message: {
          id: nextId(),
          role: 'tutor' as const,
          mode,
          text: socraticReply(text, historyLen),
        },
        cores_balance: balance - costPerQuestion,
        new_badges: [],
      }
    },
    { method: 'POST', body: JSON.stringify({ text, mode }) }
  )
}

/** POST /api/tutor/feynman —— 开启费曼检验（返回开场追问 + 会话 id） */
export function startFeynman(topic: string): Promise<TutorReply> {
  return deckCall(
    '/tutor/feynman',
    () => {
      const { sessionId, opening } = mockStartFeynman(topic)
      return {
        message: { id: nextId(), role: 'tutor' as const, mode: 'feynman' as const, text: opening },
        cores_balance: TUTOR_STATE_MOCK.cores_balance,
        feynman_session_id: sessionId,
        new_badges: [],
      }
    },
    { method: 'POST', body: JSON.stringify({ topic }) }
  )
}

/** POST /api/tutor/feynman/check —— 提交解释，返回盲区点评 + 评级 + 掌握度变化（扣一次提问费用） */
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
    { method: 'POST', body: JSON.stringify({ session_id: sessionId, text }) }
  )
}
