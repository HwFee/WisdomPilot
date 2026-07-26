/* 苏格拉底导师 mock：脚本化追问树（真实后端就位后由 LLM 生成） */

import type { FeynmanGrade, MasteryLevel, MasteryUpdate, TutorState } from '../types'
import { ABILITY_MAP_MOCK } from './abilities'

export const TUTOR_STATE_MOCK: TutorState = {
  cores_balance: 86,
  today_used: 4,
  cost_per_question: 2,
  suggested_topics: ['指针的内存布局', '递归出口设计', '边界条件处理'],
  messages: [
    {
      id: 'welcome',
      role: 'tutor',
      mode: 'socratic',
      text: '我是你的苏格拉底导师。我不会给你答案——我只会追问，直到你自己把问题想明白。顺带一提：上次 REVIEW-0248 你漏掉了一处边界检查，「边界条件处理」正好可以切到「考考我」练练。',
    },
  ],
}

/** 关键词 → 定向追问 */
const KEYWORD_PROBES: Array<{ keys: string[]; reply: string }> = [
  {
    keys: ['指针', 'pointer', '内存'],
    reply: '先别急着写代码。你觉得 p 指向的内存被 free 之后，p 这个变量本身变成了什么？它还「认识」原来那块地址吗？',
  },
  {
    keys: ['递归'],
    reply: '如果递归没有出口，调用栈一层层压下去会发生什么？你能描述第 1000 层时栈里的状态吗？',
  },
  {
    keys: ['边界', '空', '0'],
    reply: '好，那我们把输入推到极限：空列表、单个元素、全部相同——你的代码在这三种情况下分别会走到哪一行？',
  },
  {
    keys: ['排序'],
    reply: '你说它排对了。那我问你：当数组里有两个相同的元素时，它们各自会落在哪个位置？一个都不多、一个都不少吗？',
  },
  {
    keys: ['循环', '死循环'],
    reply: '循环退出靠的是哪个条件？你能找到一个输入，让这个条件永远不满足吗？',
  },
]

/** 通用追问库：按对话轮数轮转 */
const GENERIC_PROBES = [
  '在你给出答案之前——你觉得这段代码最可能在哪一类输入上出错？',
  '你说的「正确」具体指什么？我们怎么验证它？',
  '如果输入规模放大 1000 倍，你的方案还成立吗？哪一步先撑不住？',
  '试着构造一个让自己代码出错的反例。最小的那个是什么？',
  '如果让你给这段代码写三条测试用例，你会先写哪三条？为什么？',
]

export function socraticReply(text: string, historyLen: number): string {
  const probe = KEYWORD_PROBES.find((p) => p.keys.some((k) => text.includes(k)))
  if (probe) return probe.reply
  return GENERIC_PROBES[historyLen % GENERIC_PROBES.length]
}

export function feynmanOpening(topic: string): string {
  return `好，「${topic}」。用你自己的话讲给我听——假装你在教一个完全不懂编程的人。不许用术语搪塞，讲到他能复述为止。`
}

export interface FeynmanVerdict {
  verdict: string
  grade: FeynmanGrade
  covered: string[]                     // 覆盖到的关键点评分项
  missed: string[]                      // 漏掉的关键点（盲区）
}

/** 评分关键点：label 展示用，keys 命中任一即算覆盖 */
export interface FeynmanKeyPoint {
  label: string
  keys: string[]
}

/** 各建议主题的评分量规 */
export const KP_KEY_POINTS: Record<string, FeynmanKeyPoint[]> = {
  指针的内存布局: [
    { label: '指针存的是地址', keys: ['地址', '指向'] },
    { label: '指针自身也占内存', keys: ['指针变量', '本身', '8 字节', '8字节'] },
    { label: '解引用取值', keys: ['解引用', '取值', '*'] },
    { label: '释放后成悬垂指针', keys: ['释放', 'free', '悬垂', '悬空'] },
  ],
  递归出口设计: [
    { label: '出口条件先判断', keys: ['出口', '终止条件', '基例'] },
    { label: '每轮向出口收敛', keys: ['收敛', '缩小', '逼近', '规模'] },
    { label: '缺出口会栈溢出', keys: ['栈溢出', '溢出', '无限', '爆栈'] },
    { label: '返回值逐层回传', keys: ['返回', '回传', '回溯'] },
  ],
  边界条件处理: [
    { label: '空输入', keys: ['空', 'null', 'NULL'] },
    { label: '单元素', keys: ['单元素', '一个元素', '只有 1', '只有1'] },
    { label: '极值与越界', keys: ['极值', '最大', '最小', '溢出', '越界'] },
    { label: '重复元素', keys: ['重复', '相同'] },
  ],
}

