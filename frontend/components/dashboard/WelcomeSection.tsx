'use client'

import { Sparkles } from 'lucide-react'
import { useState, useEffect, useRef } from 'react'

interface User {
  id: string
  username: string
}

interface WelcomeSectionProps {
  user: User
  lang?: 'zh' | 'en'
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

export function WelcomeSection({ user, lang = 'zh' }: WelcomeSectionProps) {
  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)
  const [quote, setQuote] = useState<{ content: string; author: string } | null>(null)
  const quoteIndexRef = useRef(0)

  useEffect(() => {
    const randomIndex = Math.floor(Math.random() * QUOTES.length)
    quoteIndexRef.current = randomIndex
    setQuote(QUOTES[randomIndex])
  }, [])

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

  return (
    <div className="bg-card border border-border rounded-2xl p-6">
      <div className="flex items-center justify-between">
        <div className="flex-1 min-w-0">
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            {getGreeting()}，<span className="text-primary">{user.username}</span>
          </h1>
          {quote && (
            <blockquote className="mt-3 pl-4 border-l-2 border-foreground text-sm text-muted-foreground italic leading-relaxed">
              {quote.content}
              <cite className="block mt-1 not-italic text-xs text-muted-foreground/70">
                — {quote.author}
              </cite>
            </blockquote>
          )}
        </div>
        <div className="flex-shrink-0 ml-6">
          <div className="w-12 h-12 rounded-xl bg-secondary border border-border flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-primary" strokeWidth={1.5} />
          </div>
        </div>
      </div>
    </div>
  )
}
