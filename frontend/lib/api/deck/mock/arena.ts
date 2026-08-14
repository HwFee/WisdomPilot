/* 调试竞技场 mock：今日挑战 + 本地判题（真实后端就位后由 Judge0 判定）。
 * 挑战数据与判定规则与后端 seed.py / service.py 逐字对齐（mock 是参考实现）。 */

import type { ArenaChallenge, ArenaHome, ArenaRunResult } from '../types'
import { awardMockBadges, isNightHour } from './badges'

/** DEBUG-0091：Python 中位数 -- 偶数分支左右中位取错 */
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
        # 循环只跑一轮，但左中位取错了位置
    return (nums[lo] + nums[mid + 1]) / 2`,
  failing_output: `$ pytest test_median.py -v
test_median.py::test_odd            PASSED   [ 20%]
test_median.py::test_single         PASSED   [ 40%]
test_median.py::test_even           FAILED   assert 3.5 == 3.0  [ 60%]
test_median.py::test_even_negative  FAILED   assert -2.5 == -3.5  [ 80%]
test_median.py::test_even_unsorted  FAILED   assert 6.5 == 6.0  [100%]

=================== 2 passed, 3 failed in 0.05s ===================
median([4,1,2,5]) -> 3.5（期望 3.0）
偶数个时中间两个数取错了：右中位用了 nums[mid + 1]，应为 nums[mid]。`,
  time_limit_sec: 600,
  difficulty: 3,
  related_weakness: '边界条件处理',
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
test_bsearch.py::test_last_element  PASSED   [ 80%]
test_bsearch.py::test_empty         IndexError: list index out of range  [100%]

=================== 3 passed, 2 failed in 0.09s ===================
right 初始化为 len(arr)，当 target 大于所有元素或数组为空时 mid 越界。`,
  time_limit_sec: 600,
  difficulty: 1,
  related_weakness: '边界条件处理',
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
test_str_reverse("hello")    -> 运行错误（free(): invalid pointer）    FAIL
test_str_reverse("a")        -> 运行错误（free(): invalid pointer）    FAIL
test_str_reverse("")         -> "" (expected "")                        OK
test_str_reverse("abcdef")   -> 运行错误（free(): invalid pointer）    FAIL
test_str_reverse("12345")    -> 运行错误（free(): invalid pointer）    FAIL

======================== 1/5 tests passed ========================
返回的是 dest（已移到字符串末尾），不是 result；测试程序 free 这个偏移指针直接崩溃。`,
  time_limit_sec: 600,
  difficulty: 3,
  related_weakness: '指针的内存布局',
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
test_unique.py::test_mixed          FAILED   assert 5 == 3  [ 80%]
test_unique.py::test_with_numbers   FAILED   assert 3 == 2  [100%]

=================== 2 passed, 3 failed in 0.05s ===================
count 对每个 word 都 +1，没有跳过已见元素。需要加 if w not in seen 判断。`,
  time_limit_sec: 600,
  difficulty: 2,
  related_weakness: '边界条件处理',
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
  related_weakness: '递归出口设计',
}

/** DEBUG-0096：Python 数组右旋 -- 切片方向反了 */
export const CHALLENGE_0096: ArenaChallenge = {
  id: 'DEBUG-0096',
  title: '数组右旋 · 方向反了',
  language: 'python',
  code: `def rotate(nums, k):
    """数组右旋 -- AI 生成，测试全挂，待修复"""
    n = len(nums)
    k = k % n
    return nums[k:] + nums[:k]`,
  failing_output: `$ pytest test_rotate.py -v
test_rotate.py::test_basic       FAILED   [ 20%]
test_rotate.py::test_zero        PASSED   [ 40%]
test_rotate.py::test_wrap        FAILED   [ 60%]
test_rotate.py::test_single      PASSED   [ 80%]
test_rotate.py::test_big_k       FAILED   [100%]

=================== 2 passed, 3 failed in 0.06s ===================
rotate([1,2,3,4,5], 2) -> [3,4,5,1,2]（期望 [4,5,1,2,3]）
方向反了：切片拼的是向左旋，向右旋应取 nums[-k:] + nums[:-k]。`,
  time_limit_sec: 600,
  difficulty: 2,
  related_weakness: '边界条件处理',
}

