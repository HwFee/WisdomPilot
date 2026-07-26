"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { useReducer } from "react"
import { register } from "@/lib/api"
import { PanelTag } from "@/components/deck/kit"

const inputClassName =
  "w-full h-10 px-3 bg-panel-raised border border-line font-mono text-sm text-text placeholder:text-faint focus:outline-none focus:border-signal transition-colors"

const labelClassName = "block font-mono text-[11px] tracking-[1.5px] uppercase text-dim mb-2"

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
    <main className="min-h-screen deck-grid-bg flex items-center justify-center px-6 py-12">
      <div className="w-full max-w-[400px] deck-boot">
        <div className="deck-panel p-8">
          <PanelTag label="ENLIST · 创建账号" variant="on" />
          <div className="mt-6 mb-8 flex items-center gap-2.5 font-mono text-[13px] font-medium tracking-[1px] text-text">
            <span className="deck-signal-dot" />
            智码领航 <span className="text-faint font-normal">{'// TRAINING DECK'}</span>
          </div>
          <form onSubmit={handleSubmit} className="space-y-4">
            {state.error && (
              <div className="p-3 font-mono text-xs text-deck-red bg-deck-red/10 border border-deck-red/30">
                {state.error}
              </div>
            )}
            <div>
              <label htmlFor="username" className={labelClassName}>
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
                placeholder="你的呼号"
                className={inputClassName}
              />
            </div>
            <div>
              <label htmlFor="email" className={labelClassName}>
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
                value={state.password}
                onChange={(e) =>
                  dispatch({ type: "set_field", field: "password", value: e.target.value })
                }
                required
                minLength={8}
                placeholder="至少 8 位"
                className={inputClassName}
              />
            </div>
            <div>
              <label htmlFor="confirm-password" className={labelClassName}>
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
                placeholder="••••••••"
                className={inputClassName}
              />
            </div>
            <label className="flex items-center gap-2 font-mono text-xs text-dim">
              <input
                type="checkbox"
                checked={state.agree}
                onChange={(e) => dispatch({ type: "set_agree", value: e.target.checked })}
                className="size-4 accent-[#3fb950]"
              />
              我已阅读并同意服务条款
            </label>
            <button type="submit" disabled={state.loading} className="deck-btn-primary w-full">
              {state.loading ? "注册中..." : "注册"}
            </button>
            <div className="text-center font-mono text-xs">
              <Link href="/login" className="text-dim hover:text-signal transition-colors">
                已有账号？登录
              </Link>
            </div>
          </form>
        </div>
      </div>
    </main>
  )
}
