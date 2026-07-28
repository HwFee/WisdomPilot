/* 基本功认证 mock：徽章墙 + 考试 + 本地判分（真实后端就位后由服务端判分） */

import type {
  CertAnswer,
  CertExam,
  CertRecord,
  CertResult,
  CertificationHome,
} from '../types'
import { awardMockBadges, getMockBadgeWall, isNightHour } from './badges'

/** home 静态部分；badges 字段由 getMockCertHome 按当前解锁状态实时拼装 */
export const CERT_HOME_MOCK: Omit<CertificationHome, 'badges'> = {
  has_placement: true,
  certified: [
    { topic: '链表', level: '熟练', date: '2026-07-12', score: 92, verify_code: 'WP-LIST-7F3A' },
    { topic: '排序', level: '熟练', date: '2026-07-19', score: 88, verify_code: 'WP-SORT-2E9C' },
  ],
  available_exams: [
    { id: 'cert-pointer', topic: '指针', question_count: 6, time_limit_min: 15, pass_score: 80 },
    { id: 'cert-recursion', topic: '递归', question_count: 6, time_limit_min: 15, pass_score: 80 },
    { id: 'cert-dp', topic: '动态规划', question_count: 6, time_limit_min: 20, pass_score: 80 },
  ],
  next_available_days: 3,
}

/** 指针认证试题（mock 期间其他认证复用同一套题，仅主题名不同） */
const POINTER_EXAM: CertExam = {
  info: { id: 'cert-pointer', topic: '指针', question_count: 6, time_limit_min: 15, pass_score: 80 },
  questions: [
    {
      id: 'q1',
      kind: 'mcq',
      prompt: 'int a = 5; int *p = &a; *p = 10; 之后 a 的值是？',
      options: ['5', '10', '未定义', '编译错误'],
    },
    {
      id: 'q2',
      kind: 'mcq',
      prompt: 'free(p) 之后，指针 p 本身变成什么？',
      options: ['NULL', '悬空指针（值不变但目标已释放）', '自动销毁', '指向堆顶'],
    },
    {
      id: 'q3',
      kind: 'mcq',
      prompt: '对 int arr[10]，arr 与 &arr[0] 的关系是？',
      options: ['值相等', '类型完全相同', 'arr 多一级间接', '毫无关系'],
    },
    {
      id: 'q4',
      kind: 'mcq',
      prompt: '32 位系统下 int *p; p++ 让 p 前进多少字节？',
      options: ['1', '2', '4', '8'],
    },
    {
      id: 'q5',
      kind: 'code',
      prompt: '手写 swap：通过指针交换两个 int 的值。',
      starter_code: 'void swap(int *a, int *b) {\n    \n}',
    },
    {
      id: 'q6',
      kind: 'code',
      prompt: '写一个函数 find，接收 int* 数组首地址和长度，返回最大值所在位置的指针；空数组返回 NULL。',
      starter_code: 'int* find(int *arr, int n) {\n    \n}',
    },
  ],
}

/** 定级测试：5 题 5 分钟，覆盖审阅/调试/实现 */
const PLACEMENT_EXAM: CertExam = {
  info: { id: 'placement', topic: '定级测试', question_count: 5, time_limit_min: 5, pass_score: 0 },
  questions: [
    {
      id: 'p1',
      kind: 'mcq',
      prompt: '读代码找 bug：for (i = 0; i <= n; i++) sum += arr[i]; 问题在哪？',
      options: ['越界访问 arr[n]', 'sum 类型不对', '循环方向错了', '没有 bug'],
    },
    {
      id: 'p2',
      kind: 'mcq',
      prompt: '下面哪段代码会死循环？',
      options: [
        'while (x > 0) { x -= 2; }（x 为奇数正数）',
        'for (i = 0; i < 10; i++)',
        'while (x != 0) { x = x / 2; }',
        'do { x--; } while (x > 0);',
      ],
    },
    {
      id: 'p3',
      kind: 'mcq',
      prompt: '测试发现 quicksort([2,2,1]) 返回 [1,2]，最可能丢了什么？',
      options: ['与 pivot 相等的元素', '最小值', '第一个元素', '什么都不缺'],
    },
    {
      id: 'p4',
      kind: 'code',
      prompt: '手写：返回字符串中第一个不重复的字符下标，没有则返回 -1。',
      starter_code: 'def first_unique(s):\n    ',
    },
    {
      id: 'p5',
      kind: 'code',
      prompt: '手写：判断一个整数是否为 2 的幂。',
      starter_code: 'def is_power_of_two(n):\n    ',
    },
  ],
}

