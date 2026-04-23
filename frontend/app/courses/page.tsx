'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { ArrowLeft, Code2, BookOpen, Target, Users, ArrowRight } from 'lucide-react'
import { getStoredToken } from '@/lib/api'
import { Card } from '@/components/ui/card'
import { DifficultyBadge } from '@/components/ui/badge'
import { staggerContainer, staggerItem } from '@/lib/animations'
import { getCourseConfig } from '@/lib/icons/course-icons'

const COURSES = [
  {
    id: 1,
    code: 'c',
    name: 'C语言程序设计',
    difficulty: 1,
    icon: Code2,
    description: '编程入门首选，打好扎实基础',
    learners: '12,580+'
  },
  {
    id: 2,
    code: 'cpp',
    name: 'C++程序设计',
    difficulty: 2,
    icon: Code2,
    description: '面向对象编程，系统开发利器',
    learners: '8,420+'
  },
  {
    id: 3,
    code: 'python',
    name: 'Python程序设计',
    difficulty: 1,
    icon: Code2,
    description: '简洁优雅，人工智能首选语言',
    learners: '25,800+'
  },
  {
    id: 4,
    code: 'java',
    name: 'Java程序设计',
    difficulty: 2,
    icon: Code2,
    description: '企业级开发，跨平台应用',
    learners: '15,300+'
  },
  {
    id: 5,
    code: 'rust',
    name: 'Rust程序设计',
    difficulty: 4,
    icon: Code2,
    description: '安全高效，系统编程新星',
    learners: '3,250+'
  },
  {
    id: 6,
    code: 'dsa',
    name: '数据结构与算法',
    difficulty: 3,
    icon: Target,
    description: '程序员内功，面试必考',
    learners: '18,900+'
  },
  {
    id: 7,
    code: 'algorithms',
    name: '算法设计与分析',
    difficulty: 4,
    icon: Target,
    description: '深入算法，提升编程思维',
    learners: '6,780+'
  },
  {
    id: 8,
    code: 'discrete',
    name: '离散数学',
    difficulty: 3,
    icon: BookOpen,
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
      <motion.header
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.3 }}
        className="fixed top-0 left-0 right-0 z-50 glass border-b border-border/50"
      >
        <div className="max-w-6xl mx-auto px-6">
          <div className="flex items-center justify-between h-16">
            <Link
              href="/dashboard"
              className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors group"
            >
              <ArrowLeft className="w-4 h-4 group-hover:-translate-x-0.5 transition-transform" />
              <span className="text-sm">返回</span>
            </Link>
            <h1 className="text-lg font-bold text-foreground">选择课程</h1>
            <div className="w-20"></div>
          </div>
        </div>
      </motion.header>

      {/* Main content */}
      <main className="pt-24 pb-12 px-6">
        <div className="max-w-6xl mx-auto">
          {/* 标题区域 */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="text-center mb-12"
          >
            <h2 className="text-3xl font-bold text-foreground mb-4">
              选择你的学习课程
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              从入门到进阶，覆盖主流编程语言和核心计算机科学知识
            </p>
          </motion.div>

          {/* Course grid */}
          <motion.div
            variants={staggerContainer}
            initial="initial"
            animate="animate"
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6"
          >
            {COURSES.map((course, index) => {
              const IconComponent = course.icon
              const courseConfig = getCourseConfig(course.code)

              return (
                <motion.div
                  key={course.id}
                  variants={staggerItem}
                  custom={index}
                >
                  <Link
                    href={`/mastery/${course.id}`}
                    className="group block"
                  >
                    <Card
                      variant="interactive"
                      padding="lg"
                      className="h-full"
                    >
                      {/* 难度指示 */}
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex gap-1">
                          {[...Array(4)].map((_, i) => (
                            <div
                              key={i}
                              className={`w-2 h-2 rounded-full transition-colors ${
                                i < course.difficulty ? 'bg-primary' : 'bg-muted'
                              }`}
                            />
                          ))}
                        </div>
                        {courseConfig && (
                          <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${courseConfig.bgColor} ${courseConfig.color}`}>
                            {courseConfig.icon}
                          </span>
                        )}
                      </div>

                      {/* Icon */}
                      <motion.div
                        whileHover={{ scale: 1.05 }}
                        className={cn(
                          "w-14 h-14 rounded-xl flex items-center justify-center mb-4 shadow-lg",
                          courseConfig
                            ? `bg-gradient-to-br ${courseConfig.gradient}`
                            : "bg-gradient-to-br from-primary to-primary-600"
                        )}
                      >
                        <IconComponent className="w-7 h-7 text-white" />
                      </motion.div>

                      {/* Content */}
                      <h3 className="text-lg font-semibold text-foreground mb-2 group-hover:text-primary transition-colors">
                        {course.name}
                      </h3>
                      <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
                        {course.description}
                      </p>

                      {/* Bottom info */}
                      <div className="flex items-center justify-between text-xs text-muted-foreground pt-2 border-t border-border/50">
                        <span className="flex items-center gap-1">
                          <Users className="w-3.5 h-3.5" />
                          {course.learners}
                        </span>
                        <span className="flex items-center gap-1 text-primary opacity-0 group-hover:opacity-100 transition-opacity font-medium">
                          进入
                          <ArrowRight className="w-3 h-3" />
                        </span>
                      </div>
                    </Card>
                  </Link>
                </motion.div>
              )
            })}
          </motion.div>
        </div>
      </main>
    </div>
  )
}

// Helper function
function cn(...classes: (string | boolean | undefined)[]) {
  return classes.filter(Boolean).join(' ')
}
