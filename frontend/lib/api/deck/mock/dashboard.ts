/* 仪表盘 mock：取值与 docs/design-preview/dashboard-v2.html 演示数据一致 */

import type { AbilityAxis, AxisKey, DeckDashboard } from '../types'
import { trainingFingerprint } from './certification'

/* ── P-01 主任务推荐理由（与后端 router.py _task_reason 措辞一致）── */

const TASK_AXIS_KEYS: Record<string, AxisKey> = {
  'review-gym': 'review',
  arena: 'debug',
  tutor: 'implement',
  certification: 'implement',
}

const TASK_ACTIONS: Record<string, (topic: string | null) => string> = {
  'review-gym': (topic) => (topic ? `这一关专攻「${topic}」。` : '这一关正好练这块短板。'),
  arena: (topic) => (topic ? `今天的挑战正好练「${topic}」。` : '今天的挑战正好练这块短板。'),
  tutor: (topic) => (topic ? `把「${topic}」讲清楚，能最快补上这块短板。` : '把这块短板讲清楚，能最快补上。'),
  certification: () => '先来一场无 AI 认证，检验基础是否扎实。',
}

/**
 * 生成任务卡片推荐理由（纯函数）：引用模块对应轴的等级与关联弱点知识点。
 * 与后端 `build_main_task` 的 reason 文案一致。
 * @param axes 三轴能力列表
 * @param module 任务模块 key
 * @param weakness 任务关联弱点知识点（null 时回退该轴 weakest_focus）
 * @param asPrimary true=「三轴最低」措辞（主任务）；false=「当前 LV」措辞（备用任务）
 */
export function describeTaskReason(
  axes: AbilityAxis[],
  module: string,
  weakness: string | null,
  asPrimary = true
): string {
  const axis = axes.find((a) => a.key === TASK_AXIS_KEYS[module]) ?? axes[0]
  const topic = weakness ?? axis.weakest_focus
  const prefix = asPrimary
    ? `你的「${axis.label}」轴是三轴最低（LV.${axis.level}）`
    : `你的「${axis.label}」轴当前 LV.${axis.level}`
  return prefix + '，' + TASK_ACTIONS[module](topic)
}

/* ── P-04 弱点来源标注（与后端 router.py _weak_point_source 一致）── */

// 事件来源 → [答错时文案, 答对时文案]
const WEAK_SOURCE_LABELS: Record<string, [wrong: string, right: string]> = {
  review_gym: ['审查漏报', '审查命中'],
  arena: ['竞技场失败', '竞技场攻克'],
  feynman: ['费曼待加强', '费曼检验'],
  certification: ['认证考试', '认证考试'],
  placement: ['定级测试', '定级测试'],
}

/** 事件来源 → 来源短语（纯函数），如 review_gym + 答错 → 「审查漏报」 */
export function describeWeakSource(source: string, correct: boolean): string {
  const [wrong, right] = WEAK_SOURCE_LABELS[source] ?? ['练习记录', '练习记录']
  return correct ? right : wrong
}

/** 弱点来源标注：时间标签 + 来源短语，如「3天前 · 审查漏报」 */
export function weakPointSource(timeLabel: string, source: string, correct: boolean): string {
  return `${timeLabel} · ${describeWeakSource(source, correct)}`
}

/* ── P-02 能力指纹可视化数据整形（纯函数，供 dashboard 顶部指纹条形图使用）── */

const FINGERPRINT_AXIS_ORDER: AxisKey[] = ['review', 'debug', 'implement']

/** 三轴按固定 R-D-I 顺序重排：保证指纹短码与条形图渲染顺序确定性 */
export function orderFingerprintAxes(axes: AbilityAxis[]): AbilityAxis[] {
  return FINGERPRINT_AXIS_ORDER.map((key) => axes.find((a) => a.key === key)).filter(
    (a): a is AbilityAxis => a !== undefined,
  )
}

/** 单轴 XP 进度 0-1（xp_current / xp_next，防除零并夹取到 [0,1]） */
export function axisXpProgress(axis: AbilityAxis): number {
  if (axis.xp_next <= 0) return 0
  return Math.min(1, Math.max(0, axis.xp_current / axis.xp_next))
}

/** 能力指纹短码（R{x}-D{x}-I{x}），复用认证域已实现的训练指纹（P-11 同源） */
export function dashboardFingerprint(axes: AbilityAxis[]): string {
  return trainingFingerprint(axes)
}

