/* 代码审查室 mock：内置两关，判定逻辑本地运行（真实后端就位后由服务端判定） */

import type { InjectedDefect, ReviewMark, ReviewSession, ReviewVerdict } from '../types'
import { awardMockBadges, isNightHour } from './badges'

interface MockSession extends ReviewSession {
  injected: InjectedDefect[]
}

/** 第 12 关：Python 快速排序，2 处注入缺陷（第 5 行是「疑似但正常」的陷阱行） */
const SESSION_0247: MockSession = {
  id: 'REVIEW-0247',
  title: '快速排序实现',
  language: 'python',
  code: `def quicksort(arr):
    """快速排序 —— AI 生成，待审查"""
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    rest = arr[:len(arr) // 2] + arr[len(arr) // 2:]
    left = [x for x in rest if x < pivot]
    right = [x for x in rest if x > pivot]
    return quicksort(left) + [pivot] + quicksort(right)`,
  defect_count: 2,
  difficulty: 3,
  eta_minutes: 8,
  related_weakness: '边界条件处理',
  injected: [
    {
      line: 6,
      type: 'boundary',
      explanation:
        '右半切片 arr[len(arr)//2:] 把 pivot 本体又算了进去——pivot 会在结果里出现两次。应为 arr[len(arr)//2 + 1:]。',
    },
    {
      line: 7,
      type: 'logic',
      explanation:
        'left/right 都用严格比较，与 pivot 相等的元素会被整体丢弃：quicksort([2,2,1]) 只剩 [1,2]。一侧应使用 <=。',
    },
  ],
}

/** 第 13 关：C 链表反转，3 处注入缺陷 */
const SESSION_0248: MockSession = {
  id: 'REVIEW-0248',
  title: '链表反转',
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
        cur = next->next;
    }
    return head;
}

void free_list(Node *head) {
    while (head) {
        Node *tmp = head;
        head = head->next;
    }
}`,
  defect_count: 3,
  difficulty: 4,
  eta_minutes: 12,
  related_weakness: '指针的内存布局',
  injected: [
    {
      line: 16,
      type: 'logic',
      explanation: 'cur = next->next 每轮跳过一个节点，链表一半节点丢失。应为 cur = next。',
    },
    {
      line: 18,
      type: 'logic',
      explanation: '返回的是旧头指针 head（反转后它是尾节点），新头应是 prev。',
    },
    {
      line: 22,
      type: 'performance',
      explanation: 'free_list 只移动指针从不 free(tmp)，每个节点都泄漏。',
    },
  ],
}

/** 第 3 关：Python 二分查找，2 处注入缺陷 */
const SESSION_0249: MockSession = {
  id: 'REVIEW-0249',
  title: '二分查找',
  language: 'python',
  code: `def binary_search(arr, target):
    """二分查找 -- AI 生成，待审查"""
    left, right = 0, len(arr)
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid
    return -1`,
  defect_count: 2,
  difficulty: 2,
  eta_minutes: 6,
  related_weakness: '边界条件处理',
  injected: [
    {
      line: 3,
      type: 'boundary',
      explanation:
        'right = len(arr) 越界：当 target 大于所有元素时，mid 会等于 len(arr)，arr[mid] 抛 IndexError。应为 len(arr) - 1。',
    },
    {
      line: 11,
      type: 'logic',
      explanation:
        'right = mid 会导致死循环：当 target < arr[mid] 时 right 不收缩到 mid-1，区间永远无法缩小到空。应为 right = mid - 1。',
    },
  ],
}

/** 第 4 关：Python 用户注册，安全漏洞 + 魔法数字 */
const SESSION_0250: MockSession = {
  id: 'REVIEW-0250',
  title: '用户注册函数',
  language: 'python',
  code: `def register(username, password, db):
    """用户注册 -- AI 生成，待审查"""
    if len(password) < 8:
        return False
    query = "INSERT INTO users (name, pwd) VALUES ('" + username + "', '" + password + "')"
    db.execute(query)
    if db.rowcount > 0:
        return True
    else:
        return False`,
  defect_count: 2,
  difficulty: 3,
  eta_minutes: 10,
  related_weakness: '安全漏洞模式',
  injected: [
    {
      line: 5,
      type: 'security',
      explanation:
        '字符串拼接 SQL 存在注入风险：用户名输入 \' OR 1=1 -- 即可绕过注册。应使用参数化查询 db.execute("INSERT ... VALUES (?, ?)", username, password)。',
    },
    {
      line: 3,
      type: 'style',
      explanation:
        '魔法数字 8 直接硬编码，含义不明。应定义为命名常量 MIN_PASSWORD_LENGTH = 8。',
    },
  ],
}

/** 第 5 关：Python 日志分析器，重复代码 + 性能 */
const SESSION_0251: MockSession = {
  id: 'REVIEW-0251',
  title: '日志分析器',
  language: 'python',
  code: `def analyze_logs(logs):
    """日志分析器 -- AI 生成，待审查"""
    errors = []
    warnings = []
    info = []
    for line in logs:
        if "ERROR" in line:
            parts = line.split(" ")
            timestamp = parts[0]
            message = " ".join(parts[1:])
            errors.append({"time": timestamp, "msg": message})
        if "WARN" in line:
            parts = line.split(" ")
            timestamp = parts[0]
            message = " ".join(parts[1:])
            warnings.append({"time": timestamp, "msg": message})
        if "INFO" in line:
            parts = line.split(" ")
            timestamp = parts[0]
            message = " ".join(parts[1:])
            info.append({"time": timestamp, "msg": message})
    return errors, warnings, info`,
  defect_count: 3,
  difficulty: 3,
  eta_minutes: 10,
  related_weakness: '坏味道识别',
  injected: [
    {
      line: 7,
      type: 'style',
      explanation:
        '三个 if 分支重复了完全相同的解析逻辑（split + join + append），应抽取为 _parse_line(line) 公共函数。',
    },
    {
      line: 12,
      type: 'style',
      explanation:
        '三个独立 if 应改为 elif 链：已匹配 ERROR 的行无需再检查 WARN 和 INFO，当前每行都被检查三次。',
    },
    {
      line: 8,
      type: 'performance',
      explanation:
        'line.split(" ") 会分割整行产生多余字符串，应使用 line.split(" ", 1) 只分割一次。',
    },
  ],
}

/** 第 6 关：C 字符串拷贝，缓冲区溢出 + 空指针 */
const SESSION_0252: MockSession = {
  id: 'REVIEW-0252',
  title: '字符串拷贝',
  language: 'c',
  code: `#include <string.h>

