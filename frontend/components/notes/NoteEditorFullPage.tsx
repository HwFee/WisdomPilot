'use client'

import { Panel } from '@/components/layout'
import { NoteEditorBody } from './NoteEditorBody'
import type { NoteResponse, NoteTagResponse } from '@/types/api'

interface NoteEditorFullPageProps {
  note?: NoteResponse | null
  title: string
  content: string
  selectedTags: string[]
  selectedTagSet: Set<string>
  availableTags: NoteTagResponse[]
  newTagName: string
  showTagSelector: boolean
  isSaving: boolean
  lang: 'zh' | 'en'
  onTitleChange: (value: string) => void
  onContentChange: (value: string) => void
  onNewTagNameChange: (value: string) => void
  onCreateTag: () => void
  onToggleTag: (tagName: string) => void
  onToggleTagSelector: () => void
  onSave: () => void
  onClose?: () => void
}

export function NoteEditorFullPage({
  note,
  title,
  content,
  selectedTags,
  selectedTagSet,
  availableTags,
  newTagName,
  showTagSelector,
  isSaving,
  lang,
  onTitleChange,
  onContentChange,
  onNewTagNameChange,
  onCreateTag,
  onToggleTag,
  onToggleTagSelector,
  onSave,
  onClose,
}: NoteEditorFullPageProps) {
  return (
    <Panel className="h-full flex flex-col overflow-hidden">
      <NoteEditorBody
        note={note}
        title={title}
        content={content}
        selectedTags={selectedTags}
        selectedTagSet={selectedTagSet}
        availableTags={availableTags}
        newTagName={newTagName}
        showTagSelector={showTagSelector}
        isSaving={isSaving}
        lang={lang}
        onTitleChange={onTitleChange}
        onContentChange={onContentChange}
        onNewTagNameChange={onNewTagNameChange}
        onCreateTag={onCreateTag}
        onToggleTag={onToggleTag}
        onToggleTagSelector={onToggleTagSelector}
        onSave={onSave}
        onCancel={onClose}
        variant="fullPage"
      />
    </Panel>
  )
}
