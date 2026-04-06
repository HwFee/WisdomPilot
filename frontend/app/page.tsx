import Link from 'next/link'
import { BookOpen, Sparkles, Code2, ArrowRight } from 'lucide-react'

export default function Home() {
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="bg-card border-b border-border">
        <div className="max-w-5xl mx-auto px-6 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <span className="text-primary-foreground font-bold text-sm">D</span>
              </div>
              <h1 className="text-lg font-semibold text-foreground">
                AI 个性化编程教学平台
              </h1>
            </div>
            <div className="flex items-center gap-4">
              <Link
                href="/login"
                className="text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                登录
              </Link>
              <Link
                href="/register"
                className="px-4 py-2 text-sm font-medium text-primary-foreground bg-primary rounded-lg hover:opacity-90 transition-opacity"
              >
                立即注册
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Hero */}
      <main>
        <section className="max-w-5xl mx-auto px-6 py-24 text-center">
          <div className="flex justify-center mb-8">
            <div className="w-20 h-20 bg-primary rounded-2xl flex items-center justify-center shadow-lg shadow-primary/20">
              <span className="text-primary-foreground font-bold text-3xl">DSA</span>
            </div>
          </div>
          <h2 className="text-4xl font-bold text-foreground mb-4 tracking-tight">
            数据结构与算法
          </h2>
          <p className="text-lg text-muted-foreground mb-10 max-w-xl mx-auto">
            面向中国大学生的精品课程 · AI 驱动的个性化学习 · 配套在线编程环境
          </p>
          <div className="flex justify-center gap-3">
            <Link
              href="/register"
              className="px-6 py-3 text-base font-medium text-primary-foreground bg-primary rounded-xl hover:opacity-90 transition-opacity shadow-md shadow-primary/20"
            >
              开始学习
            </Link>
            <Link
              href="/login"
              className="px-6 py-3 text-base font-medium text-primary bg-background border border-primary rounded-xl hover:bg-muted transition-colors"
            >
              已有账号登录
            </Link>
          </div>
        </section>

        {/* Features */}
        <section className="bg-muted/30 py-20">
          <div className="max-w-5xl mx-auto px-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-card rounded-xl border border-border p-6">
                <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                  <BookOpen className="w-5 h-5 text-primary" />
                </div>
                <h3 className="text-base font-semibold text-foreground mb-2">系统化课程</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  从基础到高级，涵盖线性表、树、图、排序、查找等核心内容
                </p>
              </div>
              <div className="bg-card rounded-xl border border-border p-6">
                <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                  <Sparkles className="w-5 h-5 text-primary" />
                </div>
                <h3 className="text-base font-semibold text-foreground mb-2">AI 个性化</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  根据你的学习进度，AI 动态调整教学内容，实现千人千面
                </p>
              </div>
              <div className="bg-card rounded-xl border border-border p-6">
                <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                  <Code2 className="w-5 h-5 text-primary" />
                </div>
                <h3 className="text-base font-semibold text-foreground mb-2">在线编程</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  配套课后习题和在线编程环境，边学边练，即时反馈
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Chapter Preview */}
        <section className="max-w-5xl mx-auto px-6 py-20">
          <h3 className="text-2xl font-bold text-foreground text-center mb-10">
            课程内容预览
          </h3>
          <div className="grid grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
            {[
              { num: '01', name: '基础', bg: 'bg-blue-100', text: 'text-blue-600' },
              { num: '02', name: '栈与队列', bg: 'bg-emerald-100', text: 'text-emerald-600' },
              { num: '03', name: '字符串', bg: 'bg-violet-100', text: 'text-violet-600' },
              { num: '04', name: '树', bg: 'bg-teal-100', text: 'text-teal-600' },
              { num: '05', name: '二叉搜索树', bg: 'bg-cyan-100', text: 'text-cyan-600' },
              { num: '06', name: '图', bg: 'bg-indigo-100', text: 'text-indigo-600' },
              { num: '07', name: '排序', bg: 'bg-rose-100', text: 'text-rose-600' },
              { num: '08', name: '查找', bg: 'bg-amber-100', text: 'text-amber-600' },
              { num: '09', name: '经典算法', bg: 'bg-pink-100', text: 'text-pink-600' },
              { num: '10', name: '高级结构', bg: 'bg-sky-100', text: 'text-sky-600' },
              { num: '11', name: '算法思维', bg: 'bg-purple-100', text: 'text-purple-600' },
              { num: '12', name: '竞赛专题', bg: 'bg-orange-100', text: 'text-orange-600' },
            ].map((chapter) => (
              <div
                key={chapter.num}
                className="bg-card rounded-lg border border-border p-3 text-center hover:shadow-md hover:-translate-y-0.5 transition-all duration-150 cursor-pointer"
              >
                <div className={`w-8 h-8 ${chapter.bg} rounded-lg flex items-center justify-center mx-auto mb-2`}>
                  <span className={`${chapter.text} font-bold text-xs`}>{chapter.num}</span>
                </div>
                <p className="text-xs font-medium text-foreground">{chapter.name}</p>
              </div>
            ))}
          </div>
        </section>

        {/* CTA */}
        <section className="bg-primary/5 py-16">
          <div className="max-w-5xl mx-auto px-6 text-center">
            <h3 className="text-xl font-semibold text-foreground mb-3">
              准备好开始学习了吗？
            </h3>
            <p className="text-muted-foreground text-sm mb-6">
              加入我们，提升数据结构与算法能力
            </p>
            <Link
              href="/register"
              className="inline-flex items-center gap-2 px-6 py-3 text-base font-medium text-primary-foreground bg-primary rounded-xl hover:opacity-90 transition-opacity"
            >
              立即注册
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </section>

        {/* Footer */}
        <footer className="py-8 text-center">
          <p className="text-sm text-muted-foreground">
            © 2026 AI 个性化编程教学平台
          </p>
        </footer>
      </main>
    </div>
  )
}