/** DEBUG-0097：Python 字符频次 -- 命中已见字符时计数被重置为 1 */
export const CHALLENGE_0097: ArenaChallenge = {
  id: 'DEBUG-0097',
  title: '字符频次 · 计数不累加',
  language: 'python',
  code: `def most_frequent(s):
    """出现次数最多的字符 -- AI 生成，测试全挂，待修复"""
    counts = {}
    for ch in s:
        if ch in counts:
            counts[ch] = 1
        else:
            counts[ch] = 1
    return max(counts, key=counts.get)`,
  failing_output: `$ pytest test_freq.py -v
test_freq.py::test_hello       FAILED   [ 20%]
test_freq.py::test_aaabbc      PASSED   [ 40%]
test_freq.py::test_xyz         PASSED   [ 60%]
test_freq.py::test_mississippi FAILED   [ 80%]
test_freq.py::test_abracadabra PASSED   [100%]

=================== 3 passed, 2 failed in 0.05s ===================
most_frequent("hello") -> 'h'（期望 'l'）
命中已存在的字符时把计数重置为 1，所有字符计数恒为 1，max 只能返回最先插入的字符。`,
  time_limit_sec: 600,
  difficulty: 2,
  related_weakness: '字符串处理',
}

/** DEBUG-0098：Python 括号匹配 -- 空栈直接 pop 崩溃 */
export const CHALLENGE_0098: ArenaChallenge = {
  id: 'DEBUG-0098',
  title: '括号匹配 · 空栈出栈',
  language: 'python',
  code: `def is_balanced(s):
    """括号匹配 -- AI 生成，测试全挂，待修复"""
    stack = []
    pairs = {")": "(", "]": "[", "}": "{"}
    for ch in s:
        if ch in "([{":
            stack.append(ch)
        elif ch in ")]}":
            if stack.pop() == pairs[ch]:
                continue
            return False
    return len(stack) == 0`,
  failing_output: `$ pytest test_balanced.py -v
test_balanced.py::test_ok         PASSED   [ 17%]
test_balanced.py::test_mixed      PASSED   [ 33%]
test_balanced.py::test_mismatch   PASSED   [ 50%]
test_balanced.py::test_interleave PASSED   [ 67%]
test_balanced.py::test_extra_open PASSED   [ 83%]
test_balanced.py::test_stray      IndexError: pop from empty list  [100%]

=================== 5 passed, 1 failed in 0.07s ===================
is_balanced(")") -> IndexError: pop from empty list
出栈前没有判空：出现右括号而栈为空时直接崩溃，应返回 False。`,
  time_limit_sec: 600,
  difficulty: 2,
  related_weakness: '边界条件处理',
}

/** DEBUG-0099：Python 最大子数组和 -- Kadane 缺少回退 */
export const CHALLENGE_0099: ArenaChallenge = {
  id: 'DEBUG-0099',
  title: '最大子数组和 · 不回退',
  language: 'python',
  code: `def max_subarray(nums):
    """最大子数组和 -- AI 生成，测试全挂，待修复"""
    cur = nums[0]
    best = nums[0]
    for x in nums[1:]:
        cur = cur + x
        if cur > best:
            best = cur
    return best`,
  failing_output: `$ pytest test_maxsub.py -v
test_maxsub.py::test_example     FAILED   [ 20%]
test_maxsub.py::test_single      PASSED   [ 40%]
test_maxsub.py::test_all_neg     PASSED   [ 60%]
test_maxsub.py::test_neg_then_pos PASSED  [ 80%]
test_maxsub.py::test_two_neg     FAILED   [100%]

=================== 3 passed, 2 failed in 0.06s ===================
max_subarray([-2,1,-3,4,-1,2,1,-5,4]) -> 2（期望 6）
max_subarray([-2,-1]) -> -2（期望 -1）
Kadane 漏了回退：cur 累计后从不与 x 取 max，负数把整段和一直拖到为负。`,
  time_limit_sec: 600,
  difficulty: 4,
  related_weakness: '动态规划状态设计',
}

