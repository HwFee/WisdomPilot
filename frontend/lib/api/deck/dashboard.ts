import { deckCall } from './client'
import { dashboardMock } from './mock/dashboard'
import type { DeckDashboard } from './types'

/** GET /api/dashboard —— 训练舱首页聚合数据 */
export function getDeckDashboard(): Promise<DeckDashboard> {
  return deckCall('/dashboard', () => dashboardMock)
}
