'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import { ArrowRight, Trophy, Sparkles, Code2, BookOpen, Zap, Target, Clock, Flame, Users } from 'lucide-react'

// 课程配置 - 使用设计系统的颜色
const COURSES = [
  {
    id: 1,
    code: 'C',
    name: 'C语言程序设计',
    difficulty: 1,
    icon: Code2,
    color: 'course-c',
    description: '编程入门首选，打好扎实基础',
    learners: '12,580+'
  },
  {
    id: 2,
    code: 'CPP',
    name: 'C++程序设计',
    difficulty: 2,
    icon: Code2,
    color: 'course-cpp',
    description: '面向对象编程，系统开发利器',
    learners: '8,420+'
  },
  {
    id: 3,
    code: 'Python',
    name: 'Python程序设计',
    difficulty: 1,
    icon: Code2,
    color: 'course-python',
    description: '简洁优雅，人工智能首选语言',
    learners: '25,800+'
  },
  {
    id: 4,
    code: 'Java',
    name: 'Java程序设计',
    difficulty: 2,
    icon: Code2,
    color: 'course-java',
    description: '企业级开发，跨平台应用',
    learners: '15,300+'
  },
  {
    id: 5,
    code: 'Rust',
    name: 'Rust程序设计',
    difficulty: 4,
    icon: Code2,
    color: 'course-rust',
    description: '安全高效，系统编程新星',
    learners: '3,250+'
  },
  {
    id: 6,
    code: 'DSA',
    name: '数据结构与算法',
    difficulty: 3,
    icon: Target,
    color: 'course-dsa',
    description: '程序员内功，面试必考',
    learners: '18,900+'
  },
  {
    id: 7,
    code: 'ADA',
    name: '算法设计与分析',
    difficulty: 4,
    icon: Target,
    color: 'course-ada',
    description: '深入算法，提升编程思维',
    learners: '6,780+'
  },
  {
    id: 8,
    code: 'DiscreteMath',
    name: '离散数学',
    difficulty: 3,
    icon: BookOpen,
    color: 'course-discrete',
    description: '计算机科学数学基础',
    learners: '4,560+'
  },
]

const STATS = [
  { value: '8', label: '精品课程', icon: BookOpen },
  { value: '1000+', label: '练习题目', icon: Code2 },
  { value: '50K+', label: '学习者', icon: Users },
  { value: '24/7', label: '在线学习', icon: Clock },
]

