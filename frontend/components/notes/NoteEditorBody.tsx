'use client'

import { NoteEditorToolbar } from './NoteEditorToolbar'
import { NoteTagSelector } from './NoteTagSelector'
import { NoteTitleInput } from './NoteTitleInput'
import { MarkdownEditorPane } from './MarkdownEditorPane'
import { MarkdownPreviewPane } from './MarkdownPreviewPane'
import { NoteEditorFooter } from './NoteEditorFooter'
import type { NoteResponse, NoteTagResponse } from '@/types/api'

interface NoteEditorBodyProps {
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
  onCancel?: () => void
  variant: 'fullPage' | 'modal'
}

export function NoteEditorBody({
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
  onCancel,
  variant,
}: NoteEditorBodyProps) {
  return (
    <>
      <NoteEditorToolbar
        note={note}
        lang={lang}
        showTagSelector={showTagSelector}
        onToggleTagSelector={onToggleTagSelector}
        onClose={onCancel}
        variant={variant}
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
          variant={variant}
        />
      )}
      <NoteTitleInput title={title} lang={lang} onTitleChange={onTitleChange} variant={variant} />
      <div className="flex-1 flex min-h-0">
        <MarkdownEditorPane
          content={content}
          lang={lang}
          onContentChange={onContentChange}
          variant={variant}
        />
        <MarkdownPreviewPane content={content} lang={lang} variant={variant} />
      </div>
      <NoteEditorFooter
        isSaving={isSaving}
        content={content}
        lang={lang}
        onSave={onSave}
        onCancel={onCancel}
        variant={variant}
      />
    </>
  )
}