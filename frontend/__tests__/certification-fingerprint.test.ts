/**
 * 训练指纹纯函数测试（§3.5 P-11 路径唯一性标识）
 */
import {
  CERT_HOME_MOCK,
  fingerprintFromPlacement,
  getMockCertHome,
  trainingFingerprint,
} from '@/lib/api/deck/mock/certification'
import type { AbilityAxis } from '@/lib/api/deck/types'

/** 用等级映射构造三轴测试数据（与 AbilityAxis 结构同构） */
const axesOf = (
  levels: Partial<Record<'review' | 'debug' | 'implement', number>>,
): AbilityAxis[] =>
  (['review', 'debug', 'implement'] as const).map((key) => ({
    key,
    label: key,
    level: levels[key] ?? 1,
    xp_current: 0,
    xp_next: 400,
    weakest_focus: null,
  }))

describe('trainingFingerprint', () => {
  it('设计稿示例：审阅 LV.3 / 调试 LV.1 / 实现 LV.4 → R3-D1-I4', () => {
    expect(
      trainingFingerprint(axesOf({ review: 3, debug: 1, implement: 4 })),
    ).toBe('R3-D1-I4')
  })

  it('未定级用户：三轴均 LV.1 → R1-D1-I1', () => {
    expect(trainingFingerprint(axesOf({}))).toBe('R1-D1-I1')
  })

  it('输出顺序固定为 R-D-I，与传入顺序无关', () => {
    const shuffled: AbilityAxis[] = [
      axesOf({ review: 3, debug: 1, implement: 4 })[2],
      axesOf({ review: 3, debug: 1, implement: 4 })[0],
      axesOf({ review: 3, debug: 1, implement: 4 })[1],
    ]
    expect(trainingFingerprint(shuffled)).toBe('R3-D1-I4')
  })

  it('缺失轴按 LV.1 兜底', () => {
    const partial = axesOf({ review: 3, implement: 4 }).filter(
      (a) => a.key !== 'debug',
    )
    expect(trainingFingerprint(partial)).toBe('R3-D1-I4')
  })
})

describe('fingerprintFromPlacement', () => {
  it('定级三轴等级 → 指纹短码（固定 R-D-I 顺序）', () => {
    expect(fingerprintFromPlacement({ review: 3, debug: 1, implement: 4 })).toBe('R3-D1-I4')
  })

  it('全轴 LV.1 → R1-D1-I1', () => {
    expect(fingerprintFromPlacement({ review: 1, debug: 1, implement: 1 })).toBe('R1-D1-I1')
  })

  it('与 trainingFingerprint 对同一等级数据输出一致（同源）', () => {
    const levels = { review: 3, debug: 1, implement: 4 }
    expect(fingerprintFromPlacement(levels)).toBe(trainingFingerprint(axesOf(levels)))
  })
})

describe('CERT_HOME_MOCK 指纹字段', () => {
  it('home 响应带 fingerprint，格式为「R{x}-D{x}-I{x}」', () => {
    expect(CERT_HOME_MOCK.fingerprint).toMatch(/^R\d-D\d-I\d$/)
    expect(getMockCertHome().fingerprint).toBe(CERT_HOME_MOCK.fingerprint)
  })
})
