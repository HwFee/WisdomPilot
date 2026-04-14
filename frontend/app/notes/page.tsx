'use client'

import { useEffect, useState, useRef, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { getStoredToken, logout, getNotes, deleteNote } from '@/lib/api'
import { ArrowLeft, FileText, Trash2, Edit2, Plus } from 'lucide-react'
import type { NoteResponse } from '@/types/api'

export default function NotesPage() {
  const router = useRouter()
  const [notes, setNotes] = useState<NoteResponse[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const hasFetched = useRef(false)

  const fetchData = useCallback(async (token: string) => {
    try {
      const data = await getNotes(token)
      setNotes(data.notes)
    } catch {
      // Handle error silently
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    if (hasFetched.current) return
    const token = getStoredToken()
    if (!token) {
      logout()
      router.push('/login')
      return
    }
    hasFetched.current = true
    fetchData(token)
  }, [router, fetchData])

  const handleDelete = async (noteId: string) => {
    const token = getStoredToken()
    if (!token) return

    try {
      await deleteNote(token, noteId)
      setNotes(prev => prev.filter(n => n.id !== noteId))
    } catch {
      // Handle error silently
    }
  }

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
      <header className="fixed top-0 left-0 right-0 z-50 glass border-b border-border/50">
        <div className="max-w-2xl mx-auto px-4 h-14 flex items-center gap-3">
          <button
            onClick={() => router.back()}
            className="p-2 hover:bg-muted rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <h1 className="text-lg font-semibold">笔记</h1>
          <span className="ml-auto text-sm text-muted-foreground">{notes.length} 条</span>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 pt-20 pb-8">
        {notes.length === 0 ? (
          <div className="text-center py-16">
            <div className="w-16 h-16 rounded-full bg-blue-500/10 flex items-center justify-center mx-auto mb-4">
              <FileText className="w-8 h-8 text-blue-500" />
            </div>
            <p className="text-muted-foreground">暂无笔记</p>
            <p className="text-sm text-muted-foreground mt-1">在学习过程中可以添加笔记记录心得</p>
          </div>
        ) : (
          <div className="space-y-3">
            {notes.map((note) => (
              <div
                key={note.id}
                className="bg-card rounded-xl border border-border p-4"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-blue-500/10 flex items-center justify-center">
                      <FileText className="w-4 h-4 text-blue-500" />
                    </div>
                    <div>
                      <p className="font-medium">{note.title || '无标题'}</p>
                      {note.chapter_id && (
                        <p className="text-xs text-muted-foreground">章节 {note.chapter_id}</p>
                      )}
                    </div>
                  </div>
                  <button
                    onClick={() => handleDelete(note.id)}
                    className="p-1.5 text-muted-foreground hover:text-red-500 hover:bg-red-500/10 rounded-lg transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
                <p className="text-sm text-foreground/80 whitespace-pre-wrap">{note.content}</p>
                <p className="text-xs text-muted-foreground mt-2">
                  {new Date(note.updated_at).toLocaleString('zh-CN')}
                </p>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
