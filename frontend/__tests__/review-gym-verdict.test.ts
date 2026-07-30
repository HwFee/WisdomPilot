/**
 * 代码审查室 mock 判定逻辑测试
 */
import { judgeMarks, getMockSession, NEXT_SESSION } from '@/lib/api/deck/mock/review-gym'
import type { InjectedDefect } from '@/lib/api/deck/types'

const DEFECTS: InjectedDefect[] = [
  { line: 6, type: 'boundary', explanation: 'a' },
  { line: 7, type: 'logic', explanation: 'b' },
]

describe('judgeMarks', () => {
  it('全部命中：score 100，无漏报误报', () => {
    const v = judgeMarks(DEFECTS, [
      { line: 6, type: 'boundary' },
      { line: 7, type: 'logic' },
    ])
    expect(v.hits).toHaveLength(2)
    expect(v.missed).toHaveLength(0)
    expect(v.false_alarms).toHaveLength(0)
    expect(v.score).toBe(100)
    expect(v.accuracy).toBe(1)
  })

  it('行号 ±1 容差内算命中', () => {
    const v = judgeMarks(DEFECTS, [
      { line: 5, type: 'boundary' },
      { line: 8, type: 'logic' },
    ])
    expect(v.hits).toHaveLength(2)
  })

  it('类型不符不算命中，记误报 + 漏报', () => {
    const v = judgeMarks(DEFECTS, [{ line: 6, type: 'style' }])
    expect(v.hits).toHaveLength(0)
    expect(v.missed).toHaveLength(2)
    expect(v.false_alarms).toHaveLength(1)
  })

  it('零标注：全漏报，score 30（无误报底分）', () => {
    const v = judgeMarks(DEFECTS, [])
    expect(v.missed).toHaveLength(2)
    expect(v.score).toBe(30)
  })

  it('误报拉低分数与准确率', () => {
    const v = judgeMarks(DEFECTS, [
      { line: 6, type: 'boundary' },
      { line: 7, type: 'logic' },
      { line: 1, type: 'style' },
      { line: 2, type: 'style' },
    ])
    expect(v.false_alarms).toHaveLength(2)
    expect(v.accuracy).toBe(0.5)
    expect(v.score).toBeLessThan(100)
  })
})

describe('getMockSession', () => {
  it('未知 id 回退到默认关，且不泄漏注入缺陷', () => {
    const s = getMockSession('NOPE')
    expect(s.id).toBe('REVIEW-0247')
    expect('injected' in s).toBe(false)
  })

  it('NEXT_SESSION 8 关形成环', () => {
    expect(NEXT_SESSION['REVIEW-0247']).toBe('REVIEW-0248')
    expect(NEXT_SESSION['REVIEW-0248']).toBe('REVIEW-0249')
    expect(NEXT_SESSION['REVIEW-0254']).toBe('REVIEW-0247')
  })
})