/** 未知主题的通用量规 */
export const GENERIC_KEY_POINTS: FeynmanKeyPoint[] = [
  { label: '它解决什么问题', keys: ['解决', '问题', '为什么需要'] },
  { label: '核心机制', keys: ['原理', '机制', '本质', '内部'] },
  { label: '一个具体例子', keys: ['比如', '例如', '举例', '假设'] },
]

/** 因果 / 举例结构：至少出现一处 */
const STRUCTURE_RE = /因为|所以|否则|如果|比如|例如|假设|举个例子/

/**
 * 费曼评分（纯函数）：按关键点覆盖率 + 因果/举例结构评级
 * 优秀 ≥80% 覆盖且有结构；良好 ≥50% 覆盖，或 ≥1/3 覆盖且有结构；否则待加强
 */
export function feynmanVerdict(text: string, keyPoints: FeynmanKeyPoint[]): FeynmanVerdict {
  const covered = keyPoints.filter((kp) => kp.keys.some((k) => text.includes(k)))
  const missed = keyPoints.filter((kp) => !covered.includes(kp))
  const coverage = keyPoints.length === 0 ? 0 : covered.length / keyPoints.length
  const hasStructure = STRUCTURE_RE.test(text)
  const coveredLabels = covered.map((k) => k.label)
  const missedLabels = missed.map((k) => k.label)
  const blindSpots = missedLabels.slice(0, 2).join('」「')

  if (coverage >= 0.8 && hasStructure) {
    return {
      grade: '优秀',
      verdict:
        '讲得有因有果，关键点也都踩到了——这说明你真的内化了。只追一个盲区：如果让你向「会编程但不信你的人」证明它，你会用什么证据？',
      covered: coveredLabels,
      missed: missedLabels,
    }
  }
  if (coverage >= 0.5 || (coverage >= 1 / 3 && hasStructure)) {
    const gap =
      missedLabels.length > 0
        ? `但我抓到两个盲区：「${blindSpots}」。`
        : '但通篇都在讲「是什么」，缺一条因果或一个例子撑住它。'
    return {
      grade: '良好',
      verdict: `主干讲清楚了，${gap}补上再讲一遍？`,
      covered: coveredLabels,
      missed: missedLabels,
    }
  }
  const gap =
    missedLabels.length > 0
      ? `「${blindSpots}」这些关键点你都没碰到。`
      : '你说的「正确」没有任何因果或例子支撑。'
  return {
    grade: '待加强',
    verdict: `停——${gap}这不是理解，是背诵。回到最小的一步：这个知识点要解决什么问题？不解决会怎样？`,
    covered: coveredLabels,
    missed: missedLabels,
  }
}

/* ── 掌握度更新 ── */

const GRADE_DELTA: Record<FeynmanGrade, number> = { 优秀: 0.15, 良好: 0.05, 待加强: -0.05 }

/** p_l → 掌握等级：初识 <0.3 / 熟悉 <0.6 / 熟练 <0.8 / 精通 ≥0.8 */
export function masteryLevel(p: number): MasteryLevel {
  if (p < 0.3) return '初识'
  if (p < 0.6) return '熟悉'
  if (p < 0.8) return '熟练'
  return '精通'
}

/** 费曼检验后的掌握度变化（纯函数，确定性增减并夹取 0..1） */
export function mockMasteryUpdate(
  kpName: string,
  grade: FeynmanGrade,
  currentP: number
): MasteryUpdate {
  const after = Math.min(1, Math.max(0, currentP + GRADE_DELTA[grade]))
  return { kp_name: kpName, p_l_before: currentP, p_l_after: after, level: masteryLevel(after) }
}

/* ── 费曼会话：sessionId → topic，供 submit 时解析量规 ── */

const feynmanSessions = new Map<string, string>()
let feynmanSeq = 0

export function mockStartFeynman(topic: string): { sessionId: string; opening: string } {
  feynmanSeq += 1
  const sessionId = `feynman-${Date.now()}-${feynmanSeq}`
  feynmanSessions.set(sessionId, topic)
  return { sessionId, opening: feynmanOpening(topic) }
}

export interface MockFeynmanCheck {
  verdict: string
  grade: FeynmanGrade
  mastery: MasteryUpdate
}

/** 提交解释：按会话主题取量规评分，未知会话回退通用量规 */
export function mockSubmitFeynman(sessionId: string, text: string): MockFeynmanCheck {
  const topic = feynmanSessions.get(sessionId)
  const keyPoints = (topic && KP_KEY_POINTS[topic]) || GENERIC_KEY_POINTS
  const { verdict, grade } = feynmanVerdict(text, keyPoints)
  const currentP = ABILITY_MAP_MOCK.knowledge_points.find((k) => k.name === topic)?.p_l ?? 0.3
  return { verdict, grade, mastery: mockMasteryUpdate(topic ?? '通用概念', grade, currentP) }
}
