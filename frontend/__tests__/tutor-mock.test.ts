/**
 * 苏格拉底导师 mock 测试：追问路由 + 智核扣费
 * （费曼评分/掌握度/会话绑定见 tutor-feynman.test.ts）
 */
import { socraticReply } from '@/lib/api/deck/mock/tutor'
import { sendTutorMessage } from '@/lib/api/deck/tutor'

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
