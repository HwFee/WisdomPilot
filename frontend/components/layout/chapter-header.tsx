'use client'

import { useRouter } from 'next/navigation'
import { CourseChapter } from '@/lib/course-data'
import { User } from '@/lib/api'
import { ArrowLeft, LogOut, User as UserIcon, AlignLeft } from 'lucide-react'

interface ChapterHeaderProps {
  chapter: CourseChapter
  isSidebarOpen: boolean
  onToggleSidebar: () => void
  user: User | null
  onLogout: () => void
  onToggleLang: () => void
  lang: 'zh' | 'en'
}

export function ChapterHeader({
  chapter,
  isSidebarOpen,
  onToggleSidebar,
  user,
  onLogout,
  onToggleLang,
  lang,
}: ChapterHeaderProps) {
  const router = useRouter()
  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  const handleBack = () => {
    router.push('/dashboard')
  }

  return (
    <header className="fixed top-0 left-0 right-0 z-50 h-14 bg-white border-b border-gray-200">
      <div className="flex items-center justify-between h-full px-4">
        {/* Left Section: Back + Lines Icon + Chapter Title */}
        <div className="flex items-center gap-3">
          {/* Back Button */}
          <button
            onClick={handleBack}
            aria-label="Back"
            className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <ArrowLeft className="w-4 h-4 text-gray-600" />
          </button>

          {/* Lines Icon (Sidebar Toggle) */}
          <button
            onClick={onToggleSidebar}
            aria-label="Toggle sidebar"
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <AlignLeft className="w-5 h-5 text-gray-600" />
          </button>

          {/* Divider */}
          <div className="h-5 w-px bg-gray-200" />

          {/* Chapter Badge */}
          <div
            className="w-7 h-7 rounded-lg flex items-center justify-center font-bold text-xs"
            style={{
              backgroundColor: `${chapter.color}15`,
              color: chapter.color,
            }}
          >
            {chapter.num}
          </div>

          {/* Chapter Title */}
          <h1 className="font-medium text-gray-900 text-sm">
            {t(chapter.title, chapter.titleEn)}
          </h1>
        </div>

        {/* Center Section: Empty */}
        <div className="flex-1" />

        {/* Right Section: Language + User + Logout */}
        <div className="flex items-center gap-3">
          {/* Language Toggle */}
          <button
            onClick={onToggleLang}
            className="px-3 py-1.5 rounded-lg text-xs font-medium bg-gray-100 hover:bg-gray-200 transition-colors"
          >
            {lang === 'zh' ? 'EN' : '中文'}
          </button>

          {/* User Info */}
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
              <UserIcon className="w-4 h-4 text-gray-500" />
            </div>
            <span className="text-sm font-medium text-gray-700 hidden sm:inline">
              {user?.username}
            </span>
          </div>

          {/* Logout Button */}
          <button
            onClick={onLogout}
            aria-label="Logout"
            className="p-2 rounded-lg hover:bg-red-50 text-gray-500 hover:text-red-500 transition-colors"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  )
}
