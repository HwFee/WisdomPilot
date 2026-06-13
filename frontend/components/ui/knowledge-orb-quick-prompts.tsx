"use client"

import type { ContextMode } from "@/hooks/use-knowledge-orb-state"

interface KnowledgeOrbQuickPromptsProps {
  contextMode: ContextMode
  hasKnowledgePoint: boolean
  onPrompt: (prompt: string) => void
}

const QUESTION_PROMPTS = [
  { label: "解释题意", prompt: "请详细解释这道题的题意和要求" },
  { label: "提示思路", prompt: "这道题的解题思路是什么？" },
  { label: "类似题", prompt: "请给我一道类似的练习题" },
]

const KNOWLEDGE_PROMPTS = [
  { label: "详细解释", prompt: "请详细解释这个知识点的含义和应用场景" },
  { label: "示例讲解", prompt: "请结合示例代码详细讲解这个知识点的用法" },
  { label: "注意事项", prompt: "使用这个知识点有什么需要注意的地方？" },
  { label: "相关知识点", prompt: "有哪些相关的知识点需要一起学习？" },
]

const FREE_PROMPTS = [
  { label: "帮我解释", prompt: "请帮我解释这个概念" },
  { label: "举例说明", prompt: "请给我一个实际的应用例子" },
  { label: "常见问题", prompt: "这个知识点有哪些常见的问题？" },
]

export function KnowledgeOrbQuickPrompts({ contextMode, hasKnowledgePoint, onPrompt }: KnowledgeOrbQuickPromptsProps) {
  const prompts = contextMode === "question"
    ? QUESTION_PROMPTS
    : hasKnowledgePoint
      ? KNOWLEDGE_PROMPTS
      : FREE_PROMPTS

  return (
    <div className="flex flex-wrap gap-1.5 px-3 py-2.5 shrink-0">
      {prompts.map((qp) => (
        <button type="button"
          key={qp.label}
          onClick={() => onPrompt(qp.prompt)}
          className="px-2.5 py-1 rounded-full text-xs border border-border bg-secondary/50 text-foreground transition-colors hover:bg-muted"
        >
          {qp.label}
        </button>
      ))}
    </div>
  )
}
