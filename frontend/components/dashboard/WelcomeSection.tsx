'use client'

import { Flame } from 'lucide-react'
import { useState, useEffect, useRef } from 'react'

interface User {
  id: string
  username: string
}

interface WelcomeSectionProps {
  user: User
  lang?: 'zh' | 'en'
  streakDays?: number
}

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

const QUOTE_ROTATION_INTERVAL_MS = 30_000
const TIME_UPDATE_INTERVAL_MS = 60_000

function pad(n: number) {
  return String(n).padStart(2, '0')
}

function formatTime(date: Date) {
  return `${pad(date.getHours())}:${pad(date.getMinutes())}`
}

export function WelcomeSection({ user, lang = 'zh', streakDays = 0 }: WelcomeSectionProps) {
  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)
  const quoteIndexRef = useRef(0)
  const [quote, setQuote] = useState<{ content: string; author: string } | null>(() => {
    const index = Math.floor(Math.random() * QUOTES.length)
    quoteIndexRef.current = index
    return QUOTES[index]
  })
  const [time, setTime] = useState(() => formatTime(new Date()))

  useEffect(() => {
    const interval = setInterval(() => {
      const next = (quoteIndexRef.current + 1) % QUOTES.length
      quoteIndexRef.current = next
      setQuote(QUOTES[next])
    }, QUOTE_ROTATION_INTERVAL_MS)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    const interval = setInterval(() => setTime(formatTime(new Date())), TIME_UPDATE_INTERVAL_MS)
    return () => clearInterval(interval)
  }, [])

  const getGreeting = () => {
    const hour = new Date().getHours()
    if (hour < 6) return t('夜深了', 'Good night')
    if (hour < 12) return t('早上好', 'Good morning')
    if (hour < 18) return t('下午好', 'Good afternoon')
    return t('晚上好', 'Good evening')
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-12 pb-12 mb-12 border-b border-border">
      <div className="lg:col-span-2">
        <h1 className="text-3xl lg:text-4xl font-bold tracking-tight text-foreground">
          {getGreeting()}，<span className="text-primary">{user.username}！</span>
        </h1>
        <p className="mt-3 text-base text-muted-foreground max-w-md">
          {t('今天准备挑战点什么？', 'What would you like to challenge today?')}
        </p>
        {quote && (
          <blockquote className="mt-6 pl-4 border-l-2 border-foreground text-sm text-muted-foreground italic leading-relaxed">
            {quote.content}
            <cite className="block mt-1 not-italic text-xs text-muted-foreground/70">
              — {quote.author}
            </cite>
          </blockquote>
        )}
      </div>

      <div className="flex flex-col items-start text-left lg:items-end lg:text-right justify-center">
        <div className="text-5xl font-bold tracking-tight font-mono text-foreground">
          {time}
        </div>
        <div className="text-[13px] uppercase tracking-[2px] text-muted-foreground mt-2">
          {t('北京时间', 'Beijing Time')}
        </div>
        <div className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-muted rounded-full text-sm font-medium">
          <Flame className="w-4 h-4 text-orange-500" strokeWidth={1.5} />
          <span>
            {t('连续打卡', 'Streak')} {streakDays} {t('天', 'days')}
          </span>
        </div>
      </div>
    </div>
  )
}
