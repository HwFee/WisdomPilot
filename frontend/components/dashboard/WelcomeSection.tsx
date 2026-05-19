'use client'

import { Sparkles, BookOpen } from 'lucide-react'
import { useState, useEffect, useMemo, useRef } from 'react'
import { LazyMotion, domAnimation, m, AnimatePresence } from 'framer-motion'

interface User {
  id: string
  username: string
}

interface WelcomeSectionProps {
  user: User
  lang?: 'zh' | 'en'
}

// 名言库
const QUOTES = [
  { content: '程序必须是为了给人看而写，给机器执行只是附带的。', author: 'Donald Knuth' },
  { content: '简单是可靠的先决条件。', author: 'Edsger Dijkstra' },
  { content: '先让它工作，再让它正确，最后让它快。', author: 'Kent Beck' },
  { content: '代码写得好，不如代码写得少。', author: 'Jeff Atwood' },
  { content: '任何傻瓜都能写出计算机能理解的代码，优秀的程序员写出人能理解的代码。', author: 'Martin Fowler' },
  { content: '最好的代码是没有代码。', author: 'Jeff Atwood' },
  { content: '编程不是关于你知道什么，而是关于你能想出什么。', author: 'Chris Pine' },
  { content: '好的代码本身就是最好的文档。', author: 'Steve McConnell' },
]

export function WelcomeSection({ user, lang = 'zh' }: WelcomeSectionProps) {
  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)
  const [quote, setQuote] = useState<{ content: string; author: string } | null>(null)
  const quoteIndexRef = useRef(0)

  // 随机选择一条名言
  useEffect(() => {
    const randomIndex = Math.floor(Math.random() * QUOTES.length)
    quoteIndexRef.current = randomIndex
    setQuote(QUOTES[randomIndex])
  }, [])

  // 每30秒更换名言
  useEffect(() => {
    const interval = setInterval(() => {
      const next = (quoteIndexRef.current + 1) % QUOTES.length
      quoteIndexRef.current = next
      setQuote(QUOTES[next])
    }, 30000)
    return () => clearInterval(interval)
  }, [])

  const getGreeting = () => {
    const hour = new Date().getHours()
    if (hour < 6) return t('夜深了', 'Good night')
    if (hour < 12) return t('早上好', 'Good morning')
    if (hour < 18) return t('下午好', 'Good afternoon')
    return t('晚上好', 'Good evening')
  }

  // 时间感知的背景渐变
  const bgGradient = useMemo(() => {
    const hour = new Date().getHours()
    if (hour < 6) return 'from-indigo-900/5 via-purple-900/5 to-blue-900/5' // 深夜
    if (hour < 12) return 'from-amber-100/20 via-orange-50/20 to-yellow-50/20' // 早晨
    if (hour < 18) return 'from-sky-100/20 via-blue-50/20 to-indigo-50/20'    // 下午
    return 'from-violet-100/20 via-purple-50/20 to-indigo-100/20'              // 傍晚
  }, [])

  return (
    <LazyMotion features={domAnimation}>
      <m.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="relative overflow-hidden rounded-xl p-4 bg-gradient-to-br border border-border/50"
      >
        {/* 背景装饰 */}
        <div className="absolute top-0 right-0 size-48 bg-primary/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />

        <div className="relative z-10 flex items-center gap-4">
          {/* 问候语和用户名 */}
          <div className="flex-1 min-w-0">
            <m.p
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.4, delay: 0.1 }}
              className="text-sm text-muted-foreground"
            >
              {getGreeting()}，<span className="font-semibold text-foreground">{user.username}</span>
            </m.p>

            {/* 名言 - 带渐入动画 */}
            <AnimatePresence mode="wait">
              {quote && (
                <m.p
                  key={quote.content}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.5 }}
                  className="text-xs text-muted-foreground/70 mt-1 italic truncate max-w-lg"
                >
                  "{quote.content}" : {quote.author}
                </m.p>
              )}
            </AnimatePresence>
          </div>

          {/* 右侧图标 */}
          <div className="flex-shrink-0">
            <div className="size-10 rounded-xl bg-gradient-to-br from-primary/20 to-primary/10 flex items-center justify-center">
              <Sparkles className="size-5 text-primary" />
            </div>
          </div>
        </div>
      </m.div>
    </LazyMotion>
  )
}
