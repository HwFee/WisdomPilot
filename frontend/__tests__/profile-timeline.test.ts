/**
 * P-09 训练轨迹时间线测试：mock 生成逻辑（buildTimelineMock）的契约与自洽性。
 */
import { buildTimelineMock } from '@/lib/api/deck/mock/profile'
import { placementLevels } from '@/lib/api/deck/mock/certification'
import type { TimelineEntry } from '@/lib/api/deck/types'

describe('buildTimelineMock', () => {
  it('包含全部四类节点', () => {
    const types = buildTimelineMock().map((e) => e.type)
    expect(types).toContain('placement')
    expect(types).toContain('axis_upgrade')
    expect(types).toContain('mastery')
    expect(types).toContain('cert')
  })

  it('按日期升序排列，定级是第一个节点', () => {
    const timeline = buildTimelineMock()
    expect(timeline.length).toBeGreaterThan(1)
    expect(timeline[0].type).toBe('placement')
    const dates = timeline.map((e) => e.date)
    expect([...dates].sort()).toEqual(dates)
  })

  it('placement 节点带分数/三轴等级/指纹', () => {
    const first = buildTimelineMock()[0]
    expect(first.type).toBe('placement')
    if (first.type === 'placement') {
      expect(first.score).toBeGreaterThan(0)
      expect(first.fingerprint).toMatch(/^R\d-D\d-I\d$/)
      expect(Object.values(first.levels)).toHaveLength(3)
    }
  })

  it('placement 节点与 placementLevels(score) 同源（后端 §8：debug 恒低一档）', () => {
    const first = buildTimelineMock()[0]
    expect(first.type).toBe('placement')
    if (first.type === 'placement') {
      expect(first.levels).toEqual(placementLevels(first.score))
      // 与 abilities mock（P-10 画像）同口径
      expect(first.fingerprint).toMatch(/^R3-D2-I3$/)
    }
  })

  it('轴升级节点等级严格递增', () => {
    buildTimelineMock()
      .filter((e) => e.type === 'axis_upgrade')
      .forEach((e) => {
        if (e.type === 'axis_upgrade') {
          expect(e.to_level).toBeGreaterThan(e.from_level)
          expect(['review', 'debug', 'implement']).toContain(e.axis)
        }
      })
  })

  it('每次调用返回独立数组（防外部误改共享常量）', () => {
    const a = buildTimelineMock()
    const b = buildTimelineMock()
    expect(a).not.toBe(b)
    expect(a).toEqual(b)
    a.pop()
    expect(buildTimelineMock()).toHaveLength(b.length)
  })

  it('mastery 节点只含熟练/精通里程碑', () => {
    buildTimelineMock()
      .filter((e) => e.type === 'mastery')
      .forEach((e) => {
        if (e.type === 'mastery') {
          expect(['熟练', '精通']).toContain(e.level)
        }
      })
  })
})
