'use client'

import { useState, FormEvent, useTransition } from 'react'
import Link from 'next/link'
import { forgotPassword } from '@/lib/api'
import { validateEmail } from '@/lib/utils/validation'
import { Sparkles, Mail, AlertCircle, CheckCircle2, ArrowLeft } from 'lucide-react'
import { CharacterGroup } from '@/components/ui/animated-characters'

export default function ForgotPasswordPage() {
  const [isPending, startTransition] = useTransition()
  const [emailState, setEmailState] = useState({
    value: '',
    touched: false,
    error: null as string | null,
  })
  const [formStatus, setFormStatus] = useState({
    success: false,
    error: '',
  })
  const [lang, setLang] = useState<'zh' | 'en'>('zh')
  const { value: email, touched: emailTouched, error: emailError } = emailState
  const { success: isSuccess, error } = formStatus

  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)

  const handleEmailChange = (value: string) => {
    if (emailTouched) {
      const result = validateEmail(value, lang)
      setEmailState({ value, touched: true, error: result.valid ? null : result.error || null })
    } else {
      setEmailState(prev => ({ ...prev, value }))
    }
  }

  const handleEmailBlur = () => {
    const result = validateEmail(email, lang)
    setEmailState({ value: email, touched: true, error: result.valid ? null : result.error || null })
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setFormStatus({ success: false, error: '' })

    const result = validateEmail(email, lang)
    if (!result.valid) {
      setEmailState(prev => ({ ...prev, touched: true, error: result.error || null }))
      return
    }

    startTransition(async () => {
      try {
        await forgotPassword(email)
        setFormStatus({ success: true, error: '' })
      } catch (err) {
        setFormStatus({
          success: false,
          error: err instanceof Error ? err.message : t('发送失败，请稍后重试', 'Failed to send, please try again'),
        })
      }
    })
  }

  if (isSuccess) {
    return (
      <div className="min-h-screen grid lg:grid-cols-2">
        {/* Left decoration section */}
        <div className="relative hidden lg:flex flex-col justify-between bg-gradient-to-br from-primary/90 via-primary to-primary/80 p-12 text-primary-foreground">
          <div className="relative z-20">
            <div className="flex items-center gap-2 text-lg font-semibold">
              <div className="size-8 rounded-lg bg-primary-foreground/10 backdrop-blur-sm flex items-center justify-center">
                <Sparkles className="size-4" />
              </div>
              <span>{t('智码领航', 'ZhiMa LingHang')}</span>
            </div>
          </div>

          <div className="relative z-20 flex items-end justify-center h-[500px]">
            <CharacterGroup lang={lang} />
          </div>

          <div className="relative z-20 flex items-center gap-8 text-sm text-primary-foreground/60">
            <button type="button" className="hover:text-primary-foreground transition-colors bg-transparent border-none cursor-pointer">
              {t('隐私政策', 'Privacy Policy')}
            </button>
            <button type="button" className="hover:text-primary-foreground transition-colors bg-transparent border-none cursor-pointer">
              {t('服务条款', 'Terms of Service')}
            </button>
            <button type="button" className="hover:text-primary-foreground transition-colors bg-transparent border-none cursor-pointer">
              {t('联系我们', 'Contact')}
            </button>
          </div>

          <div className="absolute inset-0 bg-grid-white/[0.05] bg-[size:20px_20px]" />
          <div className="absolute top-1/4 right-1/4 size-64 bg-primary-foreground/10 rounded-full blur-3xl" />
          <div className="absolute bottom-1/4 left-1/4 size-96 bg-primary-foreground/5 rounded-full blur-3xl" />
        </div>

        {/* Right success message section */}
        <div className="flex items-center justify-center p-8 bg-background">
          <div className="w-full max-w-[420px]">
            {/* Mobile Logo */}
            <div className="lg:hidden flex items-center justify-center gap-2 text-lg font-semibold mb-12">
              <div className="size-8 rounded-lg bg-primary/10 flex items-center justify-center">
                <Sparkles className="size-4 text-primary" />
              </div>
              <span>{t('智码领航', 'ZhiMa LingHang')}</span>
            </div>

            <div className="text-center">
              <div className="size-16 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                <CheckCircle2 className="size-8 text-green-600 dark:text-green-400" />
              </div>
              <h1 className="text-2xl font-semibold text-foreground mb-2">
                {t('邮件已发送', 'Email Sent')}
              </h1>
              <p className="text-muted-foreground mb-6">
                {t(`我们已向 ${email} 发送了一封重置密码的邮件`, `We've sent a password reset email to ${email}`)}
              </p>
              <div className="bg-blue-50 dark:bg-blue-950/30 rounded-lg p-4 mb-6 text-left">
                <p className="text-sm text-blue-800 dark:text-blue-300">
                  {t('如果没有收到邮件，请检查垃圾邮件文件夹。链接将在 24 小时后过期。', 'If you don\'t see the email, check your spam folder. The link will expire in 24 hours.')}
                </p>
              </div>
              <Link
                href="/login"
                className="inline-flex items-center justify-center w-full px-4 py-3 text-sm font-medium text-primary-foreground bg-primary rounded-lg hover:bg-primary/90 transition-colors"
              >
                <ArrowLeft className="size-4 mr-2" />
                {t('返回登录', 'Back to Login')}
              </Link>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen grid lg:grid-cols-2">
      {/* Left decoration section */}
      <div className="relative hidden lg:flex flex-col justify-between bg-gradient-to-br from-primary/90 via-primary to-primary/80 p-12 text-primary-foreground">
        <div className="relative z-20">
          <div className="flex items-center gap-2 text-lg font-semibold">
            <div className="size-8 rounded-lg bg-primary-foreground/10 backdrop-blur-sm flex items-center justify-center">
              <Sparkles className="size-4" />
            </div>
            <span>{t('智码领航', 'ZhiMa LingHang')}</span>
          </div>
        </div>

        <div className="relative z-20 flex items-end justify-center h-[500px]">
          <CharacterGroup lang={lang} />
        </div>

        <div className="relative z-20 flex items-center gap-8 text-sm text-primary-foreground/60">
          <button type="button" className="hover:text-primary-foreground transition-colors bg-transparent border-none cursor-pointer">
            {t('隐私政策', 'Privacy Policy')}
          </button>
          <button type="button" className="hover:text-primary-foreground transition-colors bg-transparent border-none cursor-pointer">
            {t('服务条款', 'Terms of Service')}
          </button>
          <button type="button" className="hover:text-primary-foreground transition-colors bg-transparent border-none cursor-pointer">
            {t('联系我们', 'Contact')}
          </button>
        </div>

        <div className="absolute inset-0 bg-grid-white/[0.05] bg-[size:20px_20px]" />
        <div className="absolute top-1/4 right-1/4 size-64 bg-primary-foreground/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 left-1/4 size-96 bg-primary-foreground/5 rounded-full blur-3xl" />
      </div>

      {/* Right form section */}
      <div className="flex items-center justify-center p-8 bg-background relative">
        {/* Language Switcher */}
        <div className="absolute top-6 right-6">
          <div className="inline-flex items-center bg-secondary rounded-full p-1">
            <button type="button"
              onClick={() => setLang('zh')}
              className={`px-3 py-1 rounded-full text-[11px] font-medium transition-all ${
                lang === 'zh'
                  ? 'bg-primary text-primary-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              中文
            </button>
            <button type="button"
              onClick={() => setLang('en')}
              className={`px-3 py-1 rounded-full text-[11px] font-medium transition-all ${
                lang === 'en'
                  ? 'bg-primary text-primary-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              EN
            </button>
          </div>
        </div>

        <div className="w-full max-w-[420px]">
          {/* Mobile Logo */}
          <div className="lg:hidden flex items-center justify-center gap-2 text-lg font-semibold mb-12">
            <div className="size-8 rounded-lg bg-primary/10 flex items-center justify-center">
              <Sparkles className="size-4 text-primary" />
            </div>
            <span>{t('智码领航', 'ZhiMa LingHang')}</span>
          </div>

          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-semibold tracking-tight mb-2">{t('找回密码', 'Forgot Password')}</h1>
            <p className="text-muted-foreground text-sm">{t('输入您注册的邮箱，我们会发送重置密码的链接', 'Enter your registered email and we\'ll send you a reset link')}</p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="flex flex-col gap-y-4">
            {error && (
              <div className="p-3 text-sm text-red-400 bg-red-950/20 border border-red-900/30 rounded-lg flex items-center gap-2">
                <AlertCircle className="size-4 flex-shrink-0" />
                {error}
              </div>
            )}

            <div className="flex flex-col gap-y-2">
              <label htmlFor="email" className="text-sm font-medium text-foreground">
                {t('邮箱地址', 'Email Address')}
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(e) => handleEmailChange(e.target.value)}
                  onBlur={handleEmailBlur}
                  className={`w-full h-12 pl-10 pr-4 bg-background border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 transition-colors ${
                    emailTouched && emailError
                      ? 'border-red-500 focus:border-red-500'
                      : emailTouched && !emailError && email
                        ? 'border-green-500 focus:border-green-500'
                        : 'border-border/60 focus:border-primary'
                  }`}
                  placeholder={t('you@example.com', 'you@example.com')}
                />
                {emailTouched && !emailError && email && (
                  <CheckCircle2 className="absolute right-3 top-1/2 -translate-y-1/2 size-4 text-green-500" />
                )}
              </div>
              {emailTouched && emailError && (
                <p className="text-xs text-red-500 flex items-center gap-1 mt-1">
                  <AlertCircle className="size-3" />
                  {emailError}
                </p>
              )}
            </div>

            <button
              type="submit"
              disabled={isPending}
              className="w-full h-12 text-base font-medium text-primary-foreground bg-primary rounded-lg hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary/50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isPending ? t('发送中...', 'Sending...') : t('发送重置链接', 'Send Reset Link')}
            </button>

            <div className="text-center">
              <Link
                href="/login"
                className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                <ArrowLeft className="size-4 mr-1" />
                {t('返回登录', 'Back to Login')}
              </Link>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