export const dashboardMock: DeckDashboard = {
  user: { name: '清源', cores: 86 },

  main_task: {
    id: 'REVIEW-0247',
    module: 'review-gym',
    module_label: '代码审查室',
    stage_label: '第 12 关',
    title: '这段快速排序里有 2 处缺陷，它们藏得很像"能跑的代码"。',
    highlight: '2 处缺陷',
    desc: 'AI 生成的代码 70% 能直接运行，但其中三分之一藏着边界错误。找出它们——这比写出它们更值钱。',
    difficulty: 3,
    eta_minutes: 8,
    related_weakness: '边界条件处理',
    reason: '你的「审阅」轴当前 LV.4，这一关专攻「边界条件处理」。',
    target_url: '/review-gym?session=REVIEW-0247',
    cta_label: '开始审查 →',
    alternates: [
      {
        id: 'DEBUG-0091',
        module: 'arena',
        module_label: '调试竞技场',
        stage_label: '今日挑战',
        title: '这段中位数统计陷入了死循环，测试全挂。',
        highlight: '死循环',
        desc: '失败输出已经摆在你面前。限时 10 分钟，让测试全部变绿——速度和准确率都算分。',
        difficulty: 3,
        eta_minutes: 10,
        related_weakness: '边界条件处理',
        reason: '你的「调试」轴当前 LV.3，今天的挑战正好练「边界条件处理」。',
        target_url: '/arena?challenge=DEBUG-0091',
        cta_label: '开始调试 →',
        alternates: [],
      },
      {
        id: 'TUTOR-REC',
        module: 'tutor',
        module_label: '苏格拉底导师',
        stage_label: '费曼检验',
        title: '用自己的话，向导师讲清楚「递归出口」为什么重要。',
        highlight: '递归出口',
        desc: '能讲明白才是真懂。导师会追问你的每一个模糊点，直到没有盲区。',
        difficulty: 2,
        eta_minutes: 5,
        related_weakness: '递归出口设计',
        reason: '你的「实现」轴当前 LV.5，把「递归出口设计」讲清楚，能最快补上这块短板。',
        target_url: '/tutor?topic=递归出口设计',
        cta_label: '开始对话 →',
        alternates: [],
      },
    ],
  },

  ability_map: {
    has_placement: true,
    axes: [
      { key: 'review', label: '审阅', level: 4, xp_current: 1240, xp_next: 1600, weakest_focus: '并发代码审阅' },
      { key: 'debug', label: '调试', level: 3, xp_current: 860, xp_next: 1200, weakest_focus: '指针与内存错误定位' },
      { key: 'implement', label: '实现', level: 5, xp_current: 2050, xp_next: 2400, weakest_focus: '动态规划状态设计' },
    ],
  },

  modules: [
    {
      key: 'review-gym',
      stats: [
        { label: '今日完成', value: '3' },
        { label: '命中率', value: '82%' },
        { label: '连续 5 天', trend: 'up' },
      ],
    },
    {
      key: 'arena',
      stats: [
        { label: '段位', value: '铂金 II' },
        { label: '本周排名', value: '#47' },
        { label: '上升 12 名', trend: 'up' },
      ],
    },
    {
      key: 'tutor',
      stats: [
        { label: '智核余额', value: '86' },
        { label: '今日已用', value: '4' },
      ],
    },
    {
      key: 'certification',
      stats: [
        { label: '已认证', value: '链表 / 排序' },
        { label: '下次可考', value: '3 天后' },
      ],
    },
  ],

  weak_points: [
    { name: '边界条件处理', category: '数据结构 · 排序', p_l: 0.42, source: weakPointSource('2天前', 'review_gym', false) },
    { name: '指针的内存布局', category: 'C 程序设计 · 指针', p_l: 0.55, source: weakPointSource('昨天', 'arena', false) },
    { name: '递归出口设计', category: '通用 · 递归', p_l: 0.61, source: weakPointSource('3天前', 'feynman', false) },
  ],

  rhythm: {
    streak_days: 7,
    days: [
      { label: '一', minutes: 25, is_today: false },
      { label: '二', minutes: 40, is_today: false },
      { label: '三', minutes: 18, is_today: false },
      { label: '四', minutes: 52, is_today: false },
      { label: '五', minutes: 34, is_today: false },
      { label: '六', minutes: 61, is_today: false },
      { label: '日', minutes: 45, is_today: true },
    ],
  },

  review_due: { total: 5, due_today: 2 },

  feed: [
    {
      time: '09:41',
      segments: [
        { t: '审查 ' },
        { t: 'REVIEW-0246', tone: 'strong' },
        { t: ' 找出 ' },
        { t: '3/3', tone: 'ok' },
        { t: ' 处缺陷' },
      ],
    },
    {
      time: '昨天',
      segments: [
        { t: '调试竞技场修复 ' },
        { t: '死循环', tone: 'strong' },
        { t: ' · ' },
        { t: '+23 分', tone: 'ok' },
      ],
    },
    {
      time: '昨天',
      segments: [
        { t: '费曼检验「指针」· 理解度 ' },
        { t: '良好', tone: 'ok' },
      ],
    },
    {
      time: '2天前',
      segments: [
        { t: '审查 ' },
        { t: 'REVIEW-0241', tone: 'strong' },
        { t: ' 漏掉 ' },
        { t: '1', tone: 'bad' },
        { t: ' 处缺陷' },
      ],
    },
  ],
}