/** DEBUG-0100：Python 字符串压缩 -- 一段结束时 count 重置为 0 */
export const CHALLENGE_0100: ArenaChallenge = {
  id: 'DEBUG-0100',
  title: '字符串压缩 · 计数归零',
  language: 'python',
  code: `def compress(s):
    """字符串压缩 -- AI 生成，测试全挂，待修复"""
    if not s:
        return ""
    result = []
    count = 1
    for i in range(1, len(s)):
        if s[i] == s[i - 1]:
            count += 1
        else:
            result.append(s[i - 1] + str(count))
            count = 0
    result.append(s[len(s) - 1] + str(count))
    return "".join(result)`,
  failing_output: `$ pytest test_compress.py -v
test_compress.py::test_aabbb     FAILED   [ 20%]
test_compress.py::test_single    PASSED   [ 40%]
test_compress.py::test_aa        PASSED   [ 60%]
test_compress.py::test_ab        FAILED   [ 80%]
test_compress.py::test_aab       FAILED   [100%]

=================== 2 passed, 3 failed in 0.05s ===================
compress("aabbb") -> 'a2b2'（期望 'a2b3'）
compress("ab") -> 'a1b0'（期望 'a1b1'）
一组字符结束时把 count 重置为 0，下一段从 0 开始计导致少 1；应重置为 1。`,
  time_limit_sec: 600,
  difficulty: 2,
  related_weakness: '字符串处理',
}

/** DEBUG-0101：Python 回文判断 -- 比较相邻字符而非首尾对称 */
export const CHALLENGE_0101: ArenaChallenge = {
  id: 'DEBUG-0101',
  title: '回文判断 · 比错了对象',
  language: 'python',
  code: `def is_palindrome(s):
    """回文判断 -- AI 生成，测试全挂，待修复"""
    cleaned = "".join(ch.lower() for ch in s if ch.isalnum())
    for i in range(len(cleaned) // 2):
        if cleaned[i] != cleaned[i + 1]:
            return False
    return True`,
  failing_output: `$ pytest test_pal.py -v
test_pal.py::test_phrase      FAILED   [ 20%]
test_pal.py::test_not_pal     PASSED   [ 40%]
test_pal.py::test_blank       PASSED   [ 60%]
test_pal.py::test_abba        FAILED   [ 80%]
test_pal.py::test_abcba       FAILED   [100%]

=================== 2 passed, 3 failed in 0.05s ===================
is_palindrome("abba") -> False（期望 True）
比较的是相邻字符而不是首尾对称字符：cleaned[i] != cleaned[i+1] 只在相邻相同时才通过。`,
  time_limit_sec: 600,
  difficulty: 2,
  related_weakness: '字符串处理',
}

/** DEBUG-0102：C 链表反转 -- 返回了循环结束后的 cur（NULL） */
export const CHALLENGE_0102: ArenaChallenge = {
  id: 'DEBUG-0102',
  title: '链表反转 · 返回了空指针',
  language: 'c',
  code: `#include <stdio.h>
#include <stdlib.h>

typedef struct Node {
    int val;
    struct Node *next;
} Node;

Node* reverse(Node *head) {
    Node *prev = NULL;
    Node *cur = head;
    while (cur) {
        Node *next = cur->next;
        cur->next = prev;
        prev = cur;
        cur = next;
    }
    return cur;
}`,
  failing_output: `$ gcc -o test test.c && ./test
test_reverse("1 2 3")      -> (空)       期望 "3 2 1"    FAIL
test_reverse("42")         -> (空)       期望 "42"        FAIL
test_reverse("4 3 2 1")    -> (空)       期望 "1 2 3 4"   FAIL
test_reverse("-1 -2")      -> (空)       期望 "-2 -1"     FAIL
test_reverse("5 4 3 2 1")  -> (空)       期望 "1 2 3 4 5" FAIL

======================== 0/5 tests passed ========================
返回的是 cur（循环结束后已是 NULL），应返回翻转后的新头 prev。`,
  time_limit_sec: 600,
  difficulty: 3,
  related_weakness: '链表操作',
}

/** DEBUG-0103：Python 移动零 -- 非零前移后末尾没补 0 */
export const CHALLENGE_0103: ArenaChallenge = {
  id: 'DEBUG-0103',
  title: '移动零 · 末尾没补零',
  language: 'python',
  code: `def move_zeros(nums):
    """把 0 移到末尾 -- AI 生成，测试全挂，待修复"""
    n = len(nums)
    idx = 0
    for i in range(n):
        if nums[i] != 0:
            nums[idx] = nums[i]
            idx += 1
    return nums`,
  failing_output: `$ pytest test_zeros.py -v
test_zeros.py::test_mixed      FAILED   [ 20%]
test_zeros.py::test_zero_only  PASSED   [ 40%]
test_zeros.py::test_no_zero    PASSED   [ 60%]
test_zeros.py::test_two_zeros  FAILED   [ 80%]
test_zeros.py::test_one_zero   PASSED   [100%]

=================== 3 passed, 2 failed in 0.05s ===================
move_zeros([0,1,0,3,12]) -> [1,3,12,3,12]（期望 [1,3,12,0,0]）
只把非零元素搬到前面，末尾没补 0，原尾元素残留在后面。`,
  time_limit_sec: 600,
  difficulty: 2,
  related_weakness: '边界条件处理',
}

