/* 基本功认证 mock：徽章墙 + 考试 + 本地判分（真实后端就位后由服务端判分） */

import type {
  AbilityAxis,
  AxisKey,
  CertAnswer,
  CertExam,
  CertRecord,
  CertResult,
  CertificationHome,
} from '../types'
import { awardMockBadges, getMockBadgeWall, isNightHour } from './badges'

/** 训练指纹轴代码（§3.5 P-11）：审阅→R / 调试→D / 实现→I */
const FINGERPRINT_AXIS_CODES: Record<AxisKey, string> = {
  review: 'R',
  debug: 'D',
  implement: 'I',
}

/** 三轴顺序固定（review → debug → implement），与后端 AXES 一致 */
const FINGERPRINT_AXES: AxisKey[] = ['review', 'debug', 'implement']

/**
 * 根据三轴等级生成训练指纹短码（如 R3-D1-I4）。
 *
 * 只暴露三轴等级的粗粒度信息（隐私约束 4），不含任何具体弱点知识点。
 * 缺失的轴按 LV.1（未定级默认）计，与后端 service.training_fingerprint 一致。
 */
export function trainingFingerprint(axes: AbilityAxis[]): string {
  const levelByAxis = new Map(axes.map((a) => [a.key, a.level]))
  return FINGERPRINT_AXES.map(
    (axis) => `${FINGERPRINT_AXIS_CODES[axis]}${levelByAxis.get(axis) ?? 1}`,
  ).join('-')
}

