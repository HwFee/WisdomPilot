/**
 * 苏格拉底导师 mock 测试：追问路由 + 智核扣费
 * （费曼评分/掌握度/会话绑定见 tutor-feynman.test.ts）
 */
import { socraticReply } from '@/lib/api/deck/mock/tutor'
import {
  askTutorAboutQuestion,
  sendTutorMessage,
  takeTutorQuestionContext,
} from '@/lib/api/deck/tutor'

describe('socraticReply', () => {
  it('命中关键词返回定向追问', () => {
    expect(socraticReply('我不懂指针', 0)).toContain('free')
    expect(socraticReply('递归怎么回事', 0)).toContain('调用栈')
  })

  it('无关键词按轮数轮转通用追问', () => {
    expect(socraticReply('嗯', 0)).not.toBe(socraticReply('嗯', 1))
  })
})

describe('sendTutorMessage 智核扣费', () => {
  it('余额充足：扣费并返回追问', async () => {
    const r = await sendTutorMessage('讲讲递归', 'socratic', [], 86, 2)
    expect(r.cores_balance).toBe(84)
    expect(r.message.role).toBe('tutor')
  })

  it('余额不足：不扣费，返回提示', async () => {
    const r = await sendTutorMessage('讲讲递归', 'socratic', [], 1, 2)
    expect(r.cores_balance).toBe(1)
    expect(r.message.text).toContain('智核余额不足')
  })

  it('携带的历史条数驱动通用追问轮换（语义与后端一致）', async () => {
    const history = [
      { role: 'user' as const, text: '你好' },
      { role: 'tutor' as const, text: '什么问题？' },
    ]
    const r = await sendTutorMessage('嗯', 'socratic', history, 86, 2)
    // 「嗯」无关键词 → 按 len(history)=2 轮换通用追问
    expect(r.message.text).toBe(socraticReply('嗯', 2))
  })

  it('polished_question：mock 回原文（真后端 LLM 润色，降级语义一致）', async () => {
    const r = await sendTutorMessage('我传指针进去改不动外面的变量', 'socratic', [], 86, 2)
    expect(r.polished_question).toBe('我传指针进去改不动外面的变量')
  })
})

describe('题目上下文', () => {
  it('携带题目上下文：mock 追问带题目前缀（演示上下文效果）', async () => {
    const r = await sendTutorMessage('嗯', 'socratic', [], 86, 2, {
      source: 'arena',
      title: '旋转数组',
      content: 'def rotate(nums, k): ...',
    })
    expect(r.message.text).toContain('《旋转数组》')
    expect(r.cores_balance).toBe(84) // 扣费语义不变
  })

  it('不带题目上下文：回复与原有一致', async () => {
    const r = await sendTutorMessage('嗯', 'socratic', [], 86, 2)
    expect(r.message.text).toBe(socraticReply('嗯', 0))
  })

  it('余额不足路径不受题目上下文影响', async () => {
    const r = await sendTutorMessage('这题怎么改', 'socratic', [], 1, 2, {
      source: 'arena',
      title: '旋转数组',
      content: 'x',
    })
    expect(r.message.text).toContain('智核余额不足')
    expect(r.cores_balance).toBe(1)
  })
})

describe('题目上下文一次性交接（sessionStorage）', () => {
  it('askTutorAboutQuestion → takeTutorQuestionContext 一次性消费', () => {
    askTutorAboutQuestion({ source: 'arena', title: '旋转数组', content: 'code' })
    expect(takeTutorQuestionContext()).toEqual({
      source: 'arena',
      title: '旋转数组',
      content: 'code',
    })
    // 第二次读取：已清除，避免陈旧上下文残留
    expect(takeTutorQuestionContext()).toBeNull()
  })

  it('无上下文时返回 null', () => {
    expect(takeTutorQuestionContext()).toBeNull()
  })

  it('坏 JSON / 缺字段返回 null', () => {
    sessionStorage.setItem('deck:tutor_question_context', 'not-json')
    expect(takeTutorQuestionContext()).toBeNull()
    sessionStorage.setItem('deck:tutor_question_context', '{"source":"arena"}')
    expect(takeTutorQuestionContext()).toBeNull()
  })
})
