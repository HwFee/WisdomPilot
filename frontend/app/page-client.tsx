'use client'

import Link from 'next/link'
import {
  ArrowRight,
  Sparkles,
  BookOpen,
  Target,
  Zap,
  Brain,
  Swords,
  Code2,
} from 'lucide-react'
import { Logo } from '@/components/ui/logo'
import { PageContainer } from '@/components/layout'
import { CourseCard } from './components/course-card'
import { useHomeData } from './hooks/use-home-data'

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

const TOOLS = [
  { icon: Target, label: '错题本', href: '/review', desc: '回顾错题' },
  { icon: BookOpen, label: '收藏夹', href: '/favorites', desc: '管理收藏' },
  { icon: Code2, label: '题解广场', href: '/solutions', desc: '参考题解' },
]

function HeroDecoration() {
  return (
    <div className="relative hidden lg:flex items-center justify-center h-full min-h-[400px]">
      <div className="absolute inset-0 border border-border bg-card" />
      <div className="relative grid grid-cols-2 gap-4 p-8">
        <div className="w-32 h-32 border border-border bg-muted" />
        <div className="w-32 h-32 border border-border bg-primary/10" />
        <div className="w-32 h-32 border border-border bg-primary/10" />
        <div className="w-32 h-32 border border-border bg-muted" />
      </div>
    </div>
  )
}

export default function HomeClient() {
  const { isLoggedIn, mounted, courses, coursesLoading } = useHomeData()

  if (!mounted) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="animate-spin rounded-full size-8 border-b-2 border-primary" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-background border-b border-border">
        <PageContainer>
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3">
              <Logo className="text-blue-500" />
              <h1 className="text-lg font-semibold text-foreground">智码领航</h1>
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
                  <Link href="/login" className="px-4 py-2 text-sm font-medium text-foreground hover:text-primary transition-colors">
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
        </PageContainer>
      </header>

      {/* Hero */}
      <section className="min-h-screen flex items-center pt-16">
        <PageContainer className="w-full">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-12 items-center">
            <div className="lg:col-span-2 text-center lg:text-left">
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary/10 rounded-full text-sm text-primary mb-8">
                <Sparkles className="size-4" />
                <span>基于生成式 AI 的程序设计实践教学系统</span>
              </div>

              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-semibold text-foreground mb-6 tracking-tight">
                开启你的
                <span className="text-gradient">编程学习之旅</span>
              </h1>

              <p className="text-lg sm:text-xl text-muted-foreground mb-10 max-w-2xl mx-auto lg:mx-0">
                闯关式学习路径，AI 个性化推荐，在线代码运行与评测，
                <br className="hidden sm:block" />
                助你从零基础到熟练掌握编程技能
              </p>

              <div className="flex flex-col sm:flex-row justify-center lg:justify-start gap-4">
                {!isLoggedIn && (
                  <Link
                    href="/register"
                    className="group inline-flex items-center justify-center gap-2 px-8 py-4 text-base font-medium text-primary-foreground bg-primary rounded-xl hover:bg-primary-600 transition-all shadow-xl shadow-primary/25 hover-lift"
                  >
                    免费开始学习
                    <ArrowRight className="size-4 group-hover:translate-x-1 transition-transform" />
                  </Link>
                )}
                <Link
                  href="/courses"
                  className="inline-flex items-center justify-center gap-2 px-8 py-4 text-base font-medium text-foreground bg-card border border-border rounded-xl hover:border-primary/50 hover:bg-muted transition-all"
                >
                  <BookOpen className="size-5 text-primary" />
                  浏览课程
                </Link>
              </div>
            </div>

            <div className="lg:col-span-1">
              <HeroDecoration />
            </div>
          </div>
        </PageContainer>
      </section>

      {/* Features */}
      <section className="py-20 border-y border-border bg-card/30">
        <PageContainer>
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-semibold text-foreground mb-4">平台功能</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              结合 AI 技术打造的编程学习工具集
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
            {FEATURES.map((feature) => (
              <div
                key={feature.title}
                className="group p-6 rounded-2xl bg-card border border-border hover:border-primary/30 transition-all card-interactive"
              >
                <div className={`size-14 rounded-xl bg-gradient-to-br ${feature.gradient} flex items-center justify-center mb-5 shadow-lg`}>
                  <feature.icon className="size-7 text-white" />
                </div>
                <h3 className="text-lg font-semibold text-foreground mb-2">{feature.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{feature.desc}</p>
              </div>
            ))}
          </div>
        </PageContainer>
      </section>

      {/* Courses */}
      <section className="py-20">
        <PageContainer>
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-semibold text-foreground mb-4">课程</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              从入门到进阶，覆盖主流编程语言
            </p>
          </div>

          {coursesLoading ? (
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full size-8 border-b-2 border-primary" />
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
              {courses.map((course) => (
                <CourseCard key={course.id} course={course} />
              ))}
            </div>
          )}
        </PageContainer>
      </section>

      {/* Tools Grid */}
      <section className="py-20 bg-card/30 border-y border-border">
        <PageContainer>
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-semibold text-foreground mb-4">学习工具</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              多种工具辅助你的编程学习
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-3xl mx-auto">
            {TOOLS.map((tool) => (
              <Link
                key={tool.href}
                href={isLoggedIn ? tool.href : '/register'}
                className="group p-5 rounded-xl bg-card border border-border hover:border-primary/30 transition-all text-center"
              >
                <tool.icon className="size-8 text-primary mx-auto mb-3 group-hover:scale-110 transition-transform" />
                <div className="font-medium text-foreground text-sm">{tool.label}</div>
                <div className="text-xs text-muted-foreground mt-1">{tool.desc}</div>
              </Link>
            ))}
          </div>
        </PageContainer>
      </section>

      {/* CTA */}
      <section className="py-24 border-b border-border bg-card/30">
        <PageContainer className="text-center">
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-semibold text-foreground mb-6">
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
              <ArrowRight className="size-5 group-hover:translate-x-1 transition-transform" />
            </Link>
          )}
        </PageContainer>
      </section>

      {/* Footer */}
      <footer className="py-10 border-t border-border bg-card/50">
        <PageContainer>
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
        </PageContainer>
      </footer>
    </div>
  )
}