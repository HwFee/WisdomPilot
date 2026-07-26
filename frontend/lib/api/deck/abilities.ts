import { deckCall } from './client'
import { ABILITY_MAP_MOCK } from './mock/abilities'
import type { AbilityMapDetail } from './types'

/** GET /api/ability-map —— 三轴 + 全量知识点掌握度 */
export function getAbilityMap(): Promise<AbilityMapDetail> {
  return deckCall('/ability-map', () => ABILITY_MAP_MOCK)
}
