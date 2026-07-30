/* 调试竞技场 mock：今日挑战 + 本地判题（真实后端就位后由 Judge0 判定） */

import type { ArenaChallenge, ArenaHome, ArenaRunResult } from '../types'
import { awardMockBadges, isNightHour } from './badges'

/** DEBUG-0091：Python 中位数 -- 偶数分支死循环 + 右中位索引错 */
export const CHALLENGE_0091: ArenaChallenge = {
  id: 'DEBUG-0091',
  title: '中位数统计 · 测试全挂',
  language: 'python',
  code: `def median(nums):
    """返回列表中位数 -- AI 生成，测试全挂，待修复"""
    nums = sorted(nums)
    n = len(nums)
    mid = n // 2
    if n % 2 == 1:
        return nums[mid]
    # 偶数个：找中间两个数
    lo = mid
    while lo > mid - 1:
        lo -= 1
        # 没有退出条件 -- lo 会一直减下去
    return (nums[lo] + nums[mid + 1]) / 2`,
  failing_output: `$ pytest test_median.py -v
test_median.py::test_odd            PASSED   [ 20%]
test_median.py::test_single         PASSED   [ 40%]
test_median.py::test_even           TIMEOUT  [ 60%] 执行超过 5s（疑似死循环）
test_median.py::test_even_negative  TIMEOUT  [ 80%] 执行超过 5s（疑似死循环）
test_median.py::test_even_unsorted  TIMEOUT  [100%] 执行超过 5s（疑似死循环）

=================== 2 passed, 3 timeout in 15.42s ===================`,
  time_limit_sec: 600,
  difficulty: 3,
}

/** DEBUG-0092：Python 二分查找 -- right = len(arr) 越界 */
export const CHALLENGE_0092: ArenaChallenge = {
  id: 'DEBUG-0092',
  title: '二分查找 · 越界',
  language: 'python',
  code: `def binary_search(arr, target):
    """二分查找 -- AI 生成，测试全挂，待修复"""
    left, right = 0, len(arr)
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1`,
  failing_output: `$ pytest test_bsearch.py -v
test_bsearch.py::test_found         PASSED   [ 20%]
test_bsearch.py::test_single        PASSED   [ 40%]
test_bsearch.py::test_not_found     IndexError: list index out of range  [ 60%]
test_bsearch.py::test_last_element  IndexError: list index out of range  [ 80%]
test_bsearch.py::test_empty         PASSED   [100%]

=================== 3 passed, 2 failed in 0.09s ===================
right 初始化为 len(arr)，当 target 大于所有元素时 mid 越界。`,
  time_limit_sec: 600,
  difficulty: 2,
}

/** DEBUG-0093：C 字符串反转 -- return dest 应为 return result */
export const CHALLENGE_0093: ArenaChallenge = {
  id: 'DEBUG-0093',
  title: '字符串反转 · 指针丢失',
  language: 'c',
  code: `#include <stdlib.h>
#include <string.h>

char* reverse_str(char *s) {
    /* 字符串反转 -- AI 生成，测试全挂，待修复 */
    int len = strlen(s);
    char *result = malloc(len + 1);
    char *dest = result;
    char *src = s + len - 1;
    while (src >= s) {
        *dest++ = *src--;
    }
    *dest = '\\0';
    return dest;
}`,
  failing_output: `$ gcc -o test test.c && ./test
test_str_reverse("hello")    -> "" (expected "olleh")    FAIL
test_str_reverse("a")        -> "" (expected "a")        FAIL
test_str_reverse("")         -> "" (expected "")          OK
test_str_reverse("abcdef")   -> "" (expected "fedcba")   FAIL
test_str_reverse("12345")    -> "" (expected "54321")    FAIL

======================== 1/5 tests passed ========================
返回的是 dest（已移到末尾），应返回 result（指向字符串开头）。`,
  time_limit_sec: 600,
  difficulty: 3,
}

