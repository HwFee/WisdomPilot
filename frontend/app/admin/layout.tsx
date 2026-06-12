import Link from 'next/link'
import { Bot, Shield } from 'lucide-react'
import { cn } from '@/lib/utils'

const TABS = [
  { href: '/admin', label: '用户管理', icon: Shield },
  { href: '/admin/ai', label: 'AI 配置', icon: Bot },
] as const

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div>
      {/* AI 配置入口导航 - Swiss style with bottom-border active indicator */}
      <div className="bg-card border-b border-border">
        <div className="max-w-7xl mx-auto px-4">
          <nav className="flex gap-1">
            {TABS.map(tab => (
              <Link
                key={tab.href}
                href={tab.href}
                className={cn(
                  'flex items-center gap-2 px-4 py-3 text-sm font-medium',
                  'border-b-2 border-transparent text-muted-foreground',
                  'hover:text-foreground hover:border-foreground transition-colors'
                )}
              >
                <tab.icon className="size-4" />
                {tab.label}
              </Link>
            ))}
          </nav>
        </div>
      </div>
      {children}
    </div>
  )
}
