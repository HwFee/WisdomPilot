/* 调试竞技场 mock：今日挑战 + 本地判题（真实后端就位后由 Judge0 判定） */

import type { ArenaChallenge, ArenaHome, ArenaRunResult } from '../types'

/** 今日挑战：Python 中位数 —— 偶数分支死循环 + 右中位索引错 */
export const CHALLENGE_0091: ArenaChallenge = {
  id: 'DEBUG-0091',
  title: '中位数统计 · 测试全挂',
  language: 'python',
  code: `def median(nums):
    """返回列表中位数 —— AI 生成，测试全挂，待修复"""
    nums = sorted(nums)
    n = len(nums)
    mid = n // 2
    if n % 2 == 1:
        return nums[mid]
    # 偶数个：找中间两个数
    lo = mid
    while lo > mid - 1:
        lo -= 1
        # 没有退出条件 —— lo 会一直减下去
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

/**
 * mock 判题规则（去掉全部空白后匹配）：
 * - rule_loop：包含 "lo=mid-1"（删掉死循环，直接取左中位）
 * - rule_index：包含 "nums[lo]+nums[mid])"（右中位是 nums[mid] 不是 nums[mid+1]）
 * 两条都修 → 5/5 通过；只修死循环 → 3/5；都没修 → 2/5。
 */
export function judgeArenaCode(code: string): ArenaRunResult {
  const normalized = code.replace(/\s+/g, '')
  const ruleLoop = normalized.includes('lo=mid-1')
  const ruleIndex = normalized.includes('nums[lo]+nums[mid])')

  if (ruleLoop && ruleIndex) {
    return {
      passed: 5,
      total: 5,
      output: `$ pytest test_median.py -v
test_median.py::test_odd            PASSED   [ 20%]
test_median.py::test_single         PASSED   [ 40%]
test_median.py::test_even           PASSED   [ 60%]
test_median.py::test_even_negative  PASSED   [ 80%]
test_median.py::test_even_unsorted  PASSED   [100%]

======================== 5 passed in 0.08s ========================`,
      solved: true,
      score_delta: 23,
    }
  }
  if (ruleLoop) {
    return {
      passed: 3,
      total: 5,
      output: `$ pytest test_median.py -v
test_median.py::test_even           FAILED   assert 5.0 == 4.5
test_median.py::test_even_negative  FAILED   assert -4.0 == -4.5

=================== 3 passed, 2 failed in 0.11s ===================
右中位索引还有问题：偶数个时中间两个是 nums[mid-1] 和 nums[mid]。`,
      solved: false,
      score_delta: 0,
    }
  }
  return {
    passed: 2,
    total: 5,
    output: CHALLENGE_0091.failing_output,
    solved: false,
    score_delta: 0,
  }
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
