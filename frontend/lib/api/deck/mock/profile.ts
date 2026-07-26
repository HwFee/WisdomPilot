/* 档案 mock：身份 + 智核流水 + 竞技场 + 认证 + 排行榜（数值与 dashboard/arena mock 一致） */

import type { ProfileData } from '../types'
import { ARENA_HOME_MOCK } from './arena'
import { CERT_HOME_MOCK } from './certification'
import { dashboardMock } from './dashboard'

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
}
