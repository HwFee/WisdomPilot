'use client'

import { useRouter } from 'next/navigation'
import { Zap, Trophy, Gem } from 'lucide-react'
import { Logo } from '@/components/ui/logo'
import { PageContainer } from '@/components/layout'
import { logout, type User } from '@/lib/api'
import type { UserProfileResponse } from '@/types/api'
import { type Language, translate } from '../dashboard-i18n'

type DashboardHeaderProps = {
  user: User | null
  profile: UserProfileResponse | null
  lang: Language
  onLanguageChange: (lang: Language) => void
}

export function DashboardHeader({
  user,
  profile,
  lang,
  onLanguageChange,
}: DashboardHeaderProps) {
  const { push } = useRouter()

  const handleLogout = () => {
    logout()
    push('/login')
  }

  const toggleLanguage = () => {
    const nextLang = lang === 'zh' ? 'en' : 'zh'
    onLanguageChange(nextLang)
  }

  const t = (zh: string, en: string) => translate(zh, en, lang)

  return (
    <header className="fixed top-0 left-0 right-0 z-50 glass border-b border-border/50">
      <PageContainer>
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center gap-3">
            <Logo className="text-blue-500" />
            <div>
              <h1 className="text-base font-semibold text-foreground">智码领航</h1>
              <p className="text-xs text-muted-foreground hidden sm:block">
                {t('基于生成式AI的实践教学系统', 'AI-Powered Learning')}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-2">
              <div className="flex items-center gap-1.5 px-2.5 py-1 bg-purple-500/10 rounded-full">
                <Gem className="size-3.5 text-purple-500" />
                <span className="text-xs font-medium text-purple-600 dark:text-purple-400">
                  {profile?.cores ?? 100}
                </span>
              </div>
            </div>

            <div className="flex items-center bg-muted rounded-full p-0.5">
              <button
                type="button"
                onClick={() => {
                  if (lang !== 'zh') toggleLanguage()
                }}
                className={`px-2 py-0.5 rounded-full text-xs font-medium transition-all ${
                  lang === 'zh'
                    ? 'bg-card text-foreground shadow-sm'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                中
              </button>
              <button
                type="button"
                onClick={() => {
                  if (lang !== 'en') toggleLanguage()
                }}
                className={`px-2 py-0.5 rounded-full text-xs font-medium transition-all ${
                  lang === 'en'
                    ? 'bg-card text-foreground shadow-sm'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                EN
              </button>
            </div>

            <div className="flex items-center gap-1 pl-2 border-l border-border">
              <button
                type="button"
                onClick={() => push('/cores')}
                className="p-2 text-purple-500 hover:text-purple-600 hover:bg-purple-500/10 rounded-lg transition-all"
                title={t('智核流水', 'Core Transactions')}
              >
                <Gem className="size-4" />
              </button>
              <button
                type="button"
                onClick={() => push('/tier')}
                className="p-2 text-amber-500 hover:text-amber-600 hover:bg-amber-500/10 rounded-lg transition-all"
                title={t('段位流水', 'Tier Transactions')}
              >
                <Trophy className="size-4" />
              </button>
              <button
                type="button"
                onClick={() => push('/xp')}
                className="p-2 text-blue-500 hover:text-blue-600 hover:bg-blue-500/10 rounded-lg transition-all"
                title={t('经验流水', 'XP Transactions')}
              >
                <Zap className="size-4" />
              </button>
              <span className="text-xs text-muted-foreground hidden lg:block ml-2">
                {user?.username}
              </span>
              <button
                type="button"
                onClick={handleLogout}
                className="p-2 text-muted-foreground hover:text-red-500 hover:bg-red-500/10 rounded-lg transition-all"
                title={t('退出登录', 'Logout')}
                aria-label={t('退出登录', 'Logout')}
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                  <polyline points="16 17 21 12 16 7" />
                  <line x1="21" x2="9" y1="12" y2="12" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </PageContainer>
    </header>
  )
}
