'use client'

import { useEffect, useState, useRef, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { Plus, Download } from 'lucide-react'
import { getStoredToken, logout } from '@/lib/api'
import {
  getNotes,
  deleteNote,
  exportNotes,
  getNoteTags,
  type NoteResponse,
  type NoteTagResponse,
} from '@/lib/api/notes'
import { NoteEditor } from '@/components/notes/NoteEditor'
import { NoteCard } from '@/components/notes/NoteCard'
import { NoteSearch } from '@/components/notes/NoteSearch'
import { NoteTagFilter } from '@/components/notes/NoteTagFilter'
import { Button } from '@/components/ui/button'

export default function NotesPage() {
  const { push, back } = useRouter()
  const [notesState, setNotesState] = useState({
    notes: [] as NoteResponse[],
    filteredNotes: [] as NoteResponse[],
    isLoading: true,
  })
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [editorState, setEditorState] = useState({
    showEditor: false,
    editingNote: null as NoteResponse | null,
    isFullPageEditor: false,
  })
  const { notes, filteredNotes, isLoading } = notesState
  const { showEditor, editingNote, isFullPageEditor } = editorState
  const hasFetched = useRef(false)
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const fetchData = useCallback(async (token: string) => {
    try {
      const [notesData, tagsData] = await Promise.all([
        getNotes(token),
        getNoteTags(token),
      ])
      setNotesState(prev => ({ ...prev, notes: notesData.notes, filteredNotes: notesData.notes }))
    } catch {
      // Handle error silently
    } finally {
      setNotesState(prev => ({ ...prev, isLoading: false }))
    }
  }, [])

  // 自动轮询：当有处理中的笔记时，每3秒刷新一次
  const fetchDataRef = useRef(fetchData)
  fetchDataRef.current = fetchData

  useEffect(() => {
    const hasProcessing = notes.some(
      (n) => n.processing_status === 'pending' || n.processing_status === 'processing'
    )

    if (hasProcessing) {
      pollingRef.current = setInterval(() => {
        const token = getStoredToken()
        if (token) {
          fetchDataRef.current(token)
        }
      }, 3000)
    }

    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current)
        pollingRef.current = null
      }
    }
  }, [notes])

  useEffect(() => {
    if (hasFetched.current) return
    const token = getStoredToken()
    if (!token) {
      logout()
      push('/login')
      return
    }
    hasFetched.current = true
    fetchData(token)
  }, [push, back, fetchData])

  // Filter notes when tags or search changes
  useEffect(() => {
    let filtered = notes

    // Filter by tags
    if (selectedTags.length > 0) {
      filtered = filtered.filter((note) =>
        selectedTags.every((tag) => note.tags?.includes(tag))
      )
    }

    // Filter by search query (handled by NoteSearch component)
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(
        (note) =>
          note.title?.toLowerCase().includes(query) ||
          note.content.toLowerCase().includes(query) ||
          note.knowledge_points?.some((kp) => kp.toLowerCase().includes(query))
      )
    }

    setNotesState(prev => ({ ...prev, filteredNotes: filtered }))
  }, [notes, selectedTags, searchQuery])

  const handleDelete = useCallback(async (noteId: string) => {
    // NoteCard already calls deleteNote, this just updates the UI
    setNotesState((prev) => ({ ...prev, notes: prev.notes.filter((n) => n.id !== noteId) }))
  }, [])

  const handleEdit = useCallback((note: NoteResponse) => {
    setEditorState({ editingNote: note, isFullPageEditor: true, showEditor: true })
  }, [])

  const handleCreate = useCallback(() => {
    setEditorState({ editingNote: null, isFullPageEditor: true, showEditor: true })
  }, [])

  const handleSave = useCallback((savedNote: NoteResponse) => {
    setNotesState((prev) => {
      const existing = prev.notes.find((n) => n.id === savedNote.id)
      let nextNotes: NoteResponse[]
      if (existing) {
        nextNotes = prev.notes.map((n) => (n.id === savedNote.id ? savedNote : n))
      } else {
        nextNotes = [savedNote, ...prev.notes]
      }
      return { ...prev, notes: nextNotes, filteredNotes: nextNotes }
    })
  }, [])

  const handleSearchResults = useCallback((results: NoteResponse[], query: string) => {
    if (query) {
      setSearchQuery(query)
      setNotesState(prev => ({ ...prev, filteredNotes: results }))
    } else {
      setSearchQuery('')
      // Re-apply tag filter when clearing search
      let filtered = notes
      if (selectedTags.length > 0) {
        filtered = filtered.filter((note) =>
          selectedTags.every((tag) => note.tags?.includes(tag))
        )
      }
      setNotesState(prev => ({ ...prev, filteredNotes: filtered }))
    }
  }, [notes, selectedTags])

  const handleExportAll = useCallback(async () => {
    const token = getStoredToken()
    if (!token || notes.length === 0) return

    try {
      const response = await exportNotes(token, {
        note_ids: notes.map((n) => n.id),
        format: 'markdown',
      })
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'my_notes.md'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('[笔记] 导出失败:', error)
    }
  }, [notes])

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
          <Button onClick={handleCreate} size="lg" className="gap-2">
            <Plus className="size-5" />
            新建笔记
          </Button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        <div className="flex flex-col lg:flex-row gap-8">
          {/* Sidebar */}
          <aside className="lg:w-72 shrink-0 flex flex-col gap-y-6">
            {/* Search */}
            <NoteSearch
              onResults={handleSearchResults}
              placeholder="搜索笔记..."
            />

            {/* Tags filter */}
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
                  <p className="text-base text-muted-foreground mb-6">
                    在学习过程中可以添加笔记记录心得
                  </p>
                )}
                {!searchQuery && selectedTags.length === 0 && (
                  <button type="button"
                    onClick={handleCreate}
                    className="px-6 py-3 text-base bg-primary text-primary-foreground rounded-xl hover:bg-primary/90 transition-colors"
                  >
                    创建第一条笔记
                  </button>
                )}
              </div>
            ) : (
              <div className="flex flex-col gap-y-4">
                {filteredNotes.map((note) => (
                  <NoteCard
                    key={note.id}
                    note={note}
                    onEdit={handleEdit}
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
            onClose={() => {
              setEditorState(prev => ({ ...prev, showEditor: false, isFullPageEditor: false }))
            }}
            isFullPage
          />
        </div>
      )}
    </div>
  )
}
