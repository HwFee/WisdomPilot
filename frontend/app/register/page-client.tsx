"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { useReducer } from "react"
import { Button } from "@/components/ui/button"
import { Panel, PanelHeader } from "@/components/layout"
import { register } from "@/lib/api"

// ========================================
// State / reducer (consolidates 7 useState calls)
// ========================================

interface RegisterFormState {
  username: string
  email: string
  password: string
  confirmPassword: string
  agree: boolean
  loading: boolean
  error: string | null
}

type RegisterFormAction =
  | { type: "set_field"; field: "username" | "email" | "password" | "confirmPassword"; value: string }
  | { type: "set_agree"; value: boolean }
  | { type: "set_error"; error: string | null }
  | { type: "set_loading"; loading: boolean }
  | { type: "reset" }

const initialState: RegisterFormState = {
  username: "",
  email: "",
  password: "",
  confirmPassword: "",
  agree: false,
  loading: false,
  error: null,
}

function registerReducer(state: RegisterFormState, action: RegisterFormAction): RegisterFormState {
  switch (action.type) {
    case "set_field":
      return { ...state, [action.field]: action.value }
    case "set_agree":
      return { ...state, agree: action.value }
    case "set_error":
      return { ...state, error: action.error }
    case "set_loading":
      return { ...state, loading: action.loading }
    case "reset":
      return initialState
    default:
      return state
  }
}

export default function RegisterPageClient() {
  const router = useRouter()
  const [state, dispatch] = useReducer(registerReducer, initialState)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    dispatch({ type: "set_error", error: null })

    if (state.password !== state.confirmPassword) {
      dispatch({ type: "set_error", error: "两次输入的密码不一致" })
      return
    }
    if (!state.agree) {
      dispatch({ type: "set_error", error: "请先同意服务条款" })
      return
    }

    dispatch({ type: "set_loading", loading: true })
    try {
      await register(state.email, state.username, state.password)
      router.push("/dashboard")
    } catch (err) {
      dispatch({
        type: "set_error",
        error: err instanceof Error ? err.message : "注册失败",
      })
    } finally {
      dispatch({ type: "set_loading", loading: false })
    }
  }

  return (
    <main className="min-h-screen bg-background flex items-center justify-center px-6 py-12">
      <div className="w-full max-w-md">
        <Panel>
          <PanelHeader title="注册" description="创建账号开始你的学习之旅" />
          <form onSubmit={handleSubmit} className="p-8 space-y-4">
            {state.error && (
              <div className="p-3 text-sm text-destructive bg-destructive/10 border border-destructive/30">
                {state.error}
              </div>
            )}
            <div>
              <label htmlFor="username" className="block text-xs font-semibold uppercase tracking-[1px] text-muted-foreground mb-2">
                用户名
              </label>
              <input
                id="username"
                type="text"
                value={state.username}
                onChange={(e) =>
                  dispatch({ type: "set_field", field: "username", value: e.target.value })
                }
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
                value={state.email}
                onChange={(e) =>
                  dispatch({ type: "set_field", field: "email", value: e.target.value })
                }
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
                value={state.password}
                onChange={(e) =>
                  dispatch({ type: "set_field", field: "password", value: e.target.value })
                }
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
                value={state.confirmPassword}
                onChange={(e) =>
                  dispatch({ type: "set_field", field: "confirmPassword", value: e.target.value })
                }
                required
                minLength={8}
                className="w-full h-10 px-3 bg-background border border-border focus:outline-none focus:border-foreground"
              />
            </div>
            <label className="flex items-center gap-2 text-sm text-muted-foreground">
              <input
                type="checkbox"
                checked={state.agree}
                onChange={(e) => dispatch({ type: "set_agree", value: e.target.checked })}
                className="size-4"
              />
              我已阅读并同意服务条款
            </label>
            <Button type="submit" disabled={state.loading} className="w-full">
              {state.loading ? "注册中..." : "注册"}
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
