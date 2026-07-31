/**
 * Dashboard 个性化链路 mock 纯函数测试（§3.5 P-01 推荐理由 / P-04 弱点来源 / P-02 能力指纹）
 */
import {
  axisXpProgress,
  dashboardFingerprint,
  dashboardMock,
  describeTaskReason,
  describeWeakSource,
  orderFingerprintAxes,
  weakPointSource,
} from '@/lib/api/deck/mock/dashboard'
import type { AbilityAxis } from '@/lib/api/deck/types'

// 与 dashboardMock 三轴同构的测试数据（review 最低）
const axes: AbilityAxis[] = [
  { key: 'review', label: '审阅', level: 2, xp_current: 0, xp_next: 400, weakest_focus: '边界条件处理' },
  { key: 'debug', label: '调试', level: 4, xp_current: 0, xp_next: 400, weakest_focus: '指针的内存布局' },
  { key: 'implement', label: '实现', level: 3, xp_current: 0, xp_next: 400, weakest_focus: '递归出口设计' },
]

describe('describeWeakSource', () => {
  it('审查：漏报 / 命中', () => {
    expect(describeWeakSource('review_gym', false)).toBe('审查漏报')
    expect(describeWeakSource('review_gym', true)).toBe('审查命中')
  })

  it('竞技场：失败 / 攻克', () => {
    expect(describeWeakSource('arena', false)).toBe('竞技场失败')
    expect(describeWeakSource('arena', true)).toBe('竞技场攻克')
  })

  it('费曼：待加强 / 通过', () => {
    expect(describeWeakSource('feynman', false)).toBe('费曼待加强')
    expect(describeWeakSource('feynman', true)).toBe('费曼检验')
  })

  it('未知来源兜底', () => {
    expect(describeWeakSource('unknown', false)).toBe('练习记录')
  })
})

describe('weakPointSource', () => {
  it('拼接时间标签与来源短语', () => {
    expect(weakPointSource('3天前', 'review_gym', false)).toBe('3天前 · 审查漏报')
  })
})

describe('describeTaskReason', () => {
  it('主任务：最低轴 + 关联弱点', () => {
    const reason = describeTaskReason(axes, 'review-gym', '边界条件处理', true)
    expect(reason).toContain('「审阅」轴是三轴最低（LV.2）')
    expect(reason).toContain('这一关专攻「边界条件处理」')
  })

  it('备用任务：当前 LV 措辞', () => {
    const reason = describeTaskReason(axes, 'tutor', '递归出口设计', false)
    expect(reason).toContain('「实现」轴当前 LV.3')
  })

  it('无关联弱点时回退轴 weakest_focus', () => {
    const reason = describeTaskReason(axes, 'arena', null, true)
    expect(reason).toContain('「调试」轴是三轴最低（LV.4）')
    expect(reason).toContain('「指针的内存布局」')
  })
})

describe('dashboardMock 个性化字段', () => {
  it('main_task 与全部备选任务都带 reason', () => {
    expect(dashboardMock.main_task).not.toBeNull()
    expect(dashboardMock.main_task!.reason).toBeTruthy()
    for (const alt of dashboardMock.main_task!.alternates) {
      expect(alt.reason).toBeTruthy()
    }
  })

  it('weak_points 每项带 source 且格式为「时间 · 来源」', () => {
    expect(dashboardMock.weak_points.length).toBeGreaterThan(0)
    for (const w of dashboardMock.weak_points) {
      expect(w.source).toMatch(/^.+ · .+$/)
    }
  })
})

describe('orderFingerprintAxes', () => {
  it('按固定 R-D-I 顺序重排，与传入顺序无关', () => {
    const shuffled = [axes[2], axes[0], axes[1]] // implement / review / debug
    expect(orderFingerprintAxes(shuffled).map((a) => a.key)).toEqual(['review', 'debug', 'implement'])
  })

  it('缺失轴不补位、原样保留其余轴', () => {
    const partial = axes.filter((a) => a.key !== 'debug')
    expect(orderFingerprintAxes(partial).map((a) => a.key)).toEqual(['review', 'implement'])
  })
})

describe('axisXpProgress', () => {
  it('xp_current / xp_next 比例', () => {
    expect(axisXpProgress({ ...axes[0], xp_current: 100, xp_next: 400 })).toBeCloseTo(0.25)
  })

  it('超过 100% 时夹取到 1', () => {
    expect(axisXpProgress({ ...axes[0], xp_current: 500, xp_next: 400 })).toBe(1)
  })

  it('xp_next 为 0 时防除零返回 0', () => {
    expect(axisXpProgress({ ...axes[0], xp_current: 100, xp_next: 0 })).toBe(0)
  })
})

describe('dashboardFingerprint', () => {
  it('三轴等级 → R-D-I 短码（与认证域 P-11 同源）', () => {
    expect(dashboardFingerprint(orderFingerprintAxes(axes))).toBe('R2-D4-I3')
  })
})
