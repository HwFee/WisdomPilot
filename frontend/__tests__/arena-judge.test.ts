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
  it('DEBUG-0091 两处都修复 -> 5/5 solved +23', () => {
    const r = judgeArenaCode('DEBUG-0091', FIXED)
    expect(r.solved).toBe(true)
    expect(r.passed).toBe(5)
    expect(r.score_delta).toBe(23)
  })

  it('DEBUG-0091 只修死循环 -> 3/5 未通过', () => {
    const r = judgeArenaCode('DEBUG-0091', LOOP_ONLY_FIXED)
    expect(r.solved).toBe(false)
    expect(r.passed).toBe(3)
  })

  it('DEBUG-0091 未修复 -> 2/5 未通过', () => {
    const r = judgeArenaCode('DEBUG-0091', BUGGY)
    expect(r.solved).toBe(false)
    expect(r.passed).toBe(2)
  })

  it('DEBUG-0091 空白差异不影响判定', () => {
    const r = judgeArenaCode('DEBUG-0091', FIXED.replace('lo = mid - 1', 'lo=mid-1'))
    expect(r.solved).toBe(true)
  })

  it('DEBUG-0092 修复 right 初始化 -> 5/5 solved', () => {
    const fixed = `def binary_search(arr, target):
      left, right = 0, len(arr) - 1
      while left <= right:
          mid = (left + right) // 2
          if arr[mid] == target:
              return mid
          elif arr[mid] < target:
              left = mid + 1
          else:
              right = mid - 1
      return -1`
    const r = judgeArenaCode('DEBUG-0092', fixed)
    expect(r.solved).toBe(true)
    expect(r.passed).toBe(5)
  })

  it('DEBUG-0093 修复 return result -> 5/5 solved', () => {
    const fixed = `char* reverse_str(char *s) {
      int len = strlen(s);
      char *result = malloc(len + 1);
      char *dest = result;
      char *src = s + len - 1;
      while (src >= s) { *dest++ = *src--; }
      *dest = '\\0';
      return result;
    }`
    const r = judgeArenaCode('DEBUG-0093', fixed)
    expect(r.solved).toBe(true)
    expect(r.passed).toBe(5)
  })

  it('DEBUG-0094 添加 not in seen -> 5/5 solved', () => {
    const fixed = `def count_unique(words):
      seen = set()
      count = 0
      for w in words:
          if w not in seen:
              seen.add(w)
              count += 1
      return count`
    const r = judgeArenaCode('DEBUG-0094', fixed)
    expect(r.solved).toBe(true)
    expect(r.passed).toBe(5)
  })

  it('DEBUG-0095 添加递归出口 -> 5/5 solved', () => {
    const fixed = `def factorial(n):
      if n <= 1:
          return 1
      return n * factorial(n - 1)`
    const r = judgeArenaCode('DEBUG-0095', fixed)
    expect(r.solved).toBe(true)
    expect(r.passed).toBe(5)
  })
})
