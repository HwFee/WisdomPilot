"use client"

import { useCallback } from "react"
import type { ActiveKnowledgeQuestion } from "@/contexts/AIContext"
import { buildPrompt } from "@/lib/knowledge-orb"
import { getApiBaseUrl } from "@/lib/api-config"
import type { KnowledgeOrbState, KnowledgeOrbAction } from "./use-knowledge-orb-state"

interface UseKnowledgeOrbChatArgs {
  state: KnowledgeOrbState
  dispatch: React.Dispatch<KnowledgeOrbAction>
  activeKnowledgeQuestion: ActiveKnowledgeQuestion | null
  push: (href: string) => void
  closeKnowledgePanel: () => void
}

export function useKnowledgeOrbChat({
  state,
  dispatch,
  activeKnowledgeQuestion,
  push,
  closeKnowledgePanel,
}: UseKnowledgeOrbChatArgs) {
  const sendMessage = useCallback(async () => {
    const text = state.inputValue.trim()
    if (!text || state.isStreaming) return

    const userMessage = text
    dispatch({ type: "SET_INPUT_VALUE", payload: "" })
    dispatch({ type: "ADD_MESSAGE", payload: { role: "user", content: userMessage } })
    dispatch({ type: "START_STREAMING" })

    const kp = activeKnowledgeQuestion?.knowledgePoint
    const hasContext = kp && kp.id !== ""

    const prompt = hasContext
      ? buildPrompt(kp, userMessage, state.contextMode)
      : `你是一位耐心的编程老师。问题：\n\n${userMessage}\n\n请给出简洁、有帮助的回答。`

    try {
      const token = localStorage.getItem("token:v1")
      if (!token) return

      const apiUrl = getApiBaseUrl()
      const response = await fetch(
        `${apiUrl}/api/ai/chat/stream`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ message: prompt, context: null }),
        }
      )

      if (!response.ok) {
        if (response.status === 401) {
          localStorage.removeItem("token:v1")
          localStorage.removeItem("user:v1")
          push("/login")
          return
        }
        const errorText = await response.text()
        throw new Error(`请求失败: ${response.status} — ${errorText}`)
      }
      if (!response.body) throw new Error("无响应体")

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let fullText = ""

      while (true) {
        // react-doctor-disable-next-line async-await-in-loop, react-doctor/async-await-in-loop
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value, { stream: true })
        const lines = chunk.split("\n")

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6)
            if (data === "[DONE]") continue
            try {
              const parsed = JSON.parse(data)
              if (parsed.content) {
                fullText += parsed.content
                dispatch({ type: "SET_STREAMING_TEXT", payload: fullText })
              }
            } catch { /* skip malformed */ }
          }
        }
      }
      dispatch({ type: "ADD_MESSAGE", payload: { role: "ai", content: fullText } })
    } catch (err) {
      dispatch({ type: "ADD_MESSAGE", payload: { role: "ai", content: `抱歉，AI 服务暂时不可用: ${err instanceof Error ? err.message : String(err)}` } })
    } finally {
      dispatch({ type: "STOP_STREAMING" })
    }
  }, [state.inputValue, state.isStreaming, activeKnowledgeQuestion, state.contextMode, push, dispatch])

  const handleQuickPrompt = useCallback((prompt: string) => {
    dispatch({ type: "SET_INPUT_VALUE", payload: prompt })
  }, [dispatch])

  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      e.preventDefault()
      sendMessage()
    }
    if (e.key === "Escape") {
      closeKnowledgePanel()
    }
  }, [sendMessage, closeKnowledgePanel])

  const handleClose = useCallback(() => {
    closeKnowledgePanel()
    dispatch({ type: "CLEAR_MESSAGES" })
  }, [closeKnowledgePanel, dispatch])

  return {
    sendMessage,
    handleQuickPrompt,
    handleKeyDown,
    handleClose,
  }
}
