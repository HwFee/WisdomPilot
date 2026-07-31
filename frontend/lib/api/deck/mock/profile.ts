/* 档案 mock：身份 + 智核流水 + 竞技场 + 认证 + 排行榜 + 训练轨迹时间线 */

import type { ProfileData, TimelineEntry } from '../types'
import { ARENA_HOME_MOCK } from './arena'
import { CERT_HOME_MOCK } from './certification'
import { dashboardMock } from './dashboard'

/* P-09 时间线 mock：四类条目按时间升序，覆盖 定级 → 轴升级 → 里程碑 → 认证 */
/* 定级条目与后端 §8 同源：score 60 → base=3，debug 恒低一档 → {3,2,3} → R3-D2-I3 */
const TIMELINE_MOCK: TimelineEntry[] = [
  {
    type: 'placement',
    date: '2026-03-14',
    score: 60,
    levels: { review: 3, debug: 2, implement: 3 },
    fingerprint: 'R3-D2-I3',
  },
  { type: 'axis_upgrade', date: '2026-03-20', axis: 'review', label: '审阅', from_level: 3, to_level: 4 },
  { type: 'mastery', date: '2026-04-02', kp_name: '边界条件处理', level: '熟练' },
  { type: 'axis_upgrade', date: '2026-04-11', axis: 'implement', label: '实现', from_level: 3, to_level: 4 },
  { type: 'cert', date: '2026-04-22', topic: '链表', level: '熟练', score: 92 },
  { type: 'mastery', date: '2026-05-30', kp_name: '链表操作', level: '精通' },
  { type: 'cert', date: '2026-06-18', topic: '排序', level: '熟练', score: 88 },
  { type: 'axis_upgrade', date: '2026-07-02', axis: 'implement', label: '实现', from_level: 4, to_level: 5 },
]

/** 时间线 mock 生成（纯函数）：返回一份新数组，避免外部误改共享常量 */
export function buildTimelineMock(): TimelineEntry[] {
  return [...TIMELINE_MOCK]
}

export const PROFILE_MOCK: ProfileData = {
  user: { name: '清源', joined_days: 128 },
  cores: {
    balance: 86,
    transactions: [
      { time: '今天 09:12', delta: -2, reason: '苏格拉底导师 · 追问「递归出口」' },
      { time: '今天 09:08', delta: -2, reason: '苏格拉底导师 · 追问「指针释放」' },
      { time: '今天 08:00', delta: 5, reason: '每日登录奖励' },
      { time: '昨天 21:40', delta: -2, reason: '费曼检验 · 指针' },
      { time: '昨天 21:33', delta: -2, reason: '苏格拉底导师 · 追问「边界条件」' },
      { time: '07-19 15:20', delta: 20, reason: '基本功认证通过 · 排序' },
      { time: '07-19 08:00', delta: 5, reason: '每日登录奖励' },
      { time: '07-18 19:05', delta: 10, reason: '调试竞技场 · 连胜 3 场奖励' },
    ],
  },
  arena: ARENA_HOME_MOCK.profile,
  certifications: CERT_HOME_MOCK.certified,
  leaderboard: ARENA_HOME_MOCK.leaderboard,
  recent: dashboardMock.feed,
  timeline: buildTimelineMock(),
}
