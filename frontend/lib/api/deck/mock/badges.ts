/* 徽章系统 mock：17 枚徽章定义 + 纯函数判定引擎
   规格：docs/superpowers/specs/2026-07-27-badge-system-design.md §3/§4
   真实后端就位后由服务端在提交事务内评估，本文件仅服务 mock 模式 */

import type { BadgeInfo, BadgeTier, BadgeUnlock, FeynmanGrade } from '../types'

export interface BadgeDef {
  id: string
  tier: BadgeTier
  title: string
  hidden: boolean                 // true = 彩蛋徽章，未解锁时 title/desc 脱敏为 ???
  condition_desc: string
  reward_cores: number             // 铜 5 / 银 10 / 金 20
}

/* ── 清单（铜 7 / 银 7 / 金 3，含 3 枚隐藏）── */

export const BADGE_DEFS: BadgeDef[] = [
  // 铜
  { id: 'placement-done', tier: 'bronze', title: '知己知彼', hidden: false, condition_desc: '完成定级测试', reward_cores: 5 },
  { id: 'first-cert', tier: 'bronze', title: '初露锋芒', hidden: false, condition_desc: '通过首次能力认证', reward_cores: 5 },
  { id: 'review-first', tier: 'bronze', title: '复盘首秀', hidden: false, condition_desc: '首次完成复习舱判定', reward_cores: 5 },
  { id: 'arena-first-win', tier: 'bronze', title: '首胜', hidden: false, condition_desc: '竞技场首次全题通过', reward_cores: 5 },
  { id: 'feynman-first', tier: 'bronze', title: '以教为学', hidden: false, condition_desc: '首次费曼检验合格', reward_cores: 5 },
  { id: 'streak-3', tier: 'bronze', title: '三日不断', hidden: false, condition_desc: '连续学习 3 天', reward_cores: 5 },
  { id: 'night-owl', tier: 'bronze', title: '夜猫子', hidden: true, condition_desc: '00:00–05:00 间完成一次有效提交', reward_cores: 5 },
  // 银
  { id: 'cert-adept', tier: 'silver', title: '游刃有余', hidden: false, condition_desc: '获得首个「熟练」级认证', reward_cores: 10 },
  { id: 'cert-multi-topic', tier: 'silver', title: '博览', hidden: false, condition_desc: '认证覆盖 2 个不同主题', reward_cores: 10 },
  { id: 'review-perfect', tier: 'silver', title: '弹无虚发', hidden: false, condition_desc: '复习舱单次判定全命中', reward_cores: 10 },
  { id: 'arena-streak-3', tier: 'silver', title: '连战连捷', hidden: false, condition_desc: '竞技场三连胜', reward_cores: 10 },
  { id: 'feynman-star', tier: 'silver', title: '讲明白了', hidden: false, condition_desc: '费曼检验拿到最高评级', reward_cores: 10 },
  { id: 'streak-7', tier: 'silver', title: '七日之约', hidden: false, condition_desc: '连续学习 7 天', reward_cores: 10 },
  { id: 'perfect-score', tier: 'silver', title: '满分答卷', hidden: true, condition_desc: '认证考试得分 100', reward_cores: 10 },
  // 金
  { id: 'cert-master', tier: 'gold', title: '登峰造极', hidden: false, condition_desc: '获得首个「精通」级认证', reward_cores: 20 },
  { id: 'topic-ascend', tier: 'gold', title: '一域通天', hidden: false, condition_desc: '单主题全部知识点达「精通」', reward_cores: 20 },
  { id: 'comeback', tier: 'gold', title: '起死回生', hidden: true, condition_desc: '同一知识点先答错、后在复习舱答对', reward_cores: 20 },
]

/* ── 事实与上下文（对应后端 BadgeFacts / pending_context）── */

export interface BadgeFacts {
  hasPlacement: boolean
  certCount: number
  certLevels: string[]            // 已获认证的等级，如 ['熟练']
  certTopics: string[]            // 已获认证的主题
  certPerfectScore: boolean
  reviewAttempts: number
  reviewPerfect: boolean
  arenaWins: number
  arenaWinStreak: number
  feynmanPasses: number
  feynmanBestGrade: FeynmanGrade | null
  streakDays: number
  nightSubmissions: number
  masteredTopics: number          // 全知识点精通的主题数
  comeback: boolean
}

/** 本次提交的即时上下文（win_streak 等只存当前值的事实只能靠它触发） */
export interface BadgeSubmitContext {
  placementDone?: boolean
  examPassed?: boolean
  examScore?: number
  examLevel?: string
  reviewSubmitted?: boolean
  reviewPerfect?: boolean
  arenaSolved?: boolean
  arenaWinStreak?: number
  feynmanGrade?: FeynmanGrade
  isNight?: boolean
}

/** 00:00–05:00 夜间提交判定（夜猫子徽章） */
export function isNightHour(date: Date = new Date()): boolean {
  return date.getHours() >= 0 && date.getHours() < 5
}

/* ── 判定规则：check(facts, ctx)，ctx 可为 null（回填时只读历史事实）── */

