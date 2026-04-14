'use client'

import { Rocket, Sparkles, BookOpen, Code2, Clock } from 'lucide-react'
import { useState, useEffect } from 'react'

interface User {
  id: string
  username: string
}

interface LastProgress {
  courseName: string
  chapterName: string
}

interface WelcomeSectionProps {
  user: User
  lastProgress: LastProgress | null
  onContinueLearning: () => void
  lang?: 'zh' | 'en'
}

// 名言库
const QUOTES = [
  { content: '程序必须是为了给人看而写，给机器执行只是附带的。', author: 'Donald Knuth' },
  { content: '简单是可靠的先决条件。', author: 'Edsger Dijkstra' },
  { content: '先让它工作，再让它正确，最后让它快。', author: 'Kent Beck' },
  { content: '代码写得好，不如代码写得少。', author: 'Jeff Atwood' },
  { content: '任何傻瓜都能写出计算机能理解的代码，优秀的程序员写出人能理解的代码。', author: 'Martin Fowler' },
  { content: '调试代码比编写代码难两倍，所以如果你写代码时尽可能聪明，那么你就没有足够的智慧去调试它。', author: 'Brian Kernighan' },
  { content: '最好的代码是没有代码。', author: 'Jeff Atwood' },
  { content: '编程不是关于你知道什么，而是关于你能想出什么。', author: 'Chris Pine' },
  { content: '代码是写给人看的，顺便能在机器上运行。', author: 'Harold Abelson' },
  { content: '好的代码本身就是最好的文档。', author: 'Steve McConnell' },
]

export function WelcomeSection({ user, lastProgress, onContinueLearning, lang = 'zh' }: WelcomeSectionProps) {
  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)
  const [quote, setQuote] = useState<{ content: string; author: string } | null>(null)

  // 随机选择一条名言
  useEffect(() => {
    const randomIndex = Math.floor(Math.random() * QUOTES.length)
    setQuote(QUOTES[randomIndex])
  }, [])

  const getGreeting = () => {
    const hour = new Date().getHours()
    if (hour < 12) return t('早上好', 'Good morning')
    if (hour < 18) return t('下午好', 'Good afternoon')
    return t('晚上好', 'Good evening')
  }

  // 是否有学习进度
  const hasProgress = lastProgress && lastProgress.courseName

  return (
    <div className="flex flex-col gap-4">
      {/* 主行：问候语 + 继续学习按钮 */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 py-2">
        {/* 左侧：问候语 + 名言 */}
        <div className="flex-1">
          <p className="text-muted-foreground text-base mb-1">
            {getGreeting()}，
          </p>
          <h2 className="text-2xl sm:text-3xl font-bold text-foreground">
            {user.username}！
            <span className="text-muted-foreground font-normal text-xl sm:text-2xl ml-2">
              {hasProgress
                ? t('今天准备挑战点什么？', 'Ready to challenge today?')
                : t('开始你的编程之旅吧！', 'Start your coding journey!')}
            </span>
          </h2>

          {/* 名言 - 始终显示 */}
          {quote && (
            <p className="text-sm text-muted-foreground mt-2 italic">
              "{quote.content}"
              <span className="text-muted-foreground/60 ml-1">— {quote.author}</span>
            </p>
          )}
        </div>

        {/* 右侧：大按钮 */}
        <button
          onClick={onContinueLearning}
          className="flex items-center gap-2 px-8 py-4 bg-primary text-primary-foreground rounded-2xl font-semibold text-lg hover:bg-primary-600 transition-all shadow-xl shadow-primary/30 hover:shadow-2xl hover:shadow-primary/40 hover:-translate-y-0.5"
        >
          <Rocket className="w-6 h-6" />
          {hasProgress ? t('继续学习', 'Continue Learning') : t('开始学习', 'Start Learning')}
        </button>
      </div>
    </div>
  )
}
