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

  // 新增挑战（DEBUG-0096~0110）：修复实现判过 / 缺陷代码与垃圾提交判不过。
  // 修复实现与后端 scripts/verify_arena_local.py 的 REFERENCE_FIXES 同源。
  const NEW_CHALLENGES: Array<{
    id: string
    fix: string
    buggy: string
    failPassed: number
    failTotal: number
  }> = [
    {
      id: 'DEBUG-0096',
      fix: 'def rotate(nums, k):\n    n = len(nums)\n    k = k % n\n    return nums[-k:] + nums[:-k]',
      buggy: 'return nums[k:] + nums[:k]',
      failPassed: 2,
      failTotal: 5,
    },
    {
      id: 'DEBUG-0097',
      fix: 'for ch in s:\n    if ch in counts:\n        counts[ch] += 1\n    else:\n        counts[ch] = 1',
      buggy: 'counts[ch] = 1',
      failPassed: 3,
      failTotal: 5,
    },
    {
      id: 'DEBUG-0098',
      fix: 'elif ch in ")]}":\n    if not stack:\n        return False\n    if stack.pop() == pairs[ch]:\n        continue\n    return False',
      buggy: 'if stack.pop() == pairs[ch]:\n    continue\nreturn False\nreturn len(stack) == 0',
      failPassed: 5,
      failTotal: 6,
    },
    {
      id: 'DEBUG-0099',
      fix: 'for x in nums[1:]:\n    cur = max(cur + x, x)\n    if cur > best:\n        best = cur',
      buggy: 'cur = cur + x',
      failPassed: 3,
      failTotal: 5,
    },
    {
      id: 'DEBUG-0100',
      fix: 'result.append(s[i - 1] + str(count))\ncount = 1',
      buggy: 'result.append(s[i - 1] + str(count))\ncount = 0',
      failPassed: 2,
      failTotal: 5,
    },
    {
      id: 'DEBUG-0101',
      fix: 'return cleaned == cleaned[::-1]',
      buggy: 'if cleaned[i] != cleaned[i + 1]:\n    return False',
      failPassed: 2,
      failTotal: 5,
    },
    {
      id: 'DEBUG-0102',
      fix: 'while (cur) {\n    Node *next = cur->next;\n    cur->next = prev;\n    prev = cur;\n    cur = next;\n}\nreturn prev;',
      buggy: 'return cur;',
      failPassed: 0,
      failTotal: 5,
    },
    {
      id: 'DEBUG-0103',
      fix: 'while idx < n:\n    nums[idx] = 0\n    idx += 1',
      buggy: 'return nums',
      failPassed: 3,
      failTotal: 5,
    },
    {
      id: 'DEBUG-0104',
      fix: 's = s.strip()\nif not s:\n    return 0',
      buggy: 's = s.strip()\nsign = 1',
      failPassed: 4,
      failTotal: 5,
    },
    {
      id: 'DEBUG-0105',
      fix: 'result[j][i] = matrix[i][j]',
      buggy: 'result[i][j] = matrix[j][i]',
      failPassed: 3,
      failTotal: 5,
    },
    {
      id: 'DEBUG-0106',
      fix: 'idx = (idx + k - 1) % len(people)',
      buggy: 'idx = (idx + k) % len(people)',
      failPassed: 1,
      failTotal: 5,
    },
    {
      id: 'DEBUG-0107',
      fix: 'return n + 1',
      buggy: 'return n',
      failPassed: 3,
      failTotal: 5,
    },
    {
      id: 'DEBUG-0108',
      fix: 'seen = set()\nwhile n != 1:\n    if n in seen:\n        return False\n    seen.add(n)',
      buggy: 'while n != 1:\n    n = sum(int(d) ** 2 for d in str(n))',
      failPassed: 3,
      failTotal: 5,
    },
    {
      id: 'DEBUG-0109',
      fix: 'fast = fast->next->next;',
      buggy: 'fast = fast->next;',
      failPassed: 2,
      failTotal: 5,
    },
    {
      id: 'DEBUG-0110',
      fix: 'return " ".join(reversed(words))',
      buggy: 'return " ".join(word[::-1] for word in words)',
      failPassed: 1,
      failTotal: 5,
    },
  ]

  it.each(NEW_CHALLENGES)('$id 修复实现 -> solved', ({ id, fix }) => {
    const r = judgeArenaCode(id, fix)
    expect(r.solved).toBe(true)
    expect(r.score_delta).toBe(23)
  })

  it.each(NEW_CHALLENGES)('$id 缺陷代码 -> 未通过且 passed 符合实测', ({
    id,
    buggy,
    failPassed,
    failTotal,
  }) => {
    const r = judgeArenaCode(id, buggy)
    expect(r.solved).toBe(false)
    expect(r.passed).toBe(failPassed)
    expect(r.total).toBe(failTotal)
  })

  it.each(NEW_CHALLENGES)('$id 垃圾提交 -> 不通过', ({ id }) => {
    for (const bogus of ['', 'pass', '# 不会写']) {
      expect(judgeArenaCode(id, bogus).solved).toBe(false)
    }
  })
})
