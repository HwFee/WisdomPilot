import { deckCall } from './client'
import { PROFILE_MOCK } from './mock/profile'
import type { ProfileData } from './types'

/** GET /api/profile —— 档案聚合（身份/智核/竞技场/认证/排行） */
export function getProfile(): Promise<ProfileData> {
  return deckCall('/profile', () => PROFILE_MOCK)
}
