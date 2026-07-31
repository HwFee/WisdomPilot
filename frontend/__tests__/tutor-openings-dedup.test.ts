/**
 * 导师页纯函数测试：按模式过滤消息流 + 卡片状态（主题卡/当前问题卡）
 */
import {
  cardsAfterSubmit,
  filterMessagesByMode,
  MODE_INTRO,
  type ActiveTopic,
} from '@/components/tutor/TutorClient'
import type { TutorMessage } from '@/lib/api/deck/types'

describe('filterMessagesByMode 按模式过滤消息流', () => {
  const socraticUser: TutorMessage = { id: 'su', role: 'user', mode: 'socratic', text: '我不懂指针' }
  const socraticTutor: TutorMessage = { id: 'st', role: 'tutor', mode: 'socratic', text: '追问' }
  const feynmanUser: TutorMessage = { id: 'fu', role: 'user', mode: 'feynman', text: '我来讲讲指针' }
  const feynmanTutor: TutorMessage = { id: 'ft', role: 'tutor', mode: 'feynman', text: '点评' }
  const mixed = [socraticUser, feynmanUser, socraticTutor, feynmanTutor]

  it('只保留对应 mode 的消息，两种模式互不串扰', () => {
    expect(filterMessagesByMode(mixed, 'socratic').map((m) => m.id)).toEqual(['su', 'st'])
    expect(filterMessagesByMode(mixed, 'feynman').map((m) => m.id)).toEqual(['fu', 'ft'])
  })

  it('空列表安全', () => {
    expect(filterMessagesByMode([], 'socratic')).toEqual([])
    expect(filterMessagesByMode([], 'feynman')).toEqual([])
  })

  it('用户/导师消息都按 mode 归属', () => {
    const socraticOnly = filterMessagesByMode(mixed, 'socratic')
    expect(socraticOnly.map((m) => m.mode)).toEqual(['socratic', 'socratic'])
    expect(socraticOnly.map((m) => m.role)).toEqual(['user', 'tutor'])
    const feynmanOnly = filterMessagesByMode(mixed, 'feynman')
    expect(feynmanOnly.map((m) => m.mode)).toEqual(['feynman', 'feynman'])
    expect(feynmanOnly.map((m) => m.role)).toEqual(['user', 'tutor'])
  })
})

describe('MODE_INTRO 模式介绍文案', () => {
  it('两个模式都有非空介绍', () => {
    for (const mode of ['socratic', 'feynman'] as const) {
      expect(MODE_INTRO[mode].length).toBeGreaterThan(0)
    }
  })

  it('文案区分两种模式定位（不互相重复）', () => {
    expect(MODE_INTRO.socratic).not.toBe(MODE_INTRO.feynman)
    // 类型覆盖：Record<TutorMode, string> 必须同时覆盖两个 key
    const keys = Object.keys(MODE_INTRO).sort()
    expect(keys).toEqual(['feynman', 'socratic'])
  })
})

describe('cardsAfterSubmit 提交后卡片状态', () => {
  const topic: ActiveTopic = { topic: '指针的内存布局', sessionId: 's1' }

  it('费曼提交后：主题卡保留（固定，直到用户取消或换新主题）', () => {
    const before = { activeTopic: topic, polishedQuestion: null }
    const after = cardsAfterSubmit(before, 'feynman', undefined)
    expect(after.activeTopic).toEqual(topic)
    expect(after.polishedQuestion).toBeNull()
  })

  it('苏格拉底首次提交：无问题卡且有润色问题 → 固定为当前问题卡', () => {
    const before = { activeTopic: null, polishedQuestion: null }
    const after = cardsAfterSubmit(before, 'socratic', '为什么 free 之后指针还能用？')
    expect(after.polishedQuestion).toBe('为什么 free 之后指针还能用？')
  })

  it('苏格拉底已有问题卡：后续提交不再更新（卡片固定）', () => {
    const before = { activeTopic: null, polishedQuestion: '为什么 free 之后指针还能用？' }
    const after = cardsAfterSubmit(before, 'socratic', '新的润色问题')
    expect(after.polishedQuestion).toBe('为什么 free 之后指针还能用？')
  })

  it('苏格拉底无润色问题（余额不足等）：不生成问题卡', () => {
    const before = { activeTopic: null, polishedQuestion: null }
    const after = cardsAfterSubmit(before, 'socratic', undefined)
    expect(after.polishedQuestion).toBeNull()
  })

  it('费曼提交不清问题卡、苏格拉底提交不清主题卡（两条流独立）', () => {
    const withQuestion = { activeTopic: null, polishedQuestion: 'Q1' }
    expect(cardsAfterSubmit(withQuestion, 'feynman', undefined).polishedQuestion).toBe('Q1')
    const withTopic = { activeTopic: topic, polishedQuestion: null }
    expect(cardsAfterSubmit(withTopic, 'socratic', 'Q2').activeTopic).toEqual(topic)
  })
})
