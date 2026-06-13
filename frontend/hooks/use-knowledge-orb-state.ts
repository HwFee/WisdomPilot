"use client"

import { useReducer } from "react"

export interface ChatMessage {
  role: "user" | "ai"
  content: string
}

export type ContextMode = "knowledge" | "question" | null

export interface KnowledgeOrbState {
  isHovered: boolean
  isDraggingOrb: boolean
  orbVisible: boolean
  showDisabledToast: boolean
  pos: { x: number; y: number }
  isDraggingPanel: boolean
  contextMode: ContextMode
  messages: ChatMessage[]
  inputValue: string
  isStreaming: boolean
  streamingText: string
}

const initialState: KnowledgeOrbState = {
  isHovered: false,
  isDraggingOrb: false,
  orbVisible: true,
  showDisabledToast: false,
  pos: { x: 100, y: 100 },
  isDraggingPanel: false,
  contextMode: null,
  messages: [],
  inputValue: "",
  isStreaming: false,
  streamingText: "",
}

export type KnowledgeOrbAction =
  | { type: "SET_HOVERED"; payload: boolean }
  | { type: "START_ORB_DRAG" }
  | { type: "STOP_ORB_DRAG" }
  | { type: "SHOW_ORB" }
  | { type: "HIDE_ORB" }
  | { type: "SHOW_DISABLED_TOAST" }
  | { type: "HIDE_DISABLED_TOAST" }
  | { type: "SET_PANEL_POS"; payload: { x: number; y: number } }
  | { type: "START_PANEL_DRAG" }
  | { type: "STOP_PANEL_DRAG" }
  | { type: "SET_CONTEXT_MODE"; payload: ContextMode }
  | { type: "SET_INPUT_VALUE"; payload: string }
  | { type: "START_STREAMING" }
  | { type: "SET_STREAMING_TEXT"; payload: string }
  | { type: "STOP_STREAMING" }
  | { type: "ADD_MESSAGE"; payload: ChatMessage }
  | { type: "CLEAR_MESSAGES" }

function knowledgeOrbReducer(state: KnowledgeOrbState, action: KnowledgeOrbAction): KnowledgeOrbState {
  switch (action.type) {
    case "SET_HOVERED":
      return { ...state, isHovered: action.payload }
    case "START_ORB_DRAG":
      return { ...state, isDraggingOrb: true }
    case "STOP_ORB_DRAG":
      return { ...state, isDraggingOrb: false }
    case "SHOW_ORB":
      return { ...state, orbVisible: true }
    case "HIDE_ORB":
      return { ...state, orbVisible: false }
    case "SHOW_DISABLED_TOAST":
      return { ...state, showDisabledToast: true }
    case "HIDE_DISABLED_TOAST":
      return { ...state, showDisabledToast: false }
    case "SET_PANEL_POS":
      return { ...state, pos: action.payload }
    case "START_PANEL_DRAG":
      return { ...state, isDraggingPanel: true }
    case "STOP_PANEL_DRAG":
      return { ...state, isDraggingPanel: false }
    case "SET_CONTEXT_MODE":
      return { ...state, contextMode: action.payload }
    case "SET_INPUT_VALUE":
      return { ...state, inputValue: action.payload }
    case "START_STREAMING":
      return { ...state, isStreaming: true, streamingText: "" }
    case "SET_STREAMING_TEXT":
      return { ...state, streamingText: action.payload }
    case "STOP_STREAMING":
      return { ...state, isStreaming: false, streamingText: "" }
    case "ADD_MESSAGE":
      return { ...state, messages: [...state.messages, action.payload] }
    case "CLEAR_MESSAGES":
      return { ...state, messages: [] }
    default:
      return state
  }
}

export function useKnowledgeOrbState() {
  return useReducer(knowledgeOrbReducer, initialState)
}
