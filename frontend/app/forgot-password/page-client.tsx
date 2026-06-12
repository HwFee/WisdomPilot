"use client"

import { useState, FormEvent } from "react"
import Link from "next/link"
import { forgotPassword } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Panel, PanelHeader } from "@/components/layout"
import { ArrowLeft, CheckCircle2 } from "lucide-react"

export default function ForgotPasswordClient() {
  const [email, setEmail] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isSuccess, setIsSuccess] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsSubmitting(true)
    try {
      await forgotPassword(email)
      setIsSuccess(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : "发送失败，请稍后重试")
    } finally {
      setIsSubmitting(false)
    }
  }

  if (isSuccess) {
    return (
      <main className="min-h-screen bg-background flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-md">
          <Panel>
            <div className="p-8 text-center space-y-4">
              <div className="size-12 border border-border flex items-center justify-center mx-auto">
                <CheckCircle2 strokeWidth={1.5} className="size-6 text-foreground" />
              </div>
              <h1 className="text-lg font-semibold text-foreground">邮件已发送</h1>
              <p className="text-sm text-muted-foreground leading-relaxed">
                我们已向 {email} 发送了一封重置密码的邮件。如果没有收到，请检查垃圾邮件文件夹。链接将在 24 小时后过期。
              </p>
              <Button asChild variant="ghost" className="w-full">
                <Link href="/login">
                  <ArrowLeft className="size-4 mr-2" strokeWidth={1.5} />
                  返回登录
                </Link>
              </Button>
            </div>
          </Panel>
        </div>
      </main>
    )
  }

  return (
    <main className="min-h-screen bg-background flex items-center justify-center px-6 py-12">
      <div className="w-full max-w-md">
        <Panel>
          <PanelHeader title="找回密码" description="输入注册邮箱，我们会发送重置链接" />
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
                placeholder="you@example.com"
              />
            </div>
            <Button type="submit" disabled={isSubmitting} className="w-full">
              {isSubmitting ? "发送中..." : "发送重置链接"}
            </Button>
            <div className="text-center text-sm">
              <Link href="/login" className="text-muted-foreground hover:text-foreground">
                <ArrowLeft className="size-3 inline mr-1" strokeWidth={1.5} />
                返回登录
              </Link>
            </div>
          </form>
        </Panel>
      </div>
    </main>
  )
}
