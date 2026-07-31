/**
 * 缺陷类型元数据完整性测试：五类齐全、description 非空、defectMeta 查询行为。
 */
import { DEFECT_TYPES, defectMeta } from '@/components/review-gym/defect-meta'
import type { DefectType } from '@/lib/api/deck/types'

describe('DEFECT_TYPES', () => {
  it('type 唯一且包含全部 5 类缺陷', () => {
    const types = DEFECT_TYPES.map((d) => d.type)
    expect(new Set(types).size).toBe(types.length)
    for (const t of ['logic', 'boundary', 'performance', 'style', 'security'] as DefectType[]) {
      expect(types).toContain(t)
    }
  })

  it('每条都有非空 label 与 description', () => {
    for (const d of DEFECT_TYPES) {
      expect(d.label.trim().length).toBeGreaterThan(0)
      expect(d.description.trim().length).toBeGreaterThan(0)
    }
  })
})

describe('defectMeta', () => {
  it('命中已知类型', () => {
    expect(defectMeta('security')).toMatchObject({ type: 'security', label: '安全风险' })
    expect(defectMeta('logic').description.length).toBeGreaterThan(0)
  })

  it('未知类型回退默认（第一项）', () => {
    expect(defectMeta('nope' as DefectType).type).toBe(DEFECT_TYPES[0].type)
  })
})
