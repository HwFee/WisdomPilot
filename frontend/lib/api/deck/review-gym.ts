import { deckCall } from './client'
import { getMockSession, submitMockReview } from './mock/review-gym'
import type { ReviewMark, ReviewSession, ReviewVerdict } from './types'

/** GET /api/review-gym/session?id=—— 获取一关审查会话 */
export function getReviewSession(id?: string): Promise<ReviewSession> {
  return deckCall(`/review-gym/session${id ? `?id=${encodeURIComponent(id)}` : ''}`, () =>
    getMockSession(id)
  )
}

/** POST /api/review-gym/submit —— 提交标注，返回判定结果 */
export function submitReview(id: string, marks: ReviewMark[]): Promise<ReviewVerdict> {
  return deckCall('/review-gym/submit', () => submitMockReview(id, marks), {
    method: 'POST',
    body: JSON.stringify({ session_id: id, marks }),
  })
}
