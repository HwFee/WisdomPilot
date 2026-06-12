'use client'

import Link from 'next/link'
import { Plus, Download, ArrowLeft, FileText } from 'lucide-react'
import { NoteEditor } from '@/components/notes/NoteEditor'
import { NoteCard } from '@/components/notes/NoteCard'
import { NoteSearch } from '@/components/notes/NoteSearch'
import { NoteTagFilter } from '@/components/notes/NoteTagFilter'
import { Button } from '@/components/ui/button'
import { EmptyState, PageContainer, Panel, PanelHeader } from '@/components/layout'
import { useNotesData } from './hooks/use-notes-data'
import { useNoteEditor } from './hooks/use-note-editor'
import { exportAllNotes } from './lib/notes-export'

export default function NotesClient() {
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
      <header className="h-14 border-b bg-card">
        <div className="max-w-[1280px] mx-auto px-6 h-full flex items-center gap-3">
          <Button asChild variant="ghost" size="icon" aria-label="返回">
            <Link href="/dashboard"><ArrowLeft className="size-5" strokeWidth={1.5} /></Link>
          </Button>
          <h1 className="text-sm font-semibold uppercase tracking-[2px]">我的笔记</h1>
          <span className="ml-auto text-sm text-muted-foreground">{notes.length} 条</span>
          <Button variant="ghost" onClick={handleExportAll} disabled={notes.length === 0} title="导出全部">
            <Download className="size-4 mr-2" strokeWidth={1.5} />
            导出
          </Button>
          <Button onClick={() => openEditor()} className="gap-2">
            <Plus className="size-4" strokeWidth={1.5} />
            新建笔记
          </Button>
        </div>
      </header>

      <main className="bg-background">
        <PageContainer className="py-8">
          <div className="flex flex-col lg:flex-row gap-8">
            {/* Sidebar */}
            <aside className="lg:w-72 shrink-0 flex flex-col gap-y-6">
              <NoteSearch
                onResults={handleSearchResults}
                placeholder="搜索笔记..."
              />

              <Panel>
                <PanelHeader title="标签筛选" />
                <div className="p-5">
                  <NoteTagFilter
                    selectedTags={selectedTags}
                    onTagsChange={setSelectedTags}
                  />
                </div>
              </Panel>
            </aside>

            {/* Main content */}
            <div className="flex-1">
              {filteredNotes.length === 0 ? (
                searchQuery || selectedTags.length > 0 ? (
                  <EmptyState
                    icon={FileText}
                    title="没有找到匹配的笔记"
                    description="尝试更换关键词或清除标签筛选。"
                  />
                ) : (
                  <Panel>
                    <div className="flex flex-col items-center justify-center text-center px-8 py-16">
                      <div className="size-12 border border-border flex items-center justify-center mb-6">
                        <FileText className="size-6 text-muted-foreground" strokeWidth={1.5} />
                      </div>
                      <h2 className="text-lg font-semibold text-foreground mb-2">还没有笔记</h2>
                      <p className="text-sm text-muted-foreground max-w-md leading-relaxed mb-8">
                        开始记录你的学习心得。每道题、每个知识点都可以创建笔记。
                      </p>
                      <Button onClick={() => openEditor()}>
                        <Plus className="size-4 mr-2" strokeWidth={1.5} />
                        创建第一条笔记
                      </Button>
                    </div>
                  </Panel>
                )
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
        </PageContainer>
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