/** DEBUG-0104：Python 字符串转整数 -- strip 后直接读 s[0]，空串崩溃 */
export const CHALLENGE_0104: ArenaChallenge = {
  id: 'DEBUG-0104',
  title: '字符串转整数 · 空串崩溃',
  language: 'python',
  code: `def str_to_int(s):
    """字符串转整数 -- AI 生成，测试全挂，待修复"""
    s = s.strip()
    sign = 1
    if s[0] == "-":
        sign = -1
        s = s[1:]
    elif s[0] == "+":
        s = s[1:]
    num = 0
    for ch in s:
        if ch.isdigit():
            num = num * 10 + int(ch)
        else:
            break
    return sign * num`,
  failing_output: `$ pytest test_atoi.py -v
test_atoi.py::test_positive    PASSED   [ 20%]
test_atoi.py::test_negative    PASSED   [ 40%]
test_atoi.py::test_words_tail  PASSED   [ 60%]
test_atoi.py::test_words_head  PASSED   [ 80%]
test_atoi.py::test_empty       IndexError: string index out of range  [100%]

=================== 4 passed, 1 failed in 0.05s ===================
str_to_int("") -> IndexError: string index out of range
strip 之后直接读 s[0]，没先判空；空字符串应返回 0。`,
  time_limit_sec: 600,
  difficulty: 3,
  related_weakness: '字符串处理',
}

/** DEBUG-0105：Python 矩阵转置 -- 赋值下标写反，非方阵越界 */
export const CHALLENGE_0105: ArenaChallenge = {
  id: 'DEBUG-0105',
  title: '矩阵转置 · 下标写反',
  language: 'python',
  code: `def transpose(matrix):
    """矩阵转置 -- AI 生成，测试全挂，待修复"""
    rows = len(matrix)
    cols = len(matrix[0])
    result = [[0] * rows for _ in range(cols)]
    for i in range(rows):
        for j in range(cols):
            result[i][j] = matrix[j][i]
    return result`,
  failing_output: `$ pytest test_transpose.py -v
test_transpose.py::test_1x1     PASSED   [ 20%]
test_transpose.py::test_2x2     PASSED   [ 40%]
test_transpose.py::test_2x3     IndexError: list index out of range  [ 60%]
test_transpose.py::test_3x2     IndexError: list index out of range  [ 80%]
test_transpose.py::test_3x3     PASSED   [100%]

=================== 3 passed, 2 failed in 0.06s ===================
transpose([[1,2,3],[4,5,6]]) -> IndexError: list index out of range
赋值写反了：result[i][j] = matrix[j][i]，非方阵时 j 越界；应改为 result[j][i] = matrix[i][j]。`,
  time_limit_sec: 600,
  difficulty: 3,
  related_weakness: '边界条件处理',
}

/** DEBUG-0106：Python 约瑟夫环 -- 出列下标多算 1 */
export const CHALLENGE_0106: ArenaChallenge = {
  id: 'DEBUG-0106',
  title: '约瑟夫环 · 下标多算一',
  language: 'python',
  code: `def josephus(n, k):
    """约瑟夫环最后幸存者 -- AI 生成，测试全挂，待修复"""
    people = list(range(1, n + 1))
    idx = 0
    while len(people) > 1:
        idx = (idx + k) % len(people)
        people.pop(idx)
    return people[0]`,
  failing_output: `$ pytest test_josephus.py -v
test_josephus.py::test_5_3      FAILED   [ 20%]
test_josephus.py::test_1_1      PASSED   [ 40%]
test_josephus.py::test_7_3      FAILED   [ 60%]
test_josephus.py::test_3_2      FAILED   [ 80%]
test_josephus.py::test_10_4     FAILED   [100%]

=================== 1 passed, 4 failed in 0.06s ===================
josephus(5,3) -> 1（期望 4）
出列下标多算了 1：idx = (idx + k) % n 把当前人也数了一次，应改为 (idx + k - 1) % n。`,
  time_limit_sec: 600,
  difficulty: 3,
  related_weakness: '边界条件处理',
}