char* copy_str(char *src, char *dst) {
    /* 字符串拷贝 -- AI 生成，待审查 */
    int i = 0;
    while (src[i] != '\\0') {
        dst[i] = src[i];
        i++;
    }
    dst[i] = '\\0';
    return dst;
}`,
  defect_count: 2,
  difficulty: 4,
  eta_minutes: 12,
  related_weakness: '安全漏洞模式',
  injected: [
    {
      line: 6,
      type: 'security',
      explanation:
        '循环没有检查 dst 缓冲区大小：当 src 比 dst 长时，dst[i] = src[i] 会越界写入，导致缓冲区溢出。应传入 dst 大小并做边界检查。',
    },
    {
      line: 3,
      type: 'boundary',
      explanation:
        '没有检查 src 或 dst 是否为 NULL，传入空指针会直接段错误。应在函数入口加 if (src == NULL || dst == NULL) return NULL。',
    },
  ],
}

/** 第 7 关：Python 缓存装饰器，竞态条件 + 性能 */
const SESSION_0253: MockSession = {
  id: 'REVIEW-0253',
  title: '缓存装饰器',
  language: 'python',
  code: `import time

def memoize(func):
    """缓存装饰器 -- AI 生成，待审查"""
    cache = {}
    def wrapper(*args, **kwargs):
        key = str(args) + str(kwargs)
        if key not in cache:
            cache[key] = func(*args, **kwargs)
        return cache[key]
    return wrapper`,
  defect_count: 2,
  difficulty: 4,
  eta_minutes: 12,
  related_weakness: '并发代码审阅',
  injected: [
    {
      line: 8,
      type: 'logic',
      explanation:
        '多线程下 check-then-set 存在竞态条件：两个线程同时通过 key not in cache 检查后都执行 func，缓存失效。应加 threading.Lock 保护。',
    },
    {
      line: 7,
      type: 'performance',
      explanation:
        'str(args) + str(kwargs) 每次调用都做字符串拼接，对于高频调用的热路径函数开销显著。应使用 args + tuple(sorted(kwargs.items())) 作为 key。',
    },
  ],
}

/** 第 8 关：Python 冒泡排序，糟糕命名 + 逻辑错误 */
const SESSION_0254: MockSession = {
  id: 'REVIEW-0254',
  title: '冒泡排序',
  language: 'python',
  code: `def b(a):
    """冒泡排序 -- AI 生成，待审查"""
    n = len(a)
    for i in range(n):
        for j in range(0, n - i - 1):
            if a[j] < a[j + 1]:
                t = a[j]
                a[j] = a[j + 1]
                a[j + 1] = t
    return a`,
  defect_count: 2,
  difficulty: 2,
  eta_minutes: 6,
  related_weakness: '坏味道识别',
  injected: [
    {
      line: 1,
      type: 'style',
      explanation:
        '函数名 b 和参数名 a 完全无法自解释，应改为 bubble_sort(arr)。命名是文档的一部分。',
    },
    {
      line: 6,
      type: 'logic',
      explanation:
        '比较方向错误：a[j] < a[j+1] 会把大元素冒泡到前面（降序），冒泡排序通常期望升序。应为 a[j] > a[j + 1]。',
    },
  ],
}

const SESSIONS: Record<string, MockSession> = {
  'REVIEW-0247': SESSION_0247,
  'REVIEW-0248': SESSION_0248,
  'REVIEW-0249': SESSION_0249,
  'REVIEW-0250': SESSION_0250,
  'REVIEW-0251': SESSION_0251,
  'REVIEW-0252': SESSION_0252,
  'REVIEW-0253': SESSION_0253,
  'REVIEW-0254': SESSION_0254,
}

export const NEXT_SESSION: Record<string, string> = {
  'REVIEW-0247': 'REVIEW-0248',
  'REVIEW-0248': 'REVIEW-0249',
  'REVIEW-0249': 'REVIEW-0250',
  'REVIEW-0250': 'REVIEW-0251',
  'REVIEW-0251': 'REVIEW-0252',
  'REVIEW-0252': 'REVIEW-0253',
  'REVIEW-0253': 'REVIEW-0254',
  'REVIEW-0254': 'REVIEW-0247',
}

export function getMockSession(id?: string): ReviewSession {
  const session = (id && SESSIONS[id]) || SESSION_0247
  const pub = { ...session } as Partial<MockSession>
  delete pub.injected
  return pub as ReviewSession
}

/**
 * 判定：标注行与注入缺陷行相差 ≤1 且类型一致 → 命中；
 * 无标注覆盖的注入缺陷 → 漏报；其余标注 → 误报。（不含徽章判定，保持纯函数）
 */
export function judgeMarks(
  defects: InjectedDefect[],
  marks: ReviewMark[]
): Omit<ReviewVerdict, 'new_badges'> {
  const hits: InjectedDefect[] = []
  const missed: InjectedDefect[] = []
  const falseAlarms: ReviewMark[] = []
  const usedMarks = new Set<number>()

  for (const defect of defects) {
    const hitIndex = marks.findIndex(
      (m, i) => !usedMarks.has(i) && Math.abs(m.line - defect.line) <= 1 && m.type === defect.type
    )
    if (hitIndex >= 0) {
      hits.push(defect)
      usedMarks.add(hitIndex)
    } else {
      missed.push(defect)
    }
  }
  marks.forEach((m, i) => {
    if (!usedMarks.has(i)) falseAlarms.push(m)
  })

  const precision = marks.length === 0 ? 1 : 1 - falseAlarms.length / marks.length
  const score = Math.round((hits.length / defects.length) * 70 + precision * 30)
  return {
    hits,
    missed,
    false_alarms: falseAlarms,
    score,
    accuracy: marks.length === 0 ? 0 : hits.length / marks.length,
  }
}

export function submitMockReview(id: string, marks: ReviewMark[]): ReviewVerdict {
  const session = SESSIONS[id] ?? SESSION_0247
  const verdict = judgeMarks(session.injected, marks)
  const new_badges = awardMockBadges({
    reviewSubmitted: true,
    reviewPerfect: verdict.missed.length === 0 && verdict.false_alarms.length === 0,
    isNight: isNightHour(),
  })
  return { ...verdict, new_badges }
}
