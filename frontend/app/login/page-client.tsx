"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Panel, PanelHeader } from "@/components/layout"
import { login } from "@/lib/api"

export default function LoginPageClient() {
  const router = useRouter()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      await login(email, password, false)
      router.push("/dashboard")
    } catch (err) {
      setError(err instanceof Error ? err.message : "登录失败")
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-background flex items-center justify-center px-6 py-12">
      <div className="w-full max-w-md">
        <Panel>
          <PanelHeader title="登录" description="使用你的账号继续学习" />
          <form onSubmit={handleSubmit} className="p-8 space-y-4">
            {error && (
              <div className="p-3 text-sm text-destructive bg-destructive/10 border border-destructive/30">
                {error}
              </div>
            )}
            <div>
              <label htmlFor="email" className="block text-xs font-semibold uppercase tracking-[1px] text-muted-foreground mb-2">
                邮箱
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full h-10 px-3 bg-background border border-border focus:outline-none focus:border-foreground"
              />
            </div>
            <div>
              <label htmlFor="password" className="block text-xs font-semibold uppercase tracking-[1px] text-muted-foreground mb-2">
                密码
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full h-10 px-3 bg-background border border-border focus:outline-none focus:border-foreground"
              />
            </div>
            <Button type="submit" disabled={loading} className="w-full">
              {loading ? "登录中..." : "登录"}
            </Button>
            <div className="flex items-center justify-between text-sm">
              <Link href="/register" className="text-muted-foreground hover:text-foreground">
                还没有账号？注册
              </Link>
              <Link href="/forgot-password" className="text-muted-foreground hover:text-foreground">
                忘记密码
              </Link>
            </div>
          </form>
        </Panel>
      </div>
    </main>
  )
}
