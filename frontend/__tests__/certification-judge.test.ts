/**
 * 基本功认证 mock 判分测试
 */
import { judgeExam, placementLevels } from '@/lib/api/deck/mock/certification'

const ALL_RIGHT = [
  { question_id: 'q1', answer: '10' },
  { question_id: 'q2', answer: '悬空指针（值不变但目标已释放）' },
  { question_id: 'q3', answer: '值相等' },
  { question_id: 'q4', answer: '4' },
  { question_id: 'q5', answer: 'int t = *a; *a = *b; *b = t;' },
  { question_id: 'q6', answer: 'if (n == 0) return NULL;' },
]

describe('judgeExam', () => {
  it('全对 → 100 分，通过并发凭证', () => {
    const r = judgeExam('cert-pointer', ALL_RIGHT)
    expect(r.score).toBe(100)
    expect(r.passed).toBe(true)
    expect(r.certificate).not.toBeNull()
    expect(r.certificate!.topic).toBe('指针')
    expect(r.certificate!.level).toBe('精通')
  })

  it('低于通过线 → 不通过、无凭证', () => {
    const r = judgeExam('cert-pointer', ALL_RIGHT.slice(0, 4))
    expect(r.score).toBe(67)
    expect(r.passed).toBe(false)
    expect(r.certificate).toBeNull()
  })

  it('code 题空白差异不影响判定', () => {
    const answers = ALL_RIGHT.map((a) =>
      a.question_id === 'q5' ? { ...a, answer: 'int t=*a;*a=*b;*b=t;' } : a
    )
    expect(judgeExam('cert-pointer', answers).score).toBe(100)
  })

  it('定级测试永远不算 passed，但给分数', () => {
    const r = judgeExam('placement', [])
    expect(r.passed).toBe(false)
    expect(r.score).toBe(0)
  })
})

describe('placementLevels', () => {
  it('分数映射到 1-5 级', () => {
    expect(placementLevels(0).review).toBe(1)
    expect(placementLevels(100).implement).toBe(5)
    expect(placementLevels(40).debug).toBeLessThan(placementLevels(80).debug)
  })
})