/** DEBUG-0094：Python 去重计数 -- 缺少 if w not in seen 判断 */
export const CHALLENGE_0094: ArenaChallenge = {
  id: 'DEBUG-0094',
  title: '去重计数 · 逻辑错误',
  language: 'python',
  code: `def count_unique(words):
    """去重计数 -- AI 生成，测试全挂，待修复"""
    seen = set()
    count = 0
    for w in words:
        seen.add(w)
        count += 1
    return count`,
  failing_output: `$ pytest test_unique.py -v
test_unique.py::test_empty          PASSED   [ 20%]
test_unique.py::test_all_unique     PASSED   [ 40%]
test_unique.py::test_all_same       FAILED   assert 3 == 1  [ 60%]
test_unique.py::test_mixed          FAILED   assert 4 == 2  [ 80%]
test_unique.py::test_with_numbers   FAILED   assert 3 == 2  [100%]

=================== 2 passed, 3 failed in 0.05s ===================
count 对每个 word 都 +1，没有跳过已见元素。需要加 if w not in seen 判断。`,
  time_limit_sec: 600,
  difficulty: 3,
}

/** DEBUG-0095：Python 阶乘 -- 缺少递归出口 */
export const CHALLENGE_0095: ArenaChallenge = {
  id: 'DEBUG-0095',
  title: '阶乘 · 栈溢出',
  language: 'python',
  code: `def factorial(n):
    """阶乘 -- AI 生成，测试全挂，待修复"""
    return n * factorial(n - 1)`,
  failing_output: `$ pytest test_factorial.py -v
test_factorial.py::test_zero     RecursionError  [ 20%]
test_factorial.py::test_one      RecursionError  [ 40%]
test_factorial.py::test_three    RecursionError  [ 60%]
test_factorial.py::test_five     RecursionError  [ 80%]
test_factorial.py::test_ten      RecursionError  [100%]

=================== 0 passed, 5 failed in 0.12s ===================
RecursionError: maximum recursion depth exceeded
缺少递归出口（基例），需要加 if n <= 1: return 1。`,
  time_limit_sec: 600,
  difficulty: 2,
}

/** 所有挑战的映射 */
const CHALLENGES: Record<string, ArenaChallenge> = {
  'DEBUG-0091': CHALLENGE_0091,
  'DEBUG-0092': CHALLENGE_0092,
  'DEBUG-0093': CHALLENGE_0093,
  'DEBUG-0094': CHALLENGE_0094,
  'DEBUG-0095': CHALLENGE_0095,
}

/** 各挑战的模拟全通过输出 */
const SOLVED_OUTPUTS: Record<string, string> = {
  'DEBUG-0091': `$ pytest test_median.py -v
test_median.py::test_odd            PASSED   [ 20%]
test_median.py::test_single         PASSED   [ 40%]
test_median.py::test_even           PASSED   [ 60%]
test_median.py::test_even_negative  PASSED   [ 80%]
test_median.py::test_even_unsorted  PASSED   [100%]

======================== 5 passed in 0.08s ========================`,
  'DEBUG-0092': `$ pytest test_bsearch.py -v
test_bsearch.py::test_found         PASSED   [ 20%]
test_bsearch.py::test_single        PASSED   [ 40%]
test_bsearch.py::test_not_found     PASSED   [ 60%]
test_bsearch.py::test_last_element  PASSED   [ 80%]
test_bsearch.py::test_empty         PASSED   [100%]

======================== 5 passed in 0.06s ========================`,
  'DEBUG-0093': `$ gcc -o test test.c && ./test
test_str_reverse("hello")    -> "olleh"   OK
test_str_reverse("a")        -> "a"       OK
test_str_reverse("")         -> ""        OK
test_str_reverse("abcdef")   -> "fedcba"  OK
test_str_reverse("12345")    -> "54321"   OK

======================== 5/5 tests passed ========================`,
  'DEBUG-0094': `$ pytest test_unique.py -v
test_unique.py::test_empty          PASSED   [ 20%]
test_unique.py::test_all_unique     PASSED   [ 40%]
test_unique.py::test_all_same       PASSED   [ 60%]
test_unique.py::test_mixed          PASSED   [ 80%]
test_unique.py::test_with_numbers   PASSED   [100%]

======================== 5 passed in 0.04s ========================`,
  'DEBUG-0095': `$ pytest test_factorial.py -v
test_factorial.py::test_zero     PASSED   [ 20%]
test_factorial.py::test_one      PASSED   [ 40%]
test_factorial.py::test_five     PASSED   [ 60%]
test_factorial.py::test_three    PASSED   [ 80%]
test_factorial.py::test_ten      PASSED   [100%]

======================== 5 passed in 0.03s ========================`,
}

/** DEBUG-0091 部分通过的输出 */
const PARTIAL_0091 = `$ pytest test_median.py -v
test_median.py::test_even           FAILED   assert 5.0 == 4.5
test_median.py::test_even_negative  FAILED   assert -4.0 == -4.5

=================== 3 passed, 2 failed in 0.11s ===================
右中位索引还有问题：偶数个时中间两个是 nums[mid-1] 和 nums[mid]。`

