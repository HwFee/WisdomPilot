/**
 * P-10 能力演化对比测试：computeShapeDeltas + 能力图谱 mock 的定级快照自洽性。
 */
import { ABILITY_MAP_MOCK, computeShapeDeltas } from '@/lib/api/deck/mock/abilities'
import { placementLevels } from '@/lib/api/deck/mock/certification'
import type { AbilityAxis, PlacementSnapshot } from '@/lib/api/deck/types'

const PLACEMENT: PlacementSnapshot = {
  score: 60,
  date: '2026-03-14',
  // 与后端 §8 同源：score 60 → base=3，debug 恒低一档 → LV.2
  levels: { review: 3, debug: 2, implement: 3 },
  fingerprint: 'R3-D2-I3',
}

function axis(key: 'review' | 'debug' | 'implement', level: number): AbilityAxis {
  return { key, label: key, level, xp_current: 0, xp_next: 400, weakest_focus: null }
}

describe('computeShapeDeltas', () => {
  it('成长轴 delta 为正、持平轴 delta 为 0，顺序固定 review→debug→implement', () => {
    const deltas = computeShapeDeltas(PLACEMENT, [
      axis('review', 4),
      axis('debug', 3),
      axis('implement', 5),
    ])
    expect(deltas).toHaveLength(3)
    expect(deltas.map((d) => d.axis)).toEqual(['review', 'debug', 'implement'])
    expect(deltas[0]).toMatchObject({ from_level: 3, to_level: 4, delta: 1 })
    expect(deltas[1]).toMatchObject({ from_level: 2, to_level: 3, delta: 1 })
    expect(deltas[2]).toMatchObject({ from_level: 3, to_level: 5, delta: 2 })
  })

  it('当前轴缺失时回退到定级等级（delta 0），不产生退化', () => {
    const deltas = computeShapeDeltas(PLACEMENT, [])
    expect(deltas.every((d) => d.delta === 0)).toBe(true)
    // 回退到各自定级等级（review 3 / debug 2 / implement 3）
    expect(deltas.map((d) => d.to_level)).toEqual([3, 2, 3])
  })

  it('退化轴 delta 为负', () => {
    const deltas = computeShapeDeltas(PLACEMENT, [
      axis('review', 1),
      axis('debug', 3),
      axis('implement', 3),
    ])
    expect(deltas[0].delta).toBe(-2)
    expect(deltas[1]).toMatchObject({ from_level: 2, to_level: 3, delta: 1 })
  })

  it('mock 数据自洽：定级等级与 placementLevels(60) 同源且当前无退化', () => {
    const placement = ABILITY_MAP_MOCK.placement
    expect(placement).not.toBeNull()
    if (!placement) return
    // 快照等级 = 定级结果视图同源的 placementLevels 推导
    expect(placement.levels).toEqual(placementLevels(placement.score))
    // 当前三轴没有比定级时更低的轴（成长叙事一致）
    const deltas = computeShapeDeltas(placement, ABILITY_MAP_MOCK.axes)
    expect(deltas.every((d) => d.delta >= 0)).toBe(true)
  })
})
