/* 能力图谱 mock：三轴 + 知识点掌握度（与仪表盘 mock 数值一致） */

import type { AbilityMapDetail } from '../types'

export const ABILITY_MAP_MOCK: AbilityMapDetail = {
  has_placement: true,
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
