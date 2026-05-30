import type { CodeEditorPanelRef } from '@/components/editor/CodeEditorPanel'
import type { RefObject } from 'react'

// Global registry so MorphPanel can access the active IDE's methods
let activeEditorRef: RefObject<CodeEditorPanelRef> | null = null

export function registerActiveEditor(ref: RefObject<CodeEditorPanelRef> | null) {
  activeEditorRef = ref
}

export function getActiveEditorRef(): RefObject<CodeEditorPanelRef> | null {
  return activeEditorRef
}