/** home 静态部分；badges 字段由 getMockCertHome 按当前解锁状态实时拼装 */
export const CERT_HOME_MOCK: Omit<CertificationHome, 'badges'> = {
  has_placement: true,
  // 设计稿示例指纹：审阅 LV.3 / 调试 LV.1 / 实现 LV.4
  fingerprint: 'R3-D1-I4',
  certified: [
    { topic: '链表', level: '熟练', date: '2026-07-12', score: 92, verify_code: 'WP-LIST-7F3A' },
    { topic: '排序', level: '熟练', date: '2026-07-19', score: 88, verify_code: 'WP-SORT-2E9C' },
  ],
  available_exams: [
    { id: 'cert-pointer', topic: '指针', question_count: 6, time_limit_min: 15, pass_score: 80 },
    { id: 'cert-recursion', topic: '递归', question_count: 6, time_limit_min: 15, pass_score: 80 },
    { id: 'cert-sorting', topic: '排序算法', question_count: 6, time_limit_min: 15, pass_score: 80 },
    { id: 'cert-linkedlist', topic: '链表操作', question_count: 6, time_limit_min: 15, pass_score: 80 },
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
      starter_code: '#include <stdlib.h>\nint* find(int *arr, int n) {\n    \n}',
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
        'while (x != 0) { x = x - 2; }（x 为奇数正数）',
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

/** 递归认证试题：6 题（4 MCQ + 2 code） */
const RECURSION_EXAM: CertExam = {
  info: { id: 'cert-recursion', topic: '递归', question_count: 6, time_limit_min: 15, pass_score: 80 },
  questions: [
    {
      id: 'q1',
      kind: 'mcq',
      prompt: '递归函数缺少基例（终止条件）会导致什么？',
      options: ['编译错误', '无限递归导致栈溢出', '返回 None', '语法错误'],
    },
    {
      id: 'q2',
      kind: 'mcq',
      prompt: 'def f(n):\n    if n <= 1: return 1\n    return n * f(n-1)\n上述函数计算的是什么？',
      options: ['斐波那契数', '阶乘', '幂运算', '排列数'],
    },
    {
      id: 'q3',
      kind: 'mcq',
      prompt: '朴素递归实现斐波那契数列 fib(n) = fib(n-1) + fib(n-2) 的主要性能问题是什么？',
      options: ['递归层数太深', '大量重复计算（同一 fib(k) 被多次调用）', '返回值溢出', '没有性能问题'],
    },
    {
      id: 'q4',
      kind: 'mcq',
      prompt: '尾递归优化（tail call optimization）的好处是什么？',
      options: ['减少代码行数', '复用栈帧，避免栈溢出', '提高数值精度', '自动并行执行'],
    },
    {
      id: 'q5',
      kind: 'code',
      prompt: '手写：用递归实现字符串反转。例如 reverse_str("hello") 返回 "olleh"。',
      starter_code: 'def reverse_str(s):\n    ',
    },
    {
      id: 'q6',
      kind: 'code',
      prompt: '手写：用递归实现幂运算 power(base, exp)，返回 base 的 exp 次方。不使用 ** 运算符。',
      starter_code: 'def power(base, exp):\n    ',
    },
  ],
}

/** 排序算法认证试题：6 题（4 MCQ + 2 code），与后端 seed.py 逐字对齐 */
const SORTING_EXAM: CertExam = {
  info: { id: 'cert-sorting', topic: '排序算法', question_count: 6, time_limit_min: 15, pass_score: 80 },
  questions: [
    {
      id: 'q1',
      kind: 'mcq',
      prompt: '对一个基本有序的数组做冒泡排序，若实现加入了提前退出标志，最优时间复杂度是？',
      options: ['O(n)', 'O(n log n)', 'O(n²)', 'O(1)'],
    },
    {
      id: 'q2',
      kind: 'mcq',
      prompt: '快速排序的平均时间复杂度是？',
      options: ['O(n log n)', 'O(n²)', 'O(n)', 'O(log n)'],
    },
    {
      id: 'q3',
      kind: 'mcq',
      prompt: '归并排序的空间复杂度是？',
      options: ['O(n)', 'O(1)', 'O(log n)', 'O(n log n)'],
    },
    {
      id: 'q4',
      kind: 'mcq',
      prompt: '下列哪个排序算法是不稳定的？',
      options: ['快速排序', '冒泡排序', '插入排序', '归并排序'],
    },
    {
      id: 'q5',
      kind: 'code',
      prompt: '手写：实现冒泡排序 bubble_sort(arr)，升序排序并返回数组。',
      starter_code: 'def bubble_sort(arr):\n    ',
    },
    {
      id: 'q6',
      kind: 'code',
      prompt: '手写：实现快速排序 quicksort(arr)，升序排序并返回数组。',
      starter_code: 'def quicksort(arr):\n    ',
    },
  ],
}

/** 链表操作认证试题：6 题（4 MCQ + 2 code），与后端 seed.py 逐字对齐 */
const LINKEDLIST_EXAM: CertExam = {
  info: { id: 'cert-linkedlist', topic: '链表操作', question_count: 6, time_limit_min: 15, pass_score: 80 },
  questions: [
    {
      id: 'q1',
      kind: 'mcq',
      prompt: '在单链表头部插入一个新节点的时间复杂度是？',
      options: ['O(1)', 'O(n)', 'O(log n)', 'O(n²)'],
    },
    {
      id: 'q2',
      kind: 'mcq',
      prompt: '迭代反转单链表时，通常需要同时维护几个指针？',
      options: ['3 个（prev / cur / next）', '1 个', '2 个', '4 个'],
    },
    {
      id: 'q3',
      kind: 'mcq',
      prompt: '判断单链表是否存在环，常用的方法有？',
      options: ['快慢双指针', '哈希集合记录已访问节点', '两者都可', '反转链表后比较'],
    },
    {
      id: 'q4',
      kind: 'mcq',
      prompt: '已知某节点的前驱节点，删除该节点的时间复杂度是？',
      options: ['O(1)', 'O(n)', 'O(log n)', 'O(n log n)'],
    },
    {
      id: 'q5',
      kind: 'code',
      prompt: '手写：实现 remove_nth_from_end(arr, n)，删除数组倒数第 n 个元素并返回新数组（模拟删除链表倒数第 n 个节点）。',
      starter_code: 'def remove_nth_from_end(arr, n):\n    ',
    },
    {
      id: 'q6',
      kind: 'code',
      prompt: '手写：实现 merge_two_sorted(a, b)，合并两个升序数组并返回升序数组（模拟合并两个有序链表）。',
      starter_code: 'def merge_two_sorted(a, b):\n    ',
    },
  ],
}

/** 判分答案表：mcq 比对选项文本；code 检查规范化后包含关键片段（与后端 seed.py 逐字对齐） */
const ANSWER_KEY: Record<string, { correct?: string; includes?: string[] }> = {
  q1: { correct: '10' },
  q2: { correct: '悬空指针（值不变但目标已释放）' },
  q3: { correct: '值相等' },
  q4: { correct: '4' },
  q5: { includes: ['*a=*b', '*b='] },
  q6: { includes: ['NULL', 'arr[i]||*(arr+i'] },
  p1: { correct: '越界访问 arr[n]' },
  p2: { correct: 'while (x != 0) { x = x - 2; }（x 为奇数正数）' },
  p3: { correct: '与 pivot 相等的元素' },
  p4: { includes: ['==1', 'return-1'] },
  p5: { includes: ['n>0||n<=0||n<1', 'n&(n-1)||n%2||n//=2'] },
  // 各认证的 qid 相同（q1-q6），用 exam_id 前缀区分答案表避免冲突
  'rec-q1': { correct: '无限递归导致栈溢出' },
  'rec-q2': { correct: '阶乘' },
  'rec-q3': { correct: '大量重复计算（同一 fib(k) 被多次调用）' },
  'rec-q4': { correct: '复用栈帧，避免栈溢出' },
  'rec-q5': { includes: ['reverse_str(s[1:])||reverse_str(s[:-1])||s[::-1]'] },
  'rec-q6': { includes: ['return1', 'power(base,exp-1)||power(base,exp-2)||power(base,exp//2)'] },
  'sort-q1': { correct: 'O(n)' },
  'sort-q2': { correct: 'O(n log n)' },
  'sort-q3': { correct: 'O(n)' },
  'sort-q4': { correct: '快速排序' },
  'sort-q5': {
    includes: ['arr[j+1]||arr[i+1]', 'arr[j]>arr[j+1]||arr[j+1]<arr[j]||arr[i]>arr[i+1]||arr[i+1]<arr[i]'],
  },
  'sort-q6': { includes: ['pivot||partition', 'quicksort('] },
  'list-q1': { correct: 'O(1)' },
  'list-q2': { correct: '3 个（prev / cur / next）' },
  'list-q3': { correct: '两者都可' },
  'list-q4': { correct: 'O(1)' },
  'list-q5': { includes: ['len(arr)-n', 'return'] },
  'list-q6': { includes: ['while||sorted(', 'append||sorted('] },
}

const CERT_BY_ID: Record<string, { topic: string; verify_prefix: string }> = {
  'cert-pointer': { topic: '指针', verify_prefix: 'WP-PTR' },
  'cert-recursion': { topic: '递归', verify_prefix: 'WP-REC' },
  'cert-sorting': { topic: '排序算法', verify_prefix: 'WP-SORT' },
  'cert-linkedlist': { topic: '链表操作', verify_prefix: 'WP-LIST' },
}

/** 各认证 qid 相同时的答案表前缀 */
const EXAM_KEY_PREFIX: Record<string, string> = {
  'cert-recursion': 'rec-',
  'cert-sorting': 'sort-',
  'cert-linkedlist': 'list-',
}

export function getMockExam(id: string): CertExam {
  if (id === 'placement') return PLACEMENT_EXAM
  if (id === 'cert-recursion') return RECURSION_EXAM
  if (id === 'cert-sorting') return SORTING_EXAM
  if (id === 'cert-linkedlist') return LINKEDLIST_EXAM
  return POINTER_EXAM
}

/** 本地判分：mcq 对答案表，code 检查关键片段（不含徽章判定，保持纯函数） */
export function judgeExam(examId: string, answers: CertAnswer[]): Omit<CertResult, 'new_badges'> {
  const exam = getMockExam(examId)
  // 各认证的 qid 相同（q1-q6），用前缀区分答案表
  const keyPrefix = EXAM_KEY_PREFIX[examId] ?? ''
  const perQuestion = exam.questions.map((q) => {
    const answer = answers.find((a) => a.question_id === q.id)?.answer ?? ''
    const key = ANSWER_KEY[`${keyPrefix}${q.id}`]
    let correct = false
    if (key?.correct) correct = answer === key.correct
    else if (key?.includes) {
      const normalized = answer.replace(/\s+/g, '')
      // 片段内 "||" 分隔备选写法（任一命中即算该片段命中），与后端 judge_cert_answer 逐字对齐
      correct = key.includes.every((frag) =>
        frag.split('||').some((alt) => normalized.includes(alt.replace(/\s+/g, ''))),
      )
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

/**
 * 定级结果 → 三轴初始等级（1-5）。
 *
 * 规则与后端 service.placement_levels_from_score（§8）一致：
 * base = 1 + min(4, floor(score / 25))；debug 恒低一档（最低 LV.1），
 * review/implement 取 base。mock 与后端共用同一规则，防止定级仪式页
 * 与 P-10 画像的等级与真实后端漂移。
 */
export function placementLevels(score: number): { review: number; debug: number; implement: number } {
  const base = 1 + Math.min(4, Math.floor(score / 25))
  return { review: base, debug: Math.max(1, base - 1), implement: base }
}

/** 定级三轴等级 → 训练指纹短码（P-11 同源：复用轴代码表与固定顺序，R-D-I） */
export function fingerprintFromPlacement(levels: {
  review: number
  debug: number
  implement: number
}): string {
  return FINGERPRINT_AXES.map((axis) => `${FINGERPRINT_AXIS_CODES[axis]}${levels[axis]}`).join('-')
}
