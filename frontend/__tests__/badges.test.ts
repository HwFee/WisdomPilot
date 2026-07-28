/**
 * 徽章系统 mock 判定逻辑测试（纯函数：规则清单 / 判定引擎 / 徽章墙脱敏）
 */
import {
  BADGE_DEFS,
  MOCK_BADGE_FACTS,
  buildBadgeWall,
  evaluateBadgeUnlocks,
  isNightHour,
  type BadgeFacts,
} from '@/lib/api/deck/mock/badges'

/** 全零事实：无任何历史成就 */
const EMPTY_FACTS: BadgeFacts = {
  hasPlacement: false,
  certCount: 0,
  certLevels: [],
  certTopics: [],
  certPerfectScore: false,
  reviewAttempts: 0,
  reviewPerfect: false,
  arenaWins: 0,
  arenaWinStreak: 0,
  feynmanPasses: 0,
  feynmanBestGrade: null,
  streakDays: 0,
  nightSubmissions: 0,
  masteredTopics: 0,
  comeback: false,
}

describe('BADGE_DEFS 清单', () => {
  it('17 枚：铜 7 / 银 7 / 金 3，3 枚隐藏', () => {
    expect(BADGE_DEFS).toHaveLength(17)
    expect(BADGE_DEFS.filter((b) => b.tier === 'bronze')).toHaveLength(7)
    expect(BADGE_DEFS.filter((b) => b.tier === 'silver')).toHaveLength(7)
    expect(BADGE_DEFS.filter((b) => b.tier === 'gold')).toHaveLength(3)
    expect(BADGE_DEFS.filter((b) => b.hidden)).toHaveLength(3)
  })

  it('奖励符合分级：铜 5 / 银 10 / 金 20，总上限 165', () => {
    for (const b of BADGE_DEFS) {
      const expected = b.tier === 'bronze' ? 5 : b.tier === 'silver' ? 10 : 20
      expect(b.reward_cores).toBe(expected)
    }
    expect(BADGE_DEFS.reduce((sum, b) => sum + b.reward_cores, 0)).toBe(165)
  })
})

describe('evaluateBadgeUnlocks', () => {
  it('空事实 + 无上下文 → 无解锁', () => {
    expect(evaluateBadgeUnlocks(EMPTY_FACTS, null, new Set())).toHaveLength(0)
  })

  it('历史事实驱动：认证 2 主题 + 熟练 → cert-multi-topic / cert-adept / first-cert', () => {
    const facts: BadgeFacts = {
      ...EMPTY_FACTS,
      certCount: 2,
      certLevels: ['熟练', '熟练'],
      certTopics: ['链表', '排序'],
    }
    const ids = evaluateBadgeUnlocks(facts, null, new Set()).map((b) => b.id)
    expect(ids).toContain('first-cert')
    expect(ids).toContain('cert-adept')
    expect(ids).toContain('cert-multi-topic')
    expect(ids).not.toContain('cert-master')
  })

  it('提交上下文驱动：满分 → 隐藏徽章 perfect-score；三连胜 → arena-streak-3', () => {
    const byScore = evaluateBadgeUnlocks(EMPTY_FACTS, { examPassed: true, examScore: 100 }, new Set())
    expect(byScore.map((b) => b.id)).toContain('perfect-score')
    const byStreak = evaluateBadgeUnlocks(EMPTY_FACTS, { arenaSolved: true, arenaWinStreak: 3 }, new Set())
    const streakIds = byStreak.map((b) => b.id)
    expect(streakIds).toContain('arena-first-win')
    expect(streakIds).toContain('arena-streak-3')
  })

  it('费曼评级：良好 → feynman-first；优秀 → 再加 feynman-star', () => {
    const good = evaluateBadgeUnlocks(EMPTY_FACTS, { feynmanGrade: '良好' }, new Set()).map((b) => b.id)
    expect(good).toContain('feynman-first')
    expect(good).not.toContain('feynman-star')
    const star = evaluateBadgeUnlocks(EMPTY_FACTS, { feynmanGrade: '优秀' }, new Set()).map((b) => b.id)
    expect(star).toContain('feynman-star')
  })

  it('幂等：已解锁集合中的徽章不重复返回', () => {
    const facts: BadgeFacts = { ...EMPTY_FACTS, certCount: 1, certLevels: ['熟练'], certTopics: ['链表'] }
    const first = evaluateBadgeUnlocks(facts, null, new Set())
    const second = evaluateBadgeUnlocks(facts, null, new Set(first.map((b) => b.id)))
    expect(first.length).toBeGreaterThan(0)
    expect(second).toHaveLength(0)
  })

  it('解锁项携带播放仪式所需字段', () => {
    const [unlock] = evaluateBadgeUnlocks(EMPTY_FACTS, { examPassed: true, examScore: 100 }, new Set())
    expect(unlock).toMatchObject({ tier: 'bronze', reward_cores: 5 })
    expect(typeof unlock.title).toBe('string')
  })
})

describe('buildBadgeWall', () => {
  it('全量 17 枚，未解锁 hidden 脱敏为 ???', () => {
    const wall = buildBadgeWall(new Set())
    expect(wall).toHaveLength(17)
    const nightOwl = wall.find((b) => b.id === 'night-owl')!
    expect(nightOwl.hidden).toBe(true)
    expect(nightOwl.unlocked).toBe(false)
    expect(nightOwl.title).toBe('???')
    expect(nightOwl.condition_desc).toBe('???')
    expect(nightOwl.unlocked_at).toBeNull()
  })

  it('hidden 解锁后显示真名并带时间；非隐藏未解锁不脱敏', () => {
    const wall = buildBadgeWall(new Set(['night-owl']), '2026-07-27T00:00:00Z')
    const nightOwl = wall.find((b) => b.id === 'night-owl')!
    expect(nightOwl.title).toBe('夜猫子')
    expect(nightOwl.unlocked_at).toBe('2026-07-27T00:00:00Z')
    const streak = wall.find((b) => b.id === 'streak-3')!
    expect(streak.unlocked).toBe(false)
    expect(streak.title).toBe('三日不断')
  })
})

describe('isNightHour', () => {
  it('00:00–05:00 为夜间', () => {
    expect(isNightHour(new Date('2026-07-27T03:30:00'))).toBe(true)
    expect(isNightHour(new Date('2026-07-27T05:00:00'))).toBe(false)
    expect(isNightHour(new Date('2026-07-27T23:59:00'))).toBe(false)
  })
})

describe('MOCK_BADGE_FACTS 自洽性', () => {
  it('与各领域 mock 一致的历史事实可解锁对应徽章', () => {
    const ids = evaluateBadgeUnlocks(MOCK_BADGE_FACTS, null, new Set()).map((b) => b.id)
    expect(ids).toEqual(
      expect.arrayContaining([
        'placement-done',
        'first-cert',
        'cert-adept',
        'cert-multi-topic',
        'arena-streak-3',
        'streak-3',
        'streak-7',
      ])
    )
  })
})
