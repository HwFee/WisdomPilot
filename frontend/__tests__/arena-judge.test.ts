/**
 * 调试竞技场 mock 判题测试
 */
import { judgeArenaCode } from '@/lib/api/deck/mock/arena'

const FIXED = `def median(nums):
    nums = sorted(nums)
    n = len(nums)
    mid = n // 2
    if n % 2 == 1:
        return nums[mid]
    lo = mid - 1
    return (nums[lo] + nums[mid]) / 2`

const LOOP_ONLY_FIXED = `def median(nums):
    nums = sorted(nums)
    n = len(nums)
    mid = n // 2
    if n % 2 == 1:
        return nums[mid]
    lo = mid - 1
    return (nums[lo] + nums[mid + 1]) / 2`

const BUGGY = `def median(nums):
    lo = mid
    while lo > mid - 1:
        lo -= 1
    return (nums[lo] + nums[mid + 1]) / 2`

describe('judgeArenaCode', () => {
  it('两处都修复 → 5/5 solved +23', () => {
    const r = judgeArenaCode(FIXED)
    expect(r.solved).toBe(true)
    expect(r.passed).toBe(5)
    expect(r.score_delta).toBe(23)
  })

  it('只修死循环 → 3/5 未通过', () => {
    const r = judgeArenaCode(LOOP_ONLY_FIXED)
    expect(r.solved).toBe(false)
    expect(r.passed).toBe(3)
  })

  it('未修复 → 2/5 未通过', () => {
    const r = judgeArenaCode(BUGGY)
    expect(r.solved).toBe(false)
    expect(r.passed).toBe(2)
  })

  it('空白差异不影响判定', () => {
    const r = judgeArenaCode(FIXED.replace('lo = mid - 1', 'lo=mid-1'))
    expect(r.solved).toBe(true)
  })
})
