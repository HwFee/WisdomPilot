/**
 * 费曼「考考我」mock 测试：量规评分 + 掌握度更新 + 会话绑定
 */
import {
  GENERIC_KEY_POINTS,
  KP_KEY_POINTS,
  feynmanVerdict,
  masteryLevel,
  mockMasteryUpdate,
  mockStartFeynman,
  mockSubmitFeynman,
} from '@/lib/api/deck/mock/tutor'
import type { FeynmanKeyPoint } from '@/lib/api/deck/mock/tutor'

const KP4: FeynmanKeyPoint[] = [
  { label: '甲', keys: ['甲'] },
  { label: '乙', keys: ['乙'] },
  { label: '丙', keys: ['丙'] },
  { label: '丁', keys: ['丁'] },
]

describe('feynmanVerdict 量规评级', () => {
  it('全覆盖 + 因果结构 → 优秀，无漏项', () => {
    const v = feynmanVerdict('甲乙丙丁，因为它们环环相扣', KP4)
    expect(v.grade).toBe('优秀')
    expect(v.covered).toEqual(['甲', '乙', '丙', '丁'])
    expect(v.missed).toEqual([])
  })

  it('全覆盖但无因果/举例结构 → 良好，提示缺结构', () => {
    const v = feynmanVerdict('甲乙丙丁', KP4)
    expect(v.grade).toBe('良好')
    expect(v.verdict).toContain('通篇')
  })

  it('覆盖 ≥50% → 良好，点评点名漏掉的关键点', () => {
    const v = feynmanVerdict('甲和乙', KP4)
    expect(v.grade).toBe('良好')
    expect(v.missed).toEqual(['丙', '丁'])
    expect(v.verdict).toContain('丙')
    expect(v.verdict).toContain('丁')
  })

  it('覆盖 1/3 且有结构 → 良好（结构加成）', () => {
    const v = feynmanVerdict('甲，因为如此', KP4.slice(0, 3))
    expect(v.grade).toBe('良好')
  })

  it('覆盖 <1/3 即便有结构 → 待加强', () => {
    const v = feynmanVerdict('甲，因为如此', KP4)
    expect(v.grade).toBe('待加强')
    expect(v.verdict).toContain('乙')
  })

  it('同义关键词命中任一即算覆盖', () => {
    const kp: FeynmanKeyPoint[] = [{ label: '指针存的是地址', keys: ['地址', '指向'] }]
    expect(feynmanVerdict('它指向一块内存', kp).covered).toEqual(['指针存的是地址'])
  })
})

describe('mockMasteryUpdate 掌握度更新', () => {
  it('按评级确定性增减：优秀 +0.15 / 良好 +0.05 / 待加强 -0.05', () => {
    expect(mockMasteryUpdate('递归出口设计', '优秀', 0.5).p_l_after).toBeCloseTo(0.65)
    expect(mockMasteryUpdate('递归出口设计', '良好', 0.5).p_l_after).toBeCloseTo(0.55)
    expect(mockMasteryUpdate('递归出口设计', '待加强', 0.5).p_l_after).toBeCloseTo(0.45)
  })

  it('结果夹取在 0..1', () => {
    expect(mockMasteryUpdate('k', '优秀', 0.95).p_l_after).toBe(1)
    expect(mockMasteryUpdate('k', '待加强', 0.02).p_l_after).toBe(0)
  })

  it('level 由 p_l_after 阈值推导', () => {
    expect(masteryLevel(0.29)).toBe('初识')
    expect(masteryLevel(0.3)).toBe('熟悉')
    expect(masteryLevel(0.6)).toBe('熟练')
    expect(masteryLevel(0.8)).toBe('精通')
    const u = mockMasteryUpdate('k', '良好', 0.76)
    expect(u.p_l_after).toBeCloseTo(0.81)
    expect(u.level).toBe('精通')
  })

  it('保留 kp_name 与 p_l_before', () => {
    const u = mockMasteryUpdate('指针的内存布局', '良好', 0.55)
    expect(u.kp_name).toBe('指针的内存布局')
    expect(u.p_l_before).toBe(0.55)
  })
})

describe('费曼会话绑定', () => {
  it('start 返回会话 id（开场白由前端主题卡呈现，不再返回 opening）', () => {
    const { sessionId } = mockStartFeynman('递归出口设计')
    expect(sessionId).toMatch(/^feynman-/)
  })

  it('start → submit 解析出该主题的量规与掌握度', () => {
    const { sessionId } = mockStartFeynman('递归出口设计')
    const r = mockSubmitFeynman(sessionId, '递归需要出口条件，因为没有出口会无限递归导致栈溢出')
    // 「出口」「栈溢出/无限」命中 2/4 → 良好，漏项点名递归量规
    expect(r.grade).toBe('良好')
    expect(r.verdict).toContain('每轮向出口收敛')
    expect(r.mastery.kp_name).toBe('递归出口设计')
    // 当前掌握度取自能力图谱 mock（递归出口设计 p_l 0.61）
    expect(r.mastery.p_l_before).toBe(0.61)
    expect(r.mastery.p_l_after).toBeCloseTo(0.66)
  })

  it('未知会话回退通用量规与默认掌握度', () => {
    const r = mockSubmitFeynman('feynman-不存在的会话', '它解决了某个问题，比如这个例子')
    expect(r.mastery.kp_name).toBe('通用概念')
    expect(r.mastery.p_l_before).toBe(0.3)
    // 通用量规：「解决/问题」+「比如」命中 2/3 → 良好
    expect(r.grade).toBe('良好')
  })

  it('已知主题均有量规，建议主题全覆盖', () => {
    for (const topic of ['指针的内存布局', '递归出口设计', '边界条件处理']) {
      expect(KP_KEY_POINTS[topic].length).toBeGreaterThanOrEqual(3)
    }
    expect(GENERIC_KEY_POINTS.length).toBeGreaterThanOrEqual(3)
  })
})
