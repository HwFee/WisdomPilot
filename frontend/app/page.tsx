'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import {
  ArrowRight,
  Sparkles,
  Code2,
  BookOpen,
  Target,
  Zap,
  Brain,
  ChevronRight,
  Swords,
  FlaskConical,
} from 'lucide-react'
import { getCourseConfig } from '@/lib/icons/course-icons'
import { Logo } from '@/components/ui/logo'

// 实际 seeded 的 3 门课程
const COURSES = [
  { id: 1, code: 'c', name: 'C语言程序设计', difficulty: 1, description: '编程入门首选，打好扎实基础' },
  { id: 2, code: 'cpp', name: 'C++程序设计', difficulty: 2, description: '面向对象编程，系统开发利器' },
  { id: 3, code: 'python', name: 'Python程序设计', difficulty: 1, description: '简洁优雅，人工智能首选语言' },
]

const FEATURES = [
  {
    icon: BookOpen,
    title: '闯关式学习',
    desc: '按章节解锁知识点，每关配备讲解与练习，循序渐进掌握编程',
    gradient: 'from-blue-500 to-cyan-500',
  },
  {
    icon: Zap,
    title: '在线运行代码',
    desc: '集成 Monaco 编辑器与判题系统，实时编译运行，即时反馈结果',
    gradient: 'from-amber-500 to-orange-500',
  },
  {
    icon: Swords,
    title: '竞技场挑战',
    desc: '与其他学习者切磋，在实战中检验知识掌握程度',
    gradient: 'from-purple-500 to-pink-500',
  },
  {
    icon: Brain,
    title: 'AI 辅助学习',
    desc: '智能生成个性化练习与提示，按需获取帮助，避免过度依赖',
    gradient: 'from-emerald-500 to-teal-500',
  },
]

