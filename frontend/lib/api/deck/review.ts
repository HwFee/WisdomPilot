import { deckCall } from './client'
import { REVIEW_QUEUE_MOCK } from './mock/review'
import type { ReviewQueue } from './types'

/** GET /api/review/queue —— 复盘队列（错题/失败项聚合） */
export function getReviewQueue(): Promise<ReviewQueue> {
  return deckCall('/review/queue', () => REVIEW_QUEUE_MOCK)
}
