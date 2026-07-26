/* 代码审查室 mock：内置两关，判定逻辑本地运行（真实后端就位后由服务端判定） */

import type { InjectedDefect, ReviewMark, ReviewSession, ReviewVerdict } from '../types'

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

const SESSIONS: Record<string, MockSession> = {
  'REVIEW-0247': SESSION_0247,
  'REVIEW-0248': SESSION_0248,
}

export const NEXT_SESSION: Record<string, string> = {
  'REVIEW-0247': 'REVIEW-0248',
  'REVIEW-0248': 'REVIEW-0247',
}

export function getMockSession(id?: string): ReviewSession {
  const session = (id && SESSIONS[id]) || SESSION_0247
  const pub = { ...session } as Partial<MockSession>
  delete pub.injected
  return pub as ReviewSession
}

/**
 * 判定：标注行与注入缺陷行相差 ≤1 且类型一致 → 命中；
 * 无标注覆盖的注入缺陷 → 漏报；其余标注 → 误报。
 */
export function judgeMarks(defects: InjectedDefect[], marks: ReviewMark[]): ReviewVerdict {
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
  return judgeMarks(session.injected, marks)
}
