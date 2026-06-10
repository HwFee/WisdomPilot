'use client'

import { Plus, Download } from 'lucide-react'
import { NoteEditor } from '@/components/notes/NoteEditor'
import { NoteCard } from '@/components/notes/NoteCard'
import { NoteSearch } from '@/components/notes/NoteSearch'
import { NoteTagFilter } from '@/components/notes/NoteTagFilter'
import { Button } from '@/components/ui/button'
import { useNotesData } from './hooks/use-notes-data'
import { useNoteEditor } from './hooks/use-note-editor'
import { exportAllNotes } from './lib/notes-export'

export default function NotesPage() {
  const {
    notes,
    filteredNotes,
    isLoading,
    selectedTags,
    setSelectedTags,
    searchQuery,
    handleDelete,
    handleSave,
    handleSearchResults,
    back,
  } = useNotesData()

  const {
    showEditor,
    editingNote,
    isFullPageEditor,
    openEditor,
    closeEditor,
  } = useNoteEditor()

  const handleExportAll = () => exportAllNotes(notes)

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-muted-foreground">加载中...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-40 glass border-b border-border/50">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center gap-4">
          <button type="button"
            onClick={() => back()}
            className="p-2.5 hover:bg-muted rounded-lg transition-colors"
          >
            ←
          </button>
          <h1 className="text-xl font-semibold">我的笔记</h1>
          <span className="ml-auto text-base text-muted-foreground">{notes.length} 条</span>
          <button type="button"
            onClick={handleExportAll}
            disabled={notes.length === 0}
            className="flex items-center gap-2 px-4 py-2 hover:bg-muted rounded-lg transition-colors disabled:opacity-50"
            title="导出全部"
          >
            <Download className="size-5" />
            <span className="text-sm">导出</span>
          </button>
          <Button onClick={() => openEditor()} size="lg" className="gap-2">
            <Plus className="size-5" />
            新建笔记
          </Button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        <div className="flex flex-col lg:flex-row gap-8">
          {/* Sidebar */}
          <aside className="lg:w-72 shrink-0 flex flex-col gap-y-6">
            <NoteSearch
              onResults={handleSearchResults}
              placeholder="搜索笔记..."
            />

            <div className="bg-card rounded-2xl border p-5">
              <h3 className="font-semibold text-lg mb-4">标签筛选</h3>
              <NoteTagFilter
                selectedTags={selectedTags}
                onTagsChange={setSelectedTags}
              />
            </div>
          </aside>

          {/* Main content */}
          <div className="flex-1">
            {filteredNotes.length === 0 ? (
              <div className="text-center py-20 bg-card rounded-2xl border border-dashed">
                <div className="size-20 rounded-2xl bg-blue-500/10 flex items-center justify-center mx-auto mb-6">
                  <span className="text-4xl">📝</span>
                </div>
                <p className="text-lg text-muted-foreground mb-2">
                  {searchQuery || selectedTags.length > 0
                    ? '没有找到匹配的笔记'
                    : '暂无笔记'}
                </p>
                {!searchQuery && selectedTags.length === 0 && (
                  <>
                    <p className="text-base text-muted-foreground mb-6">
                      在学习过程中可以添加笔记记录心得
                    </p>
                    <button type="button"
                      onClick={() => openEditor()}
                      className="px-6 py-3 text-base bg-primary text-primary-foreground rounded-xl hover:bg-primary/90 transition-colors"
                    >
                      创建第一条笔记
                    </button>
                  </>
                )}
              </div>
            ) : (
              <div className="flex flex-col gap-y-4">
                {filteredNotes.map((note) => (
                  <NoteCard
                    key={note.id}
                    note={note}
                    onEdit={openEditor}
                    onDelete={handleDelete}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Note Editor - Full Page Mode */}
      {showEditor && isFullPageEditor && (
        <div className="fixed inset-0 z-50 bg-background p-6">
          <NoteEditor
            note={editingNote}
            onSave={handleSave}
            onClose={closeEditor}
            isFullPage
          />
        </div>
      )}
    </div>
  )
}
