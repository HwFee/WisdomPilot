import type { KnowledgePointContext } from "@/contexts/AIContext"
import type { ContextMode } from "@/hooks/use-knowledge-orb-state"

export interface QuestionCtx {
  type: "choice" | "fill_blank"
  id: string
  question: string
  options?: string[]
  answerStatus?: "unanswered" | "correct" | "wrong"
}

export function parseKnowledgePoint(el: Element): KnowledgePointContext | null {
  const id = el.getAttribute("data-knowledge-point-id")
  const title = el.getAttribute("data-knowledge-point-title")
  const content = el.getAttribute("data-knowledge-point-content")
  const examplesStr = el.getAttribute("data-knowledge-point-examples")
  const difficulty = el.getAttribute("data-knowledge-point-difficulty")
  const index = el.getAttribute("data-knowledge-point-index")
  const adjacentStr = el.getAttribute("data-knowledge-point-adjacent")

  if (!id || !title || !content) return null

  let examples: string[] = []
  if (examplesStr) {
    try { examples = JSON.parse(examplesStr) } catch { examples = [] }
  }

  let adjacentPoints: Array<{ id: string; title: string }> = []
  if (adjacentStr) {
    try { adjacentPoints = JSON.parse(adjacentStr) } catch { adjacentPoints = [] }
  }

  return {
    id,
    title,
    content,
    examples,
    difficulty: difficulty ? parseInt(difficulty) || 1 : 1,
    index: index ? parseInt(index) || 0 : 0,
    adjacentPoints,
  }
}

export function parseQuestion(el: Element): QuestionCtx | null {
  const type = el.getAttribute("data-question-type")
  const id = el.getAttribute("data-question-id") || ""
  const question = el.getAttribute("data-question-text")
  if (!type || !question) return null

  const optionsStr = el.getAttribute("data-question-options")
  let options: string[] | undefined
  if (optionsStr) {
    try { options = JSON.parse(optionsStr) } catch { options = undefined }
  }
  const answerStatus = el.getAttribute("data-question-answer-status") as QuestionCtx["answerStatus"] | undefined
  return { type: type as "choice" | "fill_blank", id, question, options, answerStatus }
}

export function buildPrompt(
  kp: KnowledgePointContext,
  userMessage: string,
  mode: ContextMode
): string {
  if (mode === "question") {
    // Question mode: help with choice/fill_blank questions
    const optsStr = kp.examples && kp.examples.length > 0
      ? "\n选项：\n" + kp.examples.map((o, i) => `${String.fromCharCode(65 + i)}. ${o}`).join("\n")
      : ""
    return `你是学生的编程学习助手。当前题目：
${kp.title}${optsStr}

学生问题：${userMessage}
请根据以上题目信息，用中文给出有帮助的回答。`
  }

  // Knowledge mode
  const examplesStr = kp.examples && kp.examples.length > 0
    ? "\n示例代码：\n" + kp.examples.map((ex, i) => `\`\`\`\n${ex}\n\`\`\``).join("\n")
    : ""
  const adjacentStr = kp.adjacentPoints && kp.adjacentPoints.length > 0
    ? "\n相邻知识点：\n" + kp.adjacentPoints.map(p => `- ${p.title}`).join("\n")
    : ""

  return `你是学生的编程学习助手。当前正在学习知识点：
知识点 #${kp.index + 1}：${kp.title}
内容：${kp.content}${examplesStr}${adjacentStr}
学生问题：${userMessage}
请根据以上知识点内容，用中文给出有帮助的回答。`
}
