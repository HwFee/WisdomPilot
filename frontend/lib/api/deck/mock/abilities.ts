/* 能力图谱 mock：三轴 + 知识点掌握度 + 定级画像快照（与仪表盘 mock 数值一致） */

import type { AbilityAxis, AbilityMapDetail, AxisKey, PlacementSnapshot } from '../types'
import { fingerprintFromPlacement, placementLevels } from './certification'

/* P-10 能力演化对比：三轴展示顺序与中文标签（与后端 AXES 固定顺序一致） */
const AXIS_ORDER: AxisKey[] = ['review', 'debug', 'implement']
const AXIS_LABELS: Record<AxisKey, string> = {
  review: '审阅',
  debug: '调试',
  implement: '实现',
}

/* 定级画像快照：分数与等级复用 placementLevels（定级结果视图同源），
   保证「定级时」与用户看到的定级结果一致 */
const PLACEMENT_SCORE = 60
const PLACEMENT_LEVELS = placementLevels(PLACEMENT_SCORE)

/**
 * P-10 能力演化对比：定级时 vs 现在的三轴等级差（纯函数，可测）。
 *
 * 按固定顺序 review → debug → implement 输出每轴对比；
 * 当前轴缺失（未训练）时回退到定级等级（delta=0）。
 */
export function computeShapeDeltas(
  placement: PlacementSnapshot,
  axes: AbilityAxis[],
): Array<{
  axis: AxisKey
  label: string
  from_level: number
  to_level: number
  delta: number
}> {
  return AXIS_ORDER.map((axis) => {
    const now = axes.find((a) => a.key === axis)
    const from = placement.levels[axis]
    const to = now?.level ?? from
    return {
      axis,
      label: now?.label ?? AXIS_LABELS[axis],
      from_level: from,
      to_level: to,
      delta: to - from,
    }
  })
}

export const ABILITY_MAP_MOCK: AbilityMapDetail = {
  has_placement: true,
  placement: {
    score: PLACEMENT_SCORE,
    date: '2026-03-14',
    levels: PLACEMENT_LEVELS,
    fingerprint: fingerprintFromPlacement(PLACEMENT_LEVELS),
  },
  axes: [
    { key: 'review', label: '审阅', level: 4, xp_current: 1240, xp_next: 1600, weakest_focus: '并发代码审阅' },
    { key: 'debug', label: '调试', level: 3, xp_current: 860, xp_next: 1200, weakest_focus: '指针与内存错误定位' },
    { key: 'implement', label: '实现', level: 5, xp_current: 2050, xp_next: 2400, weakest_focus: '动态规划状态设计' },
  ],
  knowledge_points: [
    // 审阅轴
    { name: '边界条件处理', category: '数据结构 · 排序', axis: 'review', p_l: 0.42, trend: 'down', level: '熟悉' },
    { name: '并发代码审阅', category: '通用 · 并发', axis: 'review', p_l: 0.35, trend: 'flat', level: '熟悉' },
    { name: '坏味道识别', category: '工程 · 重构', axis: 'review', p_l: 0.78, trend: 'up', level: '熟练' },
    { name: '安全漏洞模式', category: '安全 · 注入', axis: 'review', p_l: 0.66, trend: 'up', level: '熟练' },
    // 调试轴
    { name: '指针的内存布局', category: 'C 程序设计 · 指针', axis: 'debug', p_l: 0.55, trend: 'flat', level: '熟悉' },
    { name: '栈与调用帧', category: '通用 · 运行时', axis: 'debug', p_l: 0.71, trend: 'up', level: '熟练' },
    { name: '断点与单步策略', category: '工具 · 调试器', axis: 'debug', p_l: 0.83, trend: 'up', level: '精通' },
    { name: '日志定位法', category: '工具 · 日志', axis: 'debug', p_l: 0.62, trend: 'flat', level: '熟练' },
    // 实现轴
    { name: '递归出口设计', category: '通用 · 递归', axis: 'implement', p_l: 0.61, trend: 'up', level: '熟练' },
    { name: '动态规划状态设计', category: '算法 · DP', axis: 'implement', p_l: 0.48, trend: 'down', level: '熟悉' },
    { name: '链表操作', category: '数据结构 · 链表', axis: 'implement', p_l: 0.88, trend: 'flat', level: '精通' },
    { name: '排序算法实现', category: '算法 · 排序', axis: 'implement', p_l: 0.85, trend: 'flat', level: '精通' },
    { name: '字符串处理', category: '通用 · 字符串', axis: 'implement', p_l: 0.74, trend: 'up', level: '熟练' },
  ],
}
