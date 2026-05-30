import Link from 'next/link'
import { Bot, Shield } from 'lucide-react'

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div>
      {/* AI 配置入口导航 - 独立模块 */}
      <div className="bg-card border-b border-border">
        <div className="max-w-7xl mx-auto px-4">
          <nav className="flex gap-4">
            <Link
              href="/admin"
              className="flex items-center gap-2 p-3 text-sm font-medium border-b-2 border-transparent hover:border-muted-foreground text-muted-foreground hover:text-foreground"
            >
              <Shield className="size-4" />
              用户管理
            </Link>
            <Link
              href="/admin/ai"
              className="flex items-center gap-2 p-3 text-sm font-medium border-b-2 border-transparent hover:border-muted-foreground text-muted-foreground hover:text-foreground"
            >
              <Bot className="size-4" />
              AI 配置
            </Link>
          </nav>
        </div>
      </div>
      {children}
    </div>
  )
}