/** DEBUG-0107：Python 缺失最小正数 -- 1..n 全出现时误返回 n */
export const CHALLENGE_0107: ArenaChallenge = {
  id: 'DEBUG-0107',
  title: '缺失最小正数 · 边界值',
  language: 'python',
  code: `def first_missing_positive(nums):
    """第一个缺失的正整数 -- AI 生成，测试全挂，待修复"""
    n = len(nums)
    present = [False] * (n + 1)
    for x in nums:
        if 1 <= x <= n:
            present[x] = True
    for i in range(1, n + 1):
        if not present[i]:
            return i
    return n`,
  failing_output: `$ pytest test_fmp.py -v
test_fmp.py::test_1_2_0        PASSED   [ 20%]
test_fmp.py::test_3_4_neg_1_1  PASSED   [ 40%]
test_fmp.py::test_big          PASSED   [ 60%]
test_fmp.py::test_1_2_3        FAILED   [ 80%]
test_fmp.py::test_single       FAILED   [100%]

=================== 3 passed, 2 failed in 0.05s ===================
first_missing_positive([1,2,3]) -> 3（期望 4）
1..n 全部出现时返回 n，但缺失的最小正整数是 n+1；应在循环后返回 n + 1。`,
  time_limit_sec: 600,
  difficulty: 5,
  related_weakness: '边界条件处理',
}

/** DEBUG-0108：Python 快乐数 -- 非快乐数进入循环死转 */
export const CHALLENGE_0108: ArenaChallenge = {
  id: 'DEBUG-0108',
  title: '快乐数 · 死循环',
  language: 'python',
  code: `def is_happy(n):
    """快乐数 -- AI 生成，测试全挂，待修复"""
    while n != 1:
        n = sum(int(d) ** 2 for d in str(n))
    return True`,
  failing_output: `$ pytest test_happy.py -v
test_happy.py::test_19          PASSED   [ 20%]
test_happy.py::test_1           PASSED   [ 40%]
test_happy.py::test_2           TIMEOUT  [ 60%] 执行超过 5s（疑似死循环）
test_happy.py::test_7           PASSED   [ 80%]
test_happy.py::test_4           TIMEOUT  [100%] 执行超过 5s（疑似死循环）

=================== 3 passed, 2 timeout in 15.40s ==================
is_happy(2) 卡死：没有记录已访问过的数字，非快乐数在 4-16-37-... 循环里永远出不来。需要加 seen 集合判重。`,
  time_limit_sec: 600,
  difficulty: 3,
  related_weakness: '递归出口设计',
}

/** DEBUG-0109：C 链表中间节点 -- fast 每次只走一步，快慢同速 */
export const CHALLENGE_0109: ArenaChallenge = {
  id: 'DEBUG-0109',
  title: '链表中间节点 · 快慢同速',
  language: 'c',
  code: `#include <stdio.h>
#include <stdlib.h>

typedef struct Node {
    int val;
    struct Node *next;
} Node;

Node* middle_node(Node *head) {
    Node *slow = head;
    Node *fast = head;
    while (fast && fast->next) {
        slow = slow->next;
        fast = fast->next;
    }
    return slow;
}`,
  failing_output: `$ gcc -o test test.c && ./test
test_middle("1 2 3")    -> 3       期望 2      FAIL
test_middle("42")       -> 42      期望 42     PASS
test_middle("1 2 3 4")  -> 4       期望 3      FAIL
test_middle("7 8")      -> 8       期望 8      PASS
test_middle("5 4 3 2 1")-> 1       期望 3      FAIL

======================== 2/5 tests passed ========================
fast 每次只走一步，slow 也跟着一直走到尾；fast 应每次跳两步，slow 才能停在中间。`,
  time_limit_sec: 600,
  difficulty: 3,
  related_weakness: '链表操作',
}

