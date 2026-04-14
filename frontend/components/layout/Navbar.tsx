'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Sparkles, Code2, Search, LogOut, User, Settings } from 'lucide-react'
import { useState } from 'react'

interface User {
  id: string
  username: string
  email: string
}

interface NavbarProps {
  user: User | null
  isLoggedIn: boolean
  aiQuota: number
  xp: number
  lang?: 'zh' | 'en'
}

export function Navbar({ user, isLoggedIn, aiQuota, xp, lang = 'zh' }: NavbarProps) {
  const router = useRouter()
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false)

  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    router.push('/login')
  }

  return (
    <header className="fixed top-0 left-0 right-0 z-50 h-16 glass border-b border-border/50">
      <div className="max-w-7xl mx-auto px-6 h-full flex items-center justify-between">
        {/* Left: Logo */}
        <div className="flex items-center gap-3">
          <Link href="/" className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-primary-600 flex items-center justify-center shadow-lg shadow-primary/25">
              <Sparkles className="w-5 h-5 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-base font-bold text-foreground">GAI 编程教学平台</h1>
              <p className="text-xs text-muted-foreground hidden sm:block">
                {t('基于生成式AI的实践教学系统', 'AI-Powered Learning')}
              </p>
            </div>
          </Link>
        </div>

        {/* Center: Navigation Tabs */}
        <nav className="hidden md:flex items-center gap-1">
          <Link
            href="/dashboard"
            className="px-4 py-2 text-sm font-medium text-foreground hover:text-primary transition-colors rounded-lg hover:bg-muted/50"
          >
            {t('仪表盘', 'Dashboard')}
          </Link>
          <Link
            href="/courses"
            className="px-4 py-2 text-sm font-medium text-foreground hover:text-primary transition-colors rounded-lg hover:bg-muted/50"
          >
            {t('我的课程', 'My Courses')}
          </Link>
          <Link
            href="/leaderboard"
            className="px-4 py-2 text-sm font-medium text-foreground hover:text-primary transition-colors rounded-lg hover:bg-muted/50"
          >
            {t('排行榜', 'Leaderboard')}
          </Link>
        </nav>

        {/* Right: Actions */}
        <div className="flex items-center gap-3">
          {/* Search */}
          <button
            className="p-2 text-muted-foreground hover:text-foreground hover:bg-muted/50 rounded-lg transition-all"
            aria-label={t('搜索', 'Search')}
          >
            <Search className="w-5 h-5" />
          </button>

          {isLoggedIn ? (
            <>
              {/* Stats Pills */}
              <div className="hidden sm:flex items-center gap-2">
                <div className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-500/10 rounded-full">
                  <Sparkles className="w-4 h-4 text-blue-500" />
                  <span className="text-sm font-medium text-blue-600 dark:text-blue-400">
                    {aiQuota}
                  </span>
                </div>
                <div className="flex items-center gap-1.5 px-3 py-1.5 bg-yellow-500/10 rounded-full">
                  <span className="text-sm font-medium text-yellow-600 dark:text-yellow-400">
                    {xp} XP
                  </span>
                </div>
              </div>

              {/* Language Toggle */}
              <div className="flex items-center bg-muted rounded-full p-0.5">
                <button
                  className={`px-2.5 py-1 rounded-full text-xs font-medium transition-all ${
                    lang === 'zh' ? 'bg-card text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  中
                </button>
                <button
                  className={`px-2.5 py-1 rounded-full text-xs font-medium transition-all ${
                    lang === 'en' ? 'bg-card text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  EN
                </button>
              </div>

              {/* User Menu */}
              <div className="relative">
                <button
                  onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                  className="flex items-center gap-2 p-2 hover:bg-muted/50 rounded-lg transition-all"
                >
                  <span className="text-sm text-muted-foreground hidden lg:block">{user?.username}</span>
                  <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                    <User className="w-4 h-4 text-primary" />
                  </div>
                </button>

                {isUserMenuOpen && (
                  <div className="absolute right-0 mt-2 w-48 bg-card rounded-xl border border-border shadow-lg py-2">
                    <div className="px-4 py-2 border-b border-border">
                      <p className="text-sm font-medium text-foreground">{user?.username}</p>
                      <p className="text-xs text-muted-foreground">{user?.email}</p>
                    </div>
                    <Link
                      href="/profile"
                      className="flex items-center gap-2 px-4 py-2 text-sm text-foreground hover:bg-muted/50 transition-colors"
                    >
                      <User className="w-4 h-4" />
                      {t('个人主页', 'Profile')}
                    </Link>
                    <Link
                      href="/settings"
                      className="flex items-center gap-2 px-4 py-2 text-sm text-foreground hover:bg-muted/50 transition-colors"
                    >
                      <Settings className="w-4 h-4" />
                      {t('设置', 'Settings')}
                    </Link>
                    <button
                      onClick={handleLogout}
                      className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-500 hover:bg-red-500/10 transition-colors"
                    >
                      <LogOut className="w-4 h-4" />
                      {t('退出登录', 'Logout')}
                    </button>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="flex items-center gap-2">
              <Link
                href="/login"
                className="px-4 py-2 text-sm font-medium text-foreground hover:text-primary transition-colors"
              >
                {t('登录', 'Login')}
              </Link>
              <Link
                href="/register"
                className="px-4 py-2.5 text-sm font-medium text-primary-foreground bg-primary rounded-lg hover:bg-primary-600 transition-colors shadow-lg shadow-primary/25"
              >
                {t('免费注册', 'Register')}
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
