/* 复盘 mock：错题/失败项聚合的参考实现（真实后端由 attempts + 掌握度表聚合） */

import type { ReviewQueue, ReviewQueueItem } from '../types'

/**
 * 由三类来源构建复盘队列（纯函数，顺序即展示顺序）：
 * 审查漏报 → 竞技未攻克 → 弱知识点。
 */
export function buildReviewQueue(
  reviewItems: ReviewQueueItem[],
  arenaItems: ReviewQueueItem[],
  knowledgeItems: ReviewQueueItem[]
): ReviewQueue {
  const items = [...reviewItems, ...arenaItems, ...knowledgeItems]
  return { items, total: items.length }
}

export const REVIEW_QUEUE_MOCK: ReviewQueue = buildReviewQueue(
  [
    {
      id: 'rg-REVIEW-0248',
      kind: 'review-gym',
      title: '重审 REVIEW-0248 · 链表反转',
      detail: '漏报 2 处 · 误报 1 处',
      target_url: '/review-gym?session=REVIEW-0248',
      cta_label: '重新审查 →',
      last_at: '昨天',
    },
  ],
  [
    {
      id: 'ar-DEBUG-0091',
      kind: 'arena',
      title: '再战 DEBUG-0091 · 中位数统计',
      detail: '尚未让测试全部变绿',
      target_url: '/arena',
      cta_label: '继续调试 →',
      last_at: '今天 10:12',
    },
  ],
  [
    {
      id: 'kp-递归出口设计',
      kind: 'knowledge',
      title: '费曼检验 · 递归出口设计',
      detail: '掌握度 42%',
      target_url: '/tutor?topic=%E9%80%92%E5%BD%92%E5%87%BA%E5%8F%A3%E8%AE%BE%E8%AE%A1',
      cta_label: '去讲清楚 →',
      last_at: '',
    },
    {
      id: 'kp-边界条件处理',
      kind: 'knowledge',
      title: '费曼检验 · 边界条件处理',
      detail: '掌握度 55%',
      target_url: '/tutor?topic=%E8%BE%B9%E7%95%8C%E6%9D%A1%E4%BB%B6%E5%A4%84%E7%90%86',
      cta_label: '去讲清楚 →',
      last_at: '',
    },
  ]
)
