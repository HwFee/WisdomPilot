/**
 * 复盘队列 mock 聚合逻辑测试
 */
import { buildReviewQueue, REVIEW_QUEUE_MOCK } from '@/lib/api/deck/mock/review'
import type { ReviewQueueItem } from '@/lib/api/deck/types'

const item = (id: string, kind: ReviewQueueItem['kind']): ReviewQueueItem => ({
  id,
  kind,
  title: id,
  detail: '',
  target_url: '/',
  cta_label: '→',
  last_at: '',
})

describe('buildReviewQueue', () => {
  it('按 审查 → 竞技 → 弱知识点 顺序合并', () => {
    const q = buildReviewQueue(
      [item('rg-1', 'review-gym')],
      [item('ar-1', 'arena')],
      [item('kp-1', 'knowledge'), item('kp-2', 'knowledge')]
    )
    expect(q.items.map((i) => i.id)).toEqual(['rg-1', 'ar-1', 'kp-1', 'kp-2'])
    expect(q.total).toBe(4)
  })

  it('空来源：返回空队列', () => {
    const q = buildReviewQueue([], [], [])
    expect(q.items).toHaveLength(0)
    expect(q.total).toBe(0)
  })

  it('total 与 items 长度一致', () => {
    expect(REVIEW_QUEUE_MOCK.total).toBe(REVIEW_QUEUE_MOCK.items.length)
  })

  it('mock 队列每项都有跳转入口', () => {
    for (const i of REVIEW_QUEUE_MOCK.items) {
      expect(i.target_url).toMatch(/^\//)
      expect(i.cta_label).toBeTruthy()
    }
  })
})
