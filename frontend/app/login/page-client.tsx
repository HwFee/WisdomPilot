"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { useState } from "react"
import { login } from "@/lib/api"
import { PanelTag } from "@/components/deck/kit"

const inputClassName =
  "w-full h-10 px-3 bg-panel-raised border border-line font-mono text-sm text-text placeholder:text-faint focus:outline-none focus:border-signal transition-colors"

const labelClassName = "block font-mono text-[11px] tracking-[1.5px] uppercase text-dim mb-2"

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
    <main className="min-h-screen deck-grid-bg flex items-center justify-center px-6 py-12">
      <div className="w-full max-w-[400px] deck-boot">
        <div className="deck-panel p-8">
          <PanelTag label="ACCESS · 身份验证" variant="on" />
          <div className="mt-6 mb-8 flex items-center gap-2.5 font-mono text-[13px] font-medium tracking-[1px] text-text">
            <span className="deck-signal-dot" />
            智码领航 <span className="text-faint font-normal">{'// TRAINING DECK'}</span>
          </div>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="p-3 font-mono text-xs text-deck-red bg-deck-red/10 border border-deck-red/30">
                {error}
              </div>
            )}
            <div>
              <label htmlFor="email" className={labelClassName}>
                邮箱
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="you@example.com"
                className={inputClassName}
              />
            </div>
            <div>
              <label htmlFor="password" className={labelClassName}>
                密码
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                placeholder="••••••••"
                className={inputClassName}
              />
            </div>
            <button type="submit" disabled={loading} className="deck-btn-primary w-full">
              {loading ? "登录中..." : "登录"}
            </button>
            <div className="flex items-center justify-between font-mono text-xs">
              <Link href="/register" className="text-dim hover:text-signal transition-colors">
                还没有账号？注册
              </Link>
              <Link href="/forgot-password" className="text-dim hover:text-signal transition-colors">
                忘记密码
              </Link>
            </div>
          </form>
        </div>
      </div>
    </main>
  )
}
