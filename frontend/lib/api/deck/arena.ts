import { deckCall } from './client'
import { ARENA_HOME_MOCK, submitMockArena } from './mock/arena'
import type { ArenaHome, ArenaRunResult } from './types'

/** GET /api/arena/home —— 竞技场首页（状态 + 今日挑战 + 排行榜） */
export function getArenaHome(): Promise<ArenaHome> {
  return deckCall('/arena/home', () => ARENA_HOME_MOCK)
}

/** POST /api/arena/run —— 提交代码判题 */
export function runArenaCode(challengeId: string, code: string): Promise<ArenaRunResult> {
  return deckCall('/arena/run', () => submitMockArena(challengeId, code), {
    method: 'POST',
    body: JSON.stringify({ challenge_id: challengeId, code }),
  })
}
