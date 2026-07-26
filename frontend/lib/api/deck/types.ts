/* ============================================
   训练舱 · 共享类型契约
   与 docs/backend-api/01-target-design.md 一一对应
   后端未就绪前由 mock 实现，字段即后端 schema
   ============================================ */

export type ModuleKey = 'review-gym' | 'arena' | 'tutor' | 'certification'
export type AxisKey = 'review' | 'debug' | 'implement'
export type Difficulty = 1 | 2 | 3 | 4 | 5

/* ── 仪表盘聚合端点 GET /api/dashboard ── */

export interface MainTask {
  id: string                          // REVIEW-0247
  module: ModuleKey
  module_label: string                // 代码审查室
  stage_label: string                 // 第 12 关
  title: string                       // 这段快速排序里有 2 处缺陷……
  highlight: string | null            // 标题中需要 <em> 高亮的片段
  desc: string
  difficulty: Difficulty
  eta_minutes: number
  related_weakness: string | null
  target_url: string
  cta_label: string                   // 开始审查 →
  alternates: MainTask[]              // 「换一个任务」轮换的完整备选任务
}

export interface AbilityAxis {
  key: AxisKey
  label: string                       // 审阅 / 调试 / 实现
  level: number
  xp_current: number
  xp_next: number                     // 到下一级所需
  weakest_focus: string | null        // 短板一句话
}

export interface WeakPoint {
  name: string
  category: string                    // 数据结构 · 排序
  p_l: number                         // 0-1 掌握度
}

export interface RhythmDay {
  label: string                       // 一 / 二 / …
  minutes: number
  is_today: boolean
}

export type FeedTone = 'plain' | 'strong' | 'ok' | 'bad'
export interface FeedSegment { t: string; tone?: FeedTone }
export interface FeedItem {
  time: string
  segments: FeedSegment[]
}

export interface ModuleStat {
  key: ModuleKey
  /** stat-line 的各字段；trend 项可无 value（如「▲ 连续 5 天」整体上色） */
  stats: Array<{ label: string; value?: string; trend?: 'up' | 'down' }>
}

export interface DeckDashboard {
  user: { name: string; cores: number }
  main_task: MainTask | null          // 未定级 → null，前端显示定级引导
  ability_map: { axes: AbilityAxis[]; has_placement: boolean }
  modules: ModuleStat[]
  weak_points: WeakPoint[]
  rhythm: { days: RhythmDay[]; streak_days: number }
  review_due: { total: number; due_today: number }
  feed: FeedItem[]
}

/* ── 代码审查室 /api/review-gym ── */

export type DefectType = 'logic' | 'boundary' | 'performance' | 'style' | 'security'

export interface ReviewSession {
  id: string
  title: string
  language: string
  code: string
  defect_count: number
  difficulty: Difficulty
  eta_minutes: number
  related_weakness: string | null
}

export interface ReviewMark {
  line: number
  type: DefectType
}

export interface InjectedDefect {
  line: number
  type: DefectType
  explanation: string
}

export interface ReviewVerdict {
  hits: InjectedDefect[]              // 命中
  missed: InjectedDefect[]            // 漏报
  false_alarms: ReviewMark[]          // 误报
  score: number                       // 0-100
  accuracy: number                    // 0-1
}

/* ── 复盘 /api/review（错题复习：与导师对话是相互独立的功能）── */

export type ReviewQueueKind = 'review-gym' | 'arena' | 'knowledge'

export interface ReviewQueueItem {
  id: string
  kind: ReviewQueueKind             // review-gym=审查漏报 arena=未攻克 knowledge=弱知识点
  title: string
  detail: string
  target_url: string
  cta_label: string
  last_at: string
}

export interface ReviewQueue {
  items: ReviewQueueItem[]
  total: number
}

/* ── 调试竞技场 /api/arena ── */

export interface ArenaChallenge {
  id: string
  title: string
  language: string
  code: string                        // 带 bug 的初始代码
  failing_output: string
  time_limit_sec: number
  difficulty: Difficulty
}

export interface ArenaRunResult {
  passed: number
  total: number
  output: string
  solved: boolean
  score_delta: number
}

export interface ArenaLeaderboardEntry {
  rank: number
  name: string
  rating: number
  solved_today: number
  is_self?: boolean
}

export interface ArenaHome {
  profile: { tier: string; rating: number; week_rank: number; rank_delta: number; win_streak: number }
  challenge: ArenaChallenge
  leaderboard: ArenaLeaderboardEntry[]
}

/* ── 苏格拉底导师 /api/tutor ── */

export type TutorMode = 'socratic' | 'feynman'

export interface TutorMessage {
  id: string
  role: 'user' | 'tutor'
  text: string
  mode: TutorMode
}

export interface TutorState {
  cores_balance: number
  today_used: number
  cost_per_question: number
  messages: TutorMessage[]
  suggested_topics: string[]
}

export type FeynmanGrade = '优秀' | '良好' | '待加强'
export type MasteryLevel = '初识' | '熟悉' | '熟练' | '精通'

export interface MasteryUpdate {
  kp_name: string
  p_l_before: number                    // 0..1
  p_l_after: number                     // 0..1
  level?: MasteryLevel
}

export interface TutorReply {
  message: TutorMessage
  cores_balance: number
  grade?: FeynmanGrade                  // 费曼检验评级
  feynman_session_id?: string           // 费曼会话 id（startFeynman 返回）
  mastery_update?: MasteryUpdate        // 费曼检验后掌握度变化
}

/* ── 基本功认证 /api/certification ── */

export interface CertRecord {
  topic: string
  level: string                       // 例如「熟练」
  date: string
  score: number
  verify_code: string
}

export interface CertExamInfo {
  id: string
  topic: string
  question_count: number
  time_limit_min: number
  pass_score: number
}

export interface CertQuestion {
  id: string
  kind: 'mcq' | 'code'
  prompt: string
  options?: string[]
  starter_code?: string
}

export interface CertExam {
  info: CertExamInfo
  questions: CertQuestion[]
}

export interface CertAnswer { question_id: string; answer: string }

export interface CertResult {
  score: number
  passed: boolean
  certificate: CertRecord | null
  per_question: Array<{ question_id: string; correct: boolean }>
}

export interface CertificationHome {
  has_placement: boolean
  certified: CertRecord[]
  available_exams: CertExamInfo[]
  next_available_days: number | null
}

/* ── 能力图谱 /api/ability-map ── */

export interface KnowledgePoint {
  name: string
  category: string
  axis: AxisKey
  p_l: number
  trend: 'up' | 'flat' | 'down'
  level: MasteryLevel
}

export interface AbilityMapDetail {
  axes: AbilityAxis[]
  has_placement: boolean
  knowledge_points: KnowledgePoint[]
}

/* ── 档案 /api/profile ── */

export interface CoreTransaction {
  time: string
  delta: number
  reason: string
}

export interface ProfileData {
  user: { name: string; joined_days: number }
  cores: { balance: number; transactions: CoreTransaction[] }
  arena: ArenaHome['profile']
  certifications: CertRecord[]
  leaderboard: ArenaLeaderboardEntry[]
  recent: FeedItem[]
}