export type BadgeCheck = (facts: BadgeFacts, ctx: BadgeSubmitContext | null) => boolean

const ADEPT_LEVELS = ['熟练', '精通']

export const BADGE_CHECKS: Record<string, BadgeCheck> = {
  'placement-done': (f, c) => f.hasPlacement || c?.placementDone === true,
  'first-cert': (f, c) => f.certCount >= 1 || c?.examPassed === true,
  'review-first': (f, c) => f.reviewAttempts >= 1 || c?.reviewSubmitted === true,
  'arena-first-win': (f, c) => f.arenaWins >= 1 || c?.arenaSolved === true,
  'feynman-first': (f, c) =>
    f.feynmanPasses >= 1 || c?.feynmanGrade === '良好' || c?.feynmanGrade === '优秀',
  'streak-3': (f) => f.streakDays >= 3,
  'night-owl': (f, c) => f.nightSubmissions >= 1 || c?.isNight === true,
  'cert-adept': (f, c) =>
    f.certLevels.some((lv) => ADEPT_LEVELS.includes(lv)) ||
    (c?.examLevel !== undefined && ADEPT_LEVELS.includes(c.examLevel)),
  'cert-multi-topic': (f) => new Set(f.certTopics).size >= 2,
  'review-perfect': (f, c) => f.reviewPerfect || c?.reviewPerfect === true,
  'arena-streak-3': (f, c) => f.arenaWinStreak >= 3 || (c?.arenaWinStreak ?? 0) >= 3,
  'feynman-star': (f, c) => f.feynmanBestGrade === '优秀' || c?.feynmanGrade === '优秀',
  'streak-7': (f) => f.streakDays >= 7,
  'perfect-score': (f, c) => f.certPerfectScore || c?.examScore === 100,
  'cert-master': (f, c) => f.certLevels.includes('精通') || c?.examLevel === '精通',
  'topic-ascend': (f) => f.masteredTopics >= 1,
  comeback: (f) => f.comeback,
}

/* ── 引擎（纯函数）── */

/** 全量跑规则，跳过已解锁，返回新解锁项（对应后端 evaluate_and_award 的判定部分） */
export function evaluateBadgeUnlocks(
  facts: BadgeFacts,
  ctx: BadgeSubmitContext | null,
  unlocked: ReadonlySet<string>
): BadgeUnlock[] {
  return BADGE_DEFS.filter(
    (def) => !unlocked.has(def.id) && BADGE_CHECKS[def.id]?.(facts, ctx) === true
  ).map((def) => ({
    id: def.id,
    tier: def.tier,
    title: def.title,
    reward_cores: def.reward_cores,
  }))
}

/** 徽章墙视图模型：hidden 未解锁脱敏为 ???（对应 GET /certification/home 的 badges 字段） */
export function buildBadgeWall(unlocked: ReadonlySet<string>, nowIso: string | null = null): BadgeInfo[] {
  return BADGE_DEFS.map((def) => {
    const isUnlocked = unlocked.has(def.id)
    const masked = def.hidden && !isUnlocked
    return {
      id: def.id,
      tier: def.tier,
      title: masked ? '???' : def.title,
      condition_desc: masked ? '???' : def.condition_desc,
      hidden: def.hidden,
      unlocked: isUnlocked,
      reward_cores: def.reward_cores,
      unlocked_at: isUnlocked ? nowIso : null,
    }
  })
}

/* ── mock 会话态：与各领域 mock 数据自洽的事实 + 已解锁集合 ── */

/** 与各 mock 一致：已定级、2 个「熟练」认证（链表/排序）、arena 当前 3 连胜、连续学习 7 天 */
export const MOCK_BADGE_FACTS: BadgeFacts = {
  hasPlacement: true,
  certCount: 2,
  certLevels: ['熟练', '熟练'],
  certTopics: ['链表', '排序'],
  certPerfectScore: false,
  reviewAttempts: 0,
  reviewPerfect: false,
  arenaWins: 0,
  arenaWinStreak: 3,
  feynmanPasses: 0,
  feynmanBestGrade: null,
  streakDays: 7,
  nightSubmissions: 0,
  masteredTopics: 0,
  comeback: false,
}

/** 历史事实已达成的徽章预置为已解锁，保证徽章墙与 mock 数据自洽 */
const mockUnlocked = new Set<string>(
  evaluateBadgeUnlocks(MOCK_BADGE_FACTS, null, new Set()).map((b) => b.id)
)

/** 提交端点共用：评估 + 记入已解锁（幂等，同条件二次提交不重复发） */
export function awardMockBadges(ctx: BadgeSubmitContext): BadgeUnlock[] {
  const fresh = evaluateBadgeUnlocks(MOCK_BADGE_FACTS, ctx, mockUnlocked)
  for (const badge of fresh) mockUnlocked.add(badge.id)
  return fresh
}

/** 认证 home 的徽章墙（每次调用按当前解锁状态重建） */
export function getMockBadgeWall(): BadgeInfo[] {
  return buildBadgeWall(mockUnlocked, new Date().toISOString())
}
