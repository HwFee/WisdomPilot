"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Panel, PanelHeader } from "@/components/layout"
import { register } from "@/lib/api"

export default function RegisterPageClient() {
  const router = useRouter()
  const [username, setUsername] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [agree, setAgree] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (password !== confirmPassword) {
      setError("两次输入的密码不一致")
      return
    }
    if (!agree) {
      setError("请先同意服务条款")
      return
    }

    setLoading(true)
    try {
      await register(email, username, password)
      router.push("/dashboard")
    } catch (err) {
      setError(err instanceof Error ? err.message : "注册失败")
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-background flex items-center justify-center px-6 py-12">
      <div className="w-full max-w-md">
        <Panel>
          <PanelHeader title="注册" description="创建账号开始你的学习之旅" />
          <form onSubmit={handleSubmit} className="p-8 space-y-4">
            {error && (
              <div className="p-3 text-sm text-destructive bg-destructive/10 border border-destructive/30">
                {error}
              </div>
            )}
            <div>
              <label htmlFor="username" className="block text-xs font-semibold uppercase tracking-[1px] text-muted-foreground mb-2">
                用户名
              </label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                className="w-full h-10 px-3 bg-background border border-border focus:outline-none focus:border-foreground"
              />
            </div>
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
                minLength={8}
                className="w-full h-10 px-3 bg-background border border-border focus:outline-none focus:border-foreground"
              />
            </div>
            <div>
              <label htmlFor="confirm-password" className="block text-xs font-semibold uppercase tracking-[1px] text-muted-foreground mb-2">
                确认密码
              </label>
              <input
                id="confirm-password"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                minLength={8}
                className="w-full h-10 px-3 bg-background border border-border focus:outline-none focus:border-foreground"
              />
            </div>
            <label className="flex items-center gap-2 text-sm text-muted-foreground">
              <input
                type="checkbox"
                checked={agree}
                onChange={(e) => setAgree(e.target.checked)}
                className="size-4"
              />
              我已阅读并同意服务条款
            </label>
            <Button type="submit" disabled={loading} className="w-full">
              {loading ? "注册中..." : "注册"}
            </Button>
            <div className="text-center text-sm">
              <Link href="/login" className="text-muted-foreground hover:text-foreground">
                已有账号？登录
              </Link>
            </div>
          </form>
        </Panel>
      </div>
    </main>
  )
}
