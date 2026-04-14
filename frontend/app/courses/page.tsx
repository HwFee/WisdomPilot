'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft, Code2, BookOpen, Target, Users, ArrowRight } from 'lucide-react'
import { getStoredToken } from '@/lib/api'

const COURSES = [
  {
    id: 1,
    code: 'C',
    name: 'C语言程序设计',
    difficulty: 1,
    icon: Code2,
    gradient: 'from-blue-500 to-cyan-500',
    description: '编程入门首选，打好扎实基础',
    learners: '12,580+'
  },
  {
    id: 2,
    code: 'CPP',
    name: 'C++程序设计',
    difficulty: 2,
    icon: Code2,
    gradient: 'from-indigo-500 to-purple-500',
    description: '面向对象编程，系统开发利器',
    learners: '8,420+'
  },
  {
    id: 3,
    code: 'Python',
    name: 'Python程序设计',
    difficulty: 1,
    icon: Code2,
    gradient: 'from-green-500 to-teal-500',
    description: '简洁优雅，人工智能首选语言',
    learners: '25,800+'
  },
  {
    id: 4,
    code: 'Java',
    name: 'Java程序设计',
    difficulty: 2,
    icon: Code2,
    gradient: 'from-orange-500 to-red-500',
    description: '企业级开发，跨平台应用',
    learners: '15,300+'
  },
  {
    id: 5,
    code: 'Rust',
    name: 'Rust程序设计',
    difficulty: 4,
    icon: Code2,
    gradient: 'from-red-500 to-orange-600',
    description: '安全高效，系统编程新星',
    learners: '3,250+'
  },
  {
    id: 6,
    code: 'DSA',
    name: '数据结构与算法',
    difficulty: 3,
    icon: Target,
    gradient: 'from-emerald-500 to-green-600',
    description: '程序员内功，面试必考',
    learners: '18,900+'
  },
  {
    id: 7,
    code: 'ADA',
    name: '算法设计与分析',
    difficulty: 4,
    icon: Target,
    gradient: 'from-violet-500 to-purple-600',
    description: '深入算法，提升编程思维',
    learners: '6,780+'
  },
  {
    id: 8,
    code: 'DiscreteMath',
    name: '离散数学',
    difficulty: 3,
    icon: BookOpen,
    gradient: 'from-amber-500 to-yellow-600',
    description: '计算机科学数学基础',
    learners: '4,560+'
  },
]

export default function CoursesPage() {
  const router = useRouter()
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    const token = getStoredToken()
    if (!token) {
      router.push('/login')
      return
    }
    setIsLoggedIn(true)
  }, [router])

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
        <div className="max-w-6xl mx-auto px-6">
          <div className="flex items-center justify-between h-16">
            <Link href="/dashboard" className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors group">
              <ArrowLeft className="w-4 h-4 group-hover:-translate-x-0.5 transition-transform" />
              <span className="text-sm">返回</span>
            </Link>
            <h1 className="text-lg font-bold text-foreground">选择课程</h1>
            <div className="w-20"></div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="pt-24 pb-12 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-foreground mb-4">
              选择你的学习课程
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              从入门到进阶，覆盖主流编程语言和核心计算机科学知识
            </p>
          </div>

          {/* Course grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {COURSES.map((course) => {
              const IconComponent = course.icon
              return (
                <Link
                  key={course.id}
                  href={`/courses/${course.id}`}
                  className="group p-6 rounded-2xl bg-card border border-border hover:border-primary/40 transition-all hover:-translate-y-1 hover:shadow-lg"
                >
                  {/* Difficulty */}
                  <div className="flex gap-1 mb-4">
                    {[...Array(4)].map((_, i) => (
                      <div
                        key={i}
                        className={`w-2 h-2 rounded-full ${
                          i < course.difficulty ? 'bg-primary' : 'bg-muted'
                        }`}
                      />
                    ))}
                  </div>

                  {/* Icon */}
                  <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${course.gradient} flex items-center justify-center mb-4 shadow-lg group-hover:scale-105 transition-transform`}>
                    <IconComponent className="w-7 h-7 text-white" />
                  </div>

                  {/* Content */}
                  <h3 className="text-lg font-semibold text-foreground mb-2 group-hover:text-primary transition-colors">
                    {course.name}
                  </h3>
                  <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
                    {course.description}
                  </p>

                  {/* Bottom info */}
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Users className="w-3.5 h-3.5" />
                      {course.learners}
                    </span>
                    <span className="flex items-center gap-1 text-primary opacity-0 group-hover:opacity-100 transition-opacity">
                      进入
                      <ArrowRight className="w-3 h-3" />
                    </span>
                  </div>
                </Link>
              )
            })}
          </div>
        </div>
      </main>
    </div>
  )
}