const FEATURES = [
  {
    icon: Sparkles,
    title: 'AI个性化学习',
    desc: '根据学习进度智能推荐，千人千面',
    gradient: 'from-blue-500 to-cyan-500'
  },
  {
    icon: Target,
    title: '闯关式学习',
    desc: '关卡验证机制，确保真正掌握',
    gradient: 'from-purple-500 to-pink-500'
  },
  {
    icon: Trophy,
    title: '排行榜激励',
    desc: '实时排名，激发学习动力',
    gradient: 'from-yellow-500 to-orange-500'
  },
  {
    icon: Clock,
    title: '间隔复习',
    desc: '艾宾浩斯遗忘曲线，科学复习',
    gradient: 'from-green-500 to-teal-500'
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

  // 获取课程颜色类名
  const getCourseColorClass = (color: string) => {
    return `bg-${color}`
  }

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
              <div className="w-10 h-10 bg-gradient-to-br from-primary to-primary-600 rounded-xl flex items-center justify-center shadow-lg shadow-primary/25">
                <Code2 className="w-5 h-5 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-foreground">GAI 编程教学平台</h1>
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

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 overflow-hidden">
        {/* 背景装饰 */}
        <div className="absolute inset-0 gradient-mesh"></div>
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[600px] bg-primary/5 rounded-full blur-3xl"></div>

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-4xl mx-auto">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary/10 rounded-full text-sm text-primary mb-8 animate-fade-in">
              <Sparkles className="w-4 h-4" />
              <span>AI驱动的个性化编程学习平台</span>
            </div>

            {/* 主标题 */}
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-foreground mb-6 tracking-tight animate-fade-in delay-100">
              开启你的
              <span className="text-gradient">编程学习之旅</span>
            </h1>

            {/* 副标题 */}
            <p className="text-lg sm:text-xl text-muted-foreground mb-10 max-w-2xl mx-auto animate-fade-in delay-200">
              8门精品编程课程，闯关式学习体验，AI个性化推荐，
              <br className="hidden sm:block" />
              科学复习机制，助你高效掌握编程技能
            </p>

            {/* CTA 按钮 */}
            <div className="flex flex-col sm:flex-row justify-center gap-4 animate-fade-in delay-300">
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
                href="/leaderboard"
                className="inline-flex items-center justify-center gap-2 px-8 py-4 text-base font-medium text-foreground bg-card border border-border rounded-xl hover:border-primary/50 hover:bg-muted transition-all"
              >
                <Trophy className="w-5 h-5 text-yellow-500" />
                查看排行榜
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-12 border-y border-border bg-card/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 lg:gap-8">
            {STATS.map((stat, index) => (
              <div
                key={index}
                className="flex items-center justify-center gap-4 p-4 rounded-2xl bg-card border border-border hover:border-primary/30 transition-colors"
              >
                <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
                  <stat.icon className="w-6 h-6 text-primary" />
                </div>
                <div>
                  <div className="text-2xl sm:text-3xl font-bold text-foreground">{stat.value}</div>
                  <div className="text-sm text-muted-foreground">{stat.label}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-foreground mb-4">
              为什么选择我们
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              我们结合最新的AI技术与教育心理学，打造最适合你的学习体验
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {FEATURES.map((feature, index) => (
              <div
                key={index}
                className="group p-6 rounded-2xl bg-card border border-border hover:border-primary/30 transition-all card-interactive"
              >
                <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${feature.gradient} flex items-center justify-center mb-5 shadow-lg`}>
                  <feature.icon className="w-7 h-7 text-white" />
                </div>
                <h3 className="text-lg font-semibold text-foreground mb-2">{feature.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Courses Section */}
      <section className="py-20 bg-card/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-foreground mb-4">
              选择课程开始学习
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              从入门到进阶，覆盖主流编程语言和核心计算机科学知识
            </p>
          </div>

          {/* Bento Grid 布局 */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6">
            {COURSES.map((course, index) => {
              const IconComponent = course.icon
              return (
                <Link
                  key={course.id}
                  href={isLoggedIn ? `/courses/${course.id}` : '/register'}
                  className={`group relative p-6 rounded-2xl bg-card border border-border hover:border-primary/40 transition-all card-interactive ${
                    index === 0 || index === 5 ? 'sm:col-span-2 lg:col-span-1' : ''
                  }`}
                >
                  {/* 难度指示 */}
                  <div className="absolute top-4 right-4 flex gap-1">
                    {[...Array(4)].map((_, i) => (
                      <div
                        key={i}
                        className={`w-1.5 h-1.5 rounded-full ${
                          i < course.difficulty ? 'bg-primary' : 'bg-muted'
                        }`}
                      />
                    ))}
                  </div>

                  {/* 图标 */}
                  <div className={`w-14 h-14 rounded-xl bg-${course.color} flex items-center justify-center mb-4 shadow-lg group-hover:scale-105 transition-transform`}>
                    <IconComponent className="w-7 h-7 text-white" />
                  </div>

                  {/* 内容 */}
                  <h3 className="text-lg font-semibold text-foreground mb-2 group-hover:text-primary transition-colors">
                    {course.name}
                  </h3>
                  <p className="text-sm text-muted-foreground mb-4 truncate-2">
                    {course.description}
                  </p>

                  {/* 底部信息 */}
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Users className="w-3.5 h-3.5" />
                      {course.learners}
                    </span>
                    <span className="flex items-center gap-1 text-primary opacity-0 group-hover:opacity-100 transition-opacity">
                      开始学习
                      <ArrowRight className="w-3 h-3" />
                    </span>
                  </div>
                </Link>
              )
            })}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 relative overflow-hidden">
        {/* 背景 */}
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-course-dsa/5"></div>
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-primary/10 rounded-full blur-3xl"></div>

        <div className="relative max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-yellow-500/10 rounded-full text-sm text-yellow-600 dark:text-yellow-400 mb-6">
            <Flame className="w-4 h-4" />
            <span>已有 50,000+ 学习者加入</span>
          </div>

          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-foreground mb-6">
            准备好提升编程能力了吗？
          </h2>
          <p className="text-lg text-muted-foreground mb-10 max-w-2xl mx-auto">
            免费注册，立即开始你的编程学习之旅
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
      <footer className="py-12 border-t border-border bg-card/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <Code2 className="w-4 h-4 text-primary-foreground" />
              </div>
              <span className="font-semibold text-foreground">GAI 编程教学平台</span>
            </div>
            <p className="text-sm text-muted-foreground text-center">
              © 2026 GAI 编程教学平台 · 计算机大赛项目
            </p>
            <div className="flex items-center gap-6 text-sm text-muted-foreground">
              <span className="hover:text-foreground transition-colors cursor-pointer">关于我们</span>
              <span className="hover:text-foreground transition-colors cursor-pointer">隐私政策</span>
              <span className="hover:text-foreground transition-colors cursor-pointer">使用条款</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