export default function Home() {
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    const token = localStorage.getItem('token')
    setIsLoggedIn(!!token)
  }, [])

  if (!mounted) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 glass border-b border-border/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3">
              <Logo className="text-blue-500" />
              <div>
                <h1 className="text-lg font-bold text-foreground">智码领航</h1>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {isLoggedIn ? (
                <Link
                  href="/dashboard"
                  className="px-5 py-2.5 text-sm font-medium text-primary-foreground bg-primary rounded-lg hover:bg-primary-600 transition-colors shadow-lg shadow-primary/25"
                >
                  进入学习
                </Link>
              ) : (
                <>
                  <Link
                    href="/login"
                    className="px-4 py-2 text-sm font-medium text-foreground hover:text-primary transition-colors"
                  >
                    登录
                  </Link>
                  <Link
                    href="/register"
                    className="px-5 py-2.5 text-sm font-medium text-primary-foreground bg-primary rounded-lg hover:bg-primary-600 transition-colors shadow-lg shadow-primary/25"
                  >
                    免费注册
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="relative pt-32 pb-20 overflow-hidden">
        <div className="absolute inset-0 gradient-mesh"></div>
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[600px] bg-primary/5 rounded-full blur-3xl"></div>

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-4xl mx-auto">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary/10 rounded-full text-sm text-primary mb-8">
              <Sparkles className="w-4 h-4" />
              <span>基于生成式 AI 的程序设计实践教学系统</span>
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-foreground mb-6 tracking-tight">
              开启你的
              <span className="text-gradient">编程学习之旅</span>
            </h1>

            <p className="text-lg sm:text-xl text-muted-foreground mb-10 max-w-2xl mx-auto">
              闯关式学习路径，AI 个性化推荐，在线代码运行与评测，
              <br className="hidden sm:block" />
              助你从零基础到熟练掌握编程技能
            </p>

            <div className="flex flex-col sm:flex-row justify-center gap-4">
              {!isLoggedIn && (
                <Link
                  href="/register"
                  className="group inline-flex items-center justify-center gap-2 px-8 py-4 text-base font-medium text-primary-foreground bg-primary rounded-xl hover:bg-primary-600 transition-all shadow-xl shadow-primary/25 hover-lift"
                >
                  免费开始学习
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </Link>
              )}
              <Link
                href="/courses"
                className="inline-flex items-center justify-center gap-2 px-8 py-4 text-base font-medium text-foreground bg-card border border-border rounded-xl hover:border-primary/50 hover:bg-muted transition-all"
              >
                <BookOpen className="w-5 h-5 text-primary" />
                浏览课程
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 border-y border-border bg-card/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-foreground mb-4">平台功能</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              结合 AI 技术打造的编程学习工具集
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {FEATURES.map((feature, index) => (
              <div
                key={index}
                className="group p-6 rounded-2xl bg-card border border-border hover:border-primary/30 transition-all card-interactive"
              >
                <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${feature.gradient} flex items-center justify-center mb-5 shadow-lg`}
                >
                  <feature.icon className="w-7 h-7 text-white" />
                </div>
                <h3 className="text-lg font-semibold text-foreground mb-2">{feature.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Courses */}
      <section className="py-20">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-foreground mb-4">课程</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              从入门到进阶，覆盖主流编程语言
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 max-w-4xl mx-auto">
            {COURSES.map((course) => {
              const config = getCourseConfig(course.code.toLowerCase())
              return (
                <Link
                  key={course.id}
                  href={isLoggedIn ? `/mastery/${course.id}` : '/register'}
                  className="group relative p-6 rounded-2xl bg-card border border-border hover:border-primary/40 transition-all card-interactive overflow-hidden"
                >
                  <div className={`absolute top-0 left-0 right-0 h-1 bg-gradient-to-r ${config?.gradient || 'from-primary to-primary-600'}`} />

                  <div className="flex items-center gap-4 mb-4 mt-2">
                    <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${config?.gradient || 'from-primary to-primary-600'} flex items-center justify-center shadow-lg group-hover:scale-105 transition-transform`}
                    >
                      <div className="w-7 h-7 text-white">{config?.icon}</div>
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-foreground group-hover:text-primary transition-colors">
                        {course.name}
                      </h3>
                      <div className="flex gap-1 mt-1">
                        {[...Array(4)].map((_, i) => (
                          <div key={i} className={`w-1.5 h-1.5 rounded-full ${i < course.difficulty ? 'bg-primary' : 'bg-muted'}`} />
                        ))}
                      </div>
                    </div>
                  </div>

                  <p className="text-sm text-muted-foreground mb-4 leading-relaxed">
                    {course.description}
                  </p>

                  <div className="flex items-center justify-between text-xs pt-3 border-t border-border/50">
                    <span className="text-muted-foreground">
                      难度 {Array(course.difficulty).fill('★').join('')}
                    </span>
                    <span className="flex items-center gap-1 text-primary font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                      开始学习
                      <ChevronRight className="w-3 h-3" />
                    </span>
                  </div>
                </Link>
              )
            })}
          </div>
        </div>
      </section>

      {/* Tools Grid */}
      <section className="py-20 bg-card/30 border-y border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold text-foreground mb-4">学习工具</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              多种工具辅助你的编程学习
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-3xl mx-auto">
            {[
              { icon: Target, label: '错题本', href: '/review', desc: '回顾错题' },
              { icon: BookOpen, label: '收藏夹', href: '/favorites', desc: '管理收藏' },
              { icon: FlaskConical, label: '代码沙盒', href: '/sandbox', desc: '自由实验' },
              { icon: Code2, label: '题解广场', href: '/solutions', desc: '参考题解' },
            ].map((tool) => (
              <Link
                key={tool.href}
                href={isLoggedIn ? tool.href : '/register'}
                className="group p-5 rounded-xl bg-card border border-border hover:border-primary/30 transition-all text-center"
              >
                <tool.icon className="w-8 h-8 text-primary mx-auto mb-3 group-hover:scale-110 transition-transform" />
                <div className="font-medium text-foreground text-sm">{tool.label}</div>
                <div className="text-xs text-muted-foreground mt-1">{tool.desc}</div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-primary/5"></div>
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-primary/10 rounded-full blur-3xl"></div>

        <div className="relative max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-foreground mb-6">
            准备好开始了吗？
          </h2>
          <p className="text-lg text-muted-foreground mb-10 max-w-2xl mx-auto">
            免费注册即可开始学习
            <br />
            无需信用卡，无任何隐藏费用
          </p>

          {!isLoggedIn && (
            <Link
              href="/register"
              className="group inline-flex items-center gap-3 px-10 py-5 text-lg font-medium text-primary-foreground bg-primary rounded-2xl hover:bg-primary-600 transition-all shadow-2xl shadow-primary/30 hover-lift"
            >
              立即免费注册
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </Link>
          )}
        </div>
      </section>

      {/* Footer */}
      <footer className="py-10 border-t border-border bg-card/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <Logo size={32} className="text-blue-500" />
              <span className="font-semibold text-foreground">智码领航</span>
            </div>
            <p className="text-sm text-muted-foreground">
              基于生成式 AI 的程序设计类课程实践教学系统
            </p>
            <p className="text-sm text-muted-foreground">
              &copy; 2026 智码领航
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
