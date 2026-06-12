'use client'

import { NoteEditorToolbar } from './NoteEditorToolbar'
import { NoteTagSelector } from './NoteTagSelector'
import { NoteTitleInput } from './NoteTitleInput'
import { MarkdownEditorPane } from './MarkdownEditorPane'
import { MarkdownPreviewPane } from './MarkdownPreviewPane'
import { NoteEditorFooter } from './NoteEditorFooter'
import type { NoteResponse, NoteTagResponse } from '@/types/api'

interface NoteEditorModalProps {
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

export function NoteEditorModal({
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
}: NoteEditorModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-card rounded-2xl shadow-2xl w-full max-w-4xl aspect-square max-h-[90vh] flex flex-col overflow-hidden">
        <NoteEditorToolbar
          note={note}
          lang={lang}
          showTagSelector={showTagSelector}
          onToggleTagSelector={onToggleTagSelector}
          onClose={onClose}
          variant="modal"
        />
        {showTagSelector && (
          <NoteTagSelector
            selectedTags={selectedTags}
            selectedTagSet={selectedTagSet}
            availableTags={availableTags}
            newTagName={newTagName}
            lang={lang}
            onNewTagNameChange={onNewTagNameChange}
            onCreateTag={onCreateTag}
            onToggleTag={onToggleTag}
            variant="modal"
          />
        )}
        <NoteTitleInput title={title} lang={lang} onTitleChange={onTitleChange} variant="modal" />
        <div className="flex-1 flex gap-4 p-5 overflow-hidden min-h-0">
          <MarkdownEditorPane
            content={content}
            lang={lang}
            onContentChange={onContentChange}
            variant="modal"
          />
          <MarkdownPreviewPane content={content} lang={lang} variant="modal" />
        </div>
        <NoteEditorFooter
          isSaving={isSaving}
          content={content}
          lang={lang}
          onSave={onSave}
          onCancel={onClose}
          variant="modal"
        />
      </div>
    </div>
  )
}
