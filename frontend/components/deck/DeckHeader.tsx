'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { LogOut } from 'lucide-react'
import { getStoredUser, logout } from '@/lib/api'
import { getDeckDashboard } from '@/lib/api/deck/dashboard'
import { ThemeToggle } from './ThemeToggle'

const NAV_ITEMS = [
  { href: '/dashboard', label: '首页' },
  { href: '/review-gym', label: '审查室' },
  { href: '/arena', label: '竞技场' },
  { href: '/tutor', label: '导师' },
  { href: '/certification', label: '认证' },
  { href: '/review', label: '复盘' },
  { href: '/abilities', label: '图谱' },
] as const

/** 全局头部：品牌 + 主导航（四大模块 + 复盘 + 图谱）+ 智核 + 色系切换 + 用户 */
export function DeckHeader() {
  const pathname = usePathname()
  const { push } = useRouter()
  const [name, setName] = useState<string | null>(null)
  const [cores, setCores] = useState<number | null>(null)

  useEffect(() => {
    let alive = true
    getDeckDashboard()
      .then((d) => {
        if (!alive) return
        setName(d.user.name)
        setCores(d.user.cores)
      })
      .catch(() => {
        const stored = getStoredUser()
        if (alive && stored) setName(stored.username)
      })
    return () => {
      alive = false
    }
  }, [])

  const handleLogout = () => {
    logout()
    push('/login')
  }

  return (
    <header className="sticky top-0 z-50 h-[52px] border-b border-line bg-topbar backdrop-blur-sm">
      <div className="mx-auto flex h-full max-w-[1120px] items-center gap-5 px-7">
        <Link href="/dashboard" className="flex shrink-0 items-center gap-2.5">
          <span className="deck-signal-dot" />
          <span className="font-mono text-[13px] font-medium tracking-wider text-text">
            智码领航
          </span>
        </Link>

        <nav className="hidden flex-1 items-center gap-1 md:flex">
          {NAV_ITEMS.map((item) => {
            const active = pathname === item.href || pathname.startsWith(item.href + '/')
            return (
              <Link
                key={item.href}
                href={item.href}
                className={
                  active
                    ? 'rounded border border-line-bright bg-signal/10 px-3 py-1.5 font-mono text-xs text-signal transition-colors'
                    : 'rounded border border-transparent px-3 py-1.5 font-mono text-xs text-dim transition-colors hover:border-line hover:text-text'
                }
              >
                {item.label}
              </Link>
            )
          })}
        </nav>

        <div className="ml-auto flex items-center gap-4 md:ml-0">
          <ThemeToggle />
          {cores !== null && (
            <Link
              href="/profile"
              className="flex items-center gap-1.5 rounded border border-line px-2.5 py-1 font-mono text-xs text-dim transition-colors hover:border-line-bright"
              title="智核余额"
            >
              ◈ 智核 <b className="font-medium text-text">{cores}</b>
            </Link>
          )}
          <Link
            href="/profile"
            className="hidden font-mono text-xs text-dim transition-colors hover:text-text lg:block"
          >
            {name}
          </Link>
          <button
            type="button"
            onClick={handleLogout}
            aria-label="退出登录"
            title="退出登录"
            className="p-1.5 text-dim transition-colors hover:text-deck-red"
          >
            <LogOut className="size-4" strokeWidth={1.5} />
          </button>
        </div>
      </div>
    </header>
  )
}