/** 判分答案表：mcq 比对选项文本；code 检查规范化后包含关键片段 */
const ANSWER_KEY: Record<string, { correct?: string; includes?: string[] }> = {
  q1: { correct: '10' },
  q2: { correct: '悬空指针（值不变但目标已释放）' },
  q3: { correct: '值相等' },
  q4: { correct: '4' },
  q5: { includes: ['*a=*b', '*b='] },
  q6: { includes: ['NULL'] },
  p1: { correct: '越界访问 arr[n]' },
  p2: { correct: 'while (x > 0) { x -= 2; }（x 为奇数正数）' },
  p3: { correct: '与 pivot 相等的元素' },
  p4: { includes: ['return'] },
  p5: { includes: ['n>0'] },
}

const CERT_BY_ID: Record<string, { topic: string; verify_prefix: string }> = {
  'cert-pointer': { topic: '指针', verify_prefix: 'WP-PTR' },
  'cert-recursion': { topic: '递归', verify_prefix: 'WP-REC' },
  'cert-dp': { topic: '动态规划', verify_prefix: 'WP-DP' },
}

export function getMockExam(id: string): CertExam {
  if (id === 'placement') return PLACEMENT_EXAM
  const meta = CERT_BY_ID[id]
  // mock 期间所有认证共用指针套题，仅替换主题名
  return {
    ...POINTER_EXAM,
    info: { ...POINTER_EXAM.info, id, topic: meta?.topic ?? '指针' },
  }
}

/** 本地判分：mcq 对答案表，code 检查关键片段（不含徽章判定，保持纯函数） */
export function judgeExam(examId: string, answers: CertAnswer[]): Omit<CertResult, 'new_badges'> {
  const exam = getMockExam(examId)
  const perQuestion = exam.questions.map((q) => {
    const answer = answers.find((a) => a.question_id === q.id)?.answer ?? ''
    const key = ANSWER_KEY[q.id]
    let correct = false
    if (key?.correct) correct = answer === key.correct
    else if (key?.includes) {
      const normalized = answer.replace(/\s+/g, '')
      correct = key.includes.every((frag) => normalized.includes(frag.replace(/\s+/g, '')))
    }
    return { question_id: q.id, correct }
  })

  const correctCount = perQuestion.filter((p) => p.correct).length
  const score = Math.round((correctCount / exam.questions.length) * 100)
  const passed = examId !== 'placement' && score >= exam.info.pass_score

  let certificate: CertRecord | null = null
  if (passed) {
    const meta = CERT_BY_ID[examId] ?? { topic: exam.info.topic, verify_prefix: 'WP-CERT' }
    certificate = {
      topic: meta.topic,
      level: score >= 95 ? '精通' : '熟练',
      date: new Date().toISOString().slice(0, 10),
      score,
      verify_code: `${meta.verify_prefix}-${Math.random().toString(16).slice(2, 6).toUpperCase()}`,
    }
  }
  return { score, passed, certificate, per_question: perQuestion }
}

/** 认证 home：静态部分 + 实时徽章墙 */
export function getMockCertHome(): CertificationHome {
  return { ...CERT_HOME_MOCK, badges: getMockBadgeWall() }
}

/** 交卷：判分 + 徽章评估（本次提交上下文喂给判定引擎） */
export function submitMockExam(examId: string, answers: CertAnswer[]): CertResult {
  const result = judgeExam(examId, answers)
  const new_badges = awardMockBadges({
    placementDone: examId === 'placement',
    examPassed: result.passed,
    examScore: result.score,
    examLevel: result.certificate?.level,
    isNight: isNightHour(),
  })
  return { ...result, new_badges }
}

/** 定级结果 → 三轴初始等级（1-5） */
export function placementLevels(score: number): { review: number; debug: number; implement: number } {
  const base = 1 + Math.min(4, Math.floor(score / 25))
  return { review: base, debug: Math.max(1, base - (score < 50 ? 1 : 0)), implement: base }
}