/**
 * mock 判题：按 challenge_id 分发，去掉全部空白后做字符串匹配。
 * 每个挑战有独立的修复检测规则，与后端 service.judge_arena_code 完全对齐。
 * （不含徽章判定，保持纯函数）
 */
export function judgeArenaCode(challengeId: string, code: string): Omit<ArenaRunResult, 'new_badges'> {
  const normalized = code.replace(/\s+/g, '')
  const challenge = CHALLENGES[challengeId]
  const failingOutput = challenge?.failing_output ?? ''
  const solvedOutput = SOLVED_OUTPUTS[challengeId] ?? ''

  switch (challengeId) {
    case 'DEBUG-0091': {
      const ruleLoop = normalized.includes('lo=mid-1')
      const ruleIndex = normalized.includes('nums[lo]+nums[mid])')
      if (ruleLoop && ruleIndex) {
        return { passed: 5, total: 5, output: solvedOutput, solved: true, score_delta: 23 }
      }
      if (ruleLoop) {
        return { passed: 3, total: 5, output: PARTIAL_0091, solved: false, score_delta: 0 }
      }
      return { passed: 2, total: 5, output: failingOutput, solved: false, score_delta: 0 }
    }
    case 'DEBUG-0092': {
      const fixed = normalized.includes('len(arr)-1')
      if (fixed) {
        return { passed: 5, total: 5, output: solvedOutput, solved: true, score_delta: 23 }
      }
      return { passed: 2, total: 5, output: failingOutput, solved: false, score_delta: 0 }
    }
    case 'DEBUG-0093': {
      const fixed = normalized.includes('returnresult')
      if (fixed) {
        return { passed: 5, total: 5, output: solvedOutput, solved: true, score_delta: 23 }
      }
      return { passed: 2, total: 5, output: failingOutput, solved: false, score_delta: 0 }
    }
    case 'DEBUG-0094': {
      const fixed = normalized.includes('notinseen')
      if (fixed) {
        return { passed: 5, total: 5, output: solvedOutput, solved: true, score_delta: 23 }
      }
      return { passed: 2, total: 5, output: failingOutput, solved: false, score_delta: 0 }
    }
    case 'DEBUG-0095': {
      const fixed = normalized.includes('return1')
      if (fixed) {
        return { passed: 5, total: 5, output: solvedOutput, solved: true, score_delta: 23 }
      }
      return { passed: 0, total: 5, output: failingOutput, solved: false, score_delta: 0 }
    }
    default:
      return { passed: 0, total: 0, output: failingOutput, solved: false, score_delta: 0 }
  }
}

/** 提交判题 + 徽章评估（胜场 / 连胜上下文喂给判定引擎） */
export function submitMockArena(challengeId: string, code: string): ArenaRunResult {
  const result = judgeArenaCode(challengeId, code)
  const new_badges = awardMockBadges({
    arenaSolved: result.solved,
    arenaWinStreak: result.solved ? ARENA_HOME_MOCK.profile.win_streak + 1 : 0,
    isNight: isNightHour(),
  })
  return { ...result, new_badges }
}

export const ARENA_HOME_MOCK: ArenaHome = {
  profile: { tier: '铂金 II', rating: 1847, week_rank: 47, rank_delta: 12, win_streak: 3 },
  challenge: CHALLENGE_0091,
  leaderboard: [
    { rank: 1, name: 'NightOwl', rating: 2412, solved_today: 6 },
    { rank: 2, name: '递归终结者', rating: 2388, solved_today: 4 },
    { rank: 3, name: 'segfault', rating: 2301, solved_today: 5 },
    { rank: 4, name: '青柠', rating: 2254, solved_today: 3 },
    { rank: 5, name: 'null_ptr', rating: 2198, solved_today: 4 },
    { rank: 6, name: '栈溢出', rating: 2150, solved_today: 2 },
    { rank: 7, name: 'Momo', rating: 2105, solved_today: 3 },
    { rank: 8, name: '断点狂魔', rating: 2066, solved_today: 2 },
    { rank: 9, name: 'c0ffee', rating: 2019, solved_today: 1 },
    { rank: 10, name: '阿白', rating: 1988, solved_today: 2 },
    { rank: 47, name: '清源', rating: 1847, solved_today: 1, is_self: true },
  ],
}