/** DEBUG-0110：Python 反转单词顺序 -- 对每个单词做了字符反转 */
export const CHALLENGE_0110: ArenaChallenge = {
  id: 'DEBUG-0110',
  title: '反转单词顺序 · 反转错了对象',
  language: 'python',
  code: `def reverse_words(s):
    """反转单词顺序 -- AI 生成，测试全挂，待修复"""
    words = s.split()
    return " ".join(word[::-1] for word in words)`,
  failing_output: `$ pytest test_rwords.py -v
test_rwords.py::test_sentence   FAILED   [ 20%]
test_rwords.py::test_spaces     FAILED   [ 40%]
test_rwords.py::test_single     PASSED   [ 60%]
test_rwords.py::test_hello      FAILED   [ 80%]
test_rwords.py::test_multi_sp   FAILED   [100%]

=================== 1 passed, 4 failed in 0.05s ===================
reverse_words("the sky is blue") -> 'eht yks si eulb'（期望 'blue is sky the'）
对每个单词做了字符反转，而没有反转单词顺序；应 reversed(words) 而不是 word[::-1]。`,
  time_limit_sec: 600,
  difficulty: 2,
  related_weakness: '字符串处理',
}

/** 所有挑战的映射 */
const CHALLENGES: Record<string, ArenaChallenge> = {
  'DEBUG-0091': CHALLENGE_0091,
  'DEBUG-0092': CHALLENGE_0092,
  'DEBUG-0093': CHALLENGE_0093,
  'DEBUG-0094': CHALLENGE_0094,
  'DEBUG-0095': CHALLENGE_0095,
  'DEBUG-0096': CHALLENGE_0096,
  'DEBUG-0097': CHALLENGE_0097,
  'DEBUG-0098': CHALLENGE_0098,
  'DEBUG-0099': CHALLENGE_0099,
  'DEBUG-0100': CHALLENGE_0100,
  'DEBUG-0101': CHALLENGE_0101,
  'DEBUG-0102': CHALLENGE_0102,
  'DEBUG-0103': CHALLENGE_0103,
  'DEBUG-0104': CHALLENGE_0104,
  'DEBUG-0105': CHALLENGE_0105,
  'DEBUG-0106': CHALLENGE_0106,
  'DEBUG-0107': CHALLENGE_0107,
  'DEBUG-0108': CHALLENGE_0108,
  'DEBUG-0109': CHALLENGE_0109,
  'DEBUG-0110': CHALLENGE_0110,
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
  'DEBUG-0096': `$ pytest test_rotate.py -v
test_rotate.py::test_basic       PASSED   [ 20%]
test_rotate.py::test_zero        PASSED   [ 40%]
test_rotate.py::test_wrap        PASSED   [ 60%]
test_rotate.py::test_single      PASSED   [ 80%]
test_rotate.py::test_big_k       PASSED   [100%]

======================== 5 passed in 0.04s ========================`,
  'DEBUG-0097': `$ pytest test_freq.py -v
test_freq.py::test_hello       PASSED   [ 20%]
test_freq.py::test_aaabbc      PASSED   [ 40%]
test_freq.py::test_xyz         PASSED   [ 60%]
test_freq.py::test_mississippi PASSED   [ 80%]
test_freq.py::test_abracadabra PASSED   [100%]

======================== 5 passed in 0.04s ========================`,
  'DEBUG-0098': `$ pytest test_balanced.py -v
test_balanced.py::test_ok         PASSED   [ 17%]
test_balanced.py::test_mixed      PASSED   [ 33%]
test_balanced.py::test_mismatch   PASSED   [ 50%]
test_balanced.py::test_interleave PASSED   [ 67%]
test_balanced.py::test_extra_open PASSED   [ 83%]
test_balanced.py::test_stray      PASSED   [100%]

======================== 6 passed in 0.05s ========================`,
  'DEBUG-0099': `$ pytest test_maxsub.py -v
test_maxsub.py::test_example     PASSED   [ 20%]
test_maxsub.py::test_single      PASSED   [ 40%]
test_maxsub.py::test_all_neg     PASSED   [ 60%]
test_maxsub.py::test_neg_then_pos PASSED  [ 80%]
test_maxsub.py::test_two_neg     PASSED   [100%]

======================== 5 passed in 0.04s ========================`,
  'DEBUG-0100': `$ pytest test_compress.py -v
test_compress.py::test_aabbb     PASSED   [ 20%]
test_compress.py::test_single    PASSED   [ 40%]
test_compress.py::test_aa        PASSED   [ 60%]
test_compress.py::test_ab        PASSED   [ 80%]
test_compress.py::test_aab       PASSED   [100%]

======================== 5 passed in 0.04s ========================`,
  'DEBUG-0101': `$ pytest test_pal.py -v
test_pal.py::test_phrase      PASSED   [ 20%]
test_pal.py::test_not_pal     PASSED   [ 40%]
test_pal.py::test_blank       PASSED   [ 60%]
test_pal.py::test_abba        PASSED   [ 80%]
test_pal.py::test_abcba       PASSED   [100%]

======================== 5 passed in 0.04s ========================`,
  'DEBUG-0102': `$ gcc -o test test.c && ./test
test_reverse("1 2 3")      -> "3 2 1"     OK
test_reverse("42")         -> "42"        OK
test_reverse("4 3 2 1")    -> "1 2 3 4"   OK
test_reverse("-1 -2")      -> "-2 -1"     OK
test_reverse("5 4 3 2 1")  -> "1 2 3 4 5" OK

======================== 5/5 tests passed ========================`,
  'DEBUG-0103': `$ pytest test_zeros.py -v
test_zeros.py::test_mixed      PASSED   [ 20%]
test_zeros.py::test_zero_only  PASSED   [ 40%]
test_zeros.py::test_no_zero    PASSED   [ 60%]
test_zeros.py::test_two_zeros  PASSED   [ 80%]
test_zeros.py::test_one_zero   PASSED   [100%]

======================== 5 passed in 0.04s ========================`,
  'DEBUG-0104': `$ pytest test_atoi.py -v
test_atoi.py::test_positive    PASSED   [ 20%]
test_atoi.py::test_negative    PASSED   [ 40%]
test_atoi.py::test_words_tail  PASSED   [ 60%]
test_atoi.py::test_words_head  PASSED   [ 80%]
test_atoi.py::test_empty       PASSED   [100%]

======================== 5 passed in 0.04s ========================`,
  'DEBUG-0105': `$ pytest test_transpose.py -v
test_transpose.py::test_1x1     PASSED   [ 20%]
test_transpose.py::test_2x2     PASSED   [ 40%]
test_transpose.py::test_2x3     PASSED   [ 60%]
test_transpose.py::test_3x2     PASSED   [ 80%]
test_transpose.py::test_3x3     PASSED   [100%]

======================== 5 passed in 0.05s ========================`,
  'DEBUG-0106': `$ pytest test_josephus.py -v
test_josephus.py::test_5_3      PASSED   [ 20%]
test_josephus.py::test_1_1      PASSED   [ 40%]
test_josephus.py::test_7_3      PASSED   [ 60%]
test_josephus.py::test_3_2      PASSED   [ 80%]
test_josephus.py::test_10_4     PASSED   [100%]

======================== 5 passed in 0.05s ========================`,
  'DEBUG-0107': `$ pytest test_fmp.py -v
test_fmp.py::test_1_2_0        PASSED   [ 20%]
test_fmp.py::test_3_4_neg_1_1  PASSED   [ 40%]
test_fmp.py::test_big          PASSED   [ 60%]
test_fmp.py::test_1_2_3        PASSED   [ 80%]
test_fmp.py::test_single       PASSED   [100%]

======================== 5 passed in 0.04s ========================`,
  'DEBUG-0108': `$ pytest test_happy.py -v
test_happy.py::test_19          PASSED   [ 20%]
test_happy.py::test_1           PASSED   [ 40%]
test_happy.py::test_2           PASSED   [ 60%]
test_happy.py::test_7           PASSED   [ 80%]
test_happy.py::test_4           PASSED   [100%]

======================== 5 passed in 0.09s ========================`,
  'DEBUG-0109': `$ gcc -o test test.c && ./test
test_middle("1 2 3")    -> 2    OK
test_middle("42")       -> 42   OK
test_middle("1 2 3 4")  -> 3    OK
test_middle("7 8")      -> 8    OK
test_middle("5 4 3 2 1")-> 3    OK

======================== 5/5 tests passed ========================`,
  'DEBUG-0110': `$ pytest test_rwords.py -v
test_rwords.py::test_sentence   PASSED   [ 20%]
test_rwords.py::test_spaces     PASSED   [ 40%]
test_rwords.py::test_single     PASSED   [ 60%]
test_rwords.py::test_hello      PASSED   [ 80%]
test_rwords.py::test_multi_sp   PASSED   [100%]

======================== 5 passed in 0.04s ========================`,
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

  const solved = (total: number) =>
    ({ passed: total, total, output: solvedOutput, solved: true, score_delta: 23 })
  const failed = (passed: number, total: number) =>
    ({ passed, total, output: failingOutput, solved: false, score_delta: 0 })

  switch (challengeId) {
    case 'DEBUG-0091': {
      const ruleLoop = normalized.includes('lo=mid-1')
      const ruleIndex = normalized.includes('nums[lo]+nums[mid])')
      if (ruleLoop && ruleIndex) return solved(5)
      if (ruleLoop) {
        return { passed: 3, total: 5, output: PARTIAL_0091, solved: false, score_delta: 0 }
      }
      return failed(2, 5)
    }
    case 'DEBUG-0092': {
      return normalized.includes('len(arr)-1') ? solved(5) : failed(2, 5)
    }
    case 'DEBUG-0093': {
      return normalized.includes('returnresult') ? solved(5) : failed(1, 5)
    }
    case 'DEBUG-0094': {
      return normalized.includes('notinseen') ? solved(5) : failed(2, 5)
    }
    case 'DEBUG-0095': {
      return normalized.includes('return1') ? solved(5) : failed(0, 5)
    }
    case 'DEBUG-0096': {
      const fixed =
        normalized.includes('nums[-k:]+nums[:-k]') ||
        normalized.includes('nums[n-k:]+nums[:n-k]')
      return fixed ? solved(5) : failed(2, 5)
    }
    case 'DEBUG-0097': {
      const fixed =
        normalized.includes('counts[ch]+=1') || normalized.includes('counts[ch]=counts[ch]+1')
      return fixed ? solved(5) : failed(3, 5)
    }
    case 'DEBUG-0098': {
      const fixed =
        normalized.includes('notstack:returnFalse') ||
        normalized.includes('iflen(stack)==0') ||
        normalized.includes('ifstackandstack.pop()')
      return fixed ? solved(6) : failed(5, 6)
    }
    case 'DEBUG-0099': {
      const fixed =
        normalized.includes('max(cur+x,x)') ||
        normalized.includes('max(x,cur+x)') ||
        normalized.includes('ifcur<0:cur=0')
      return fixed ? solved(5) : failed(3, 5)
    }
    case 'DEBUG-0100': {
      const fixed = !normalized.includes('count=0') && normalized.includes('count=1')
      return fixed ? solved(5) : failed(2, 5)
    }
    case 'DEBUG-0101': {
      const fixed =
        normalized.includes('cleaned[-i-1]') ||
        normalized.includes('cleaned[-1-i]') ||
        normalized.includes('cleaned[len(cleaned)-1-i]') ||
        normalized.includes('cleaned[len(cleaned)-i-1]') ||
        normalized.includes('cleaned[::-1]')
      return fixed ? solved(5) : failed(2, 5)
    }
    case 'DEBUG-0102': {
      const fixed = normalized.includes('returnprev') || normalized.includes('return(prev')
      return fixed ? solved(5) : failed(0, 5)
    }
    case 'DEBUG-0103': {
      const fixed =
        normalized.includes('nums[idx]=0') ||
        normalized.includes('nums[i]=0') ||
        normalized.includes('[0]*(n-idx)')
      return fixed ? solved(5) : failed(3, 5)
    }
    case 'DEBUG-0104': {
      const fixed =
        normalized.includes('ifnots:return0') ||
        normalized.includes('len(s)==0') ||
        normalized.includes('s==""')
      return fixed ? solved(5) : failed(4, 5)
    }
    case 'DEBUG-0105': {
      return normalized.includes('result[j][i]=matrix[i][j]') ? solved(5) : failed(3, 5)
    }
    case 'DEBUG-0106': {
      return normalized.includes('idx+k-1') ? solved(5) : failed(1, 5)
    }
    case 'DEBUG-0107': {
      return normalized.includes('returnn+1') ? solved(5) : failed(3, 5)
    }
    case 'DEBUG-0108': {
      const fixed = normalized.includes('seen') && normalized.includes('returnFalse')
      return fixed ? solved(5) : failed(3, 5)
    }
    case 'DEBUG-0109': {
      return normalized.includes('fast=fast->next->next') ? solved(5) : failed(2, 5)
    }
    case 'DEBUG-0110': {
      const fixed =
        normalized.includes('reversed(words)') || normalized.includes('words[::-1]')
      return fixed ? solved(5) : failed(1, 5)
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
