import Link from 'next/link'

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">D</span>
              </div>
              <h1 className="text-xl font-bold text-gray-900">
                AI 个性化编程教学平台
              </h1>
            </div>
            <div className="flex items-center gap-4">
              <Link
                href="/login"
                className="text-sm text-gray-600 hover:text-gray-900"
              >
                登录
              </Link>
              <Link
                href="/register"
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700"
              >
                立即注册
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center">
          <div className="flex justify-center mb-8">
            <div className="w-24 h-24 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-2xl flex items-center justify-center shadow-xl">
              <span className="text-white font-bold text-4xl">DSA</span>
            </div>
          </div>
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            数据结构与算法
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            面向中国大学生的精品课程 | AI 驱动的个性化学习 | 配套在线编程环境
          </p>
          <div className="flex justify-center gap-4">
            <Link
              href="/register"
              className="px-8 py-3 text-lg font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 shadow-lg"
            >
              开始学习
            </Link>
            <Link
              href="/login"
              className="px-8 py-3 text-lg font-medium text-blue-600 bg-white border-2 border-blue-600 rounded-lg hover:bg-blue-50"
            >
              已有账号登录
            </Link>
          </div>
        </div>

        {/* Features */}
        <div className="mt-24 grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="bg-white rounded-xl shadow-md p-6">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">系统化课程</h3>
            <p className="text-gray-600">
              从基础到高级，涵盖线性表、树、图、排序、查找等核心内容
            </p>
          </div>
          <div className="bg-white rounded-xl shadow-md p-6">
            <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">AI 个性化</h3>
            <p className="text-gray-600">
              根据你的学习进度，AI 动态调整教学内容，实现千人千面
            </p>
          </div>
          <div className="bg-white rounded-xl shadow-md p-6">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">在线编程</h3>
            <p className="text-gray-600">
              配套课后习题和在线编程环境，边学边练，即时反馈
            </p>
          </div>
        </div>

        {/* Course Chapters Preview */}
        <div className="mt-24">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
            课程内容预览
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
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
            ].map((chapter, idx) => (
              <div
                key={idx}
                className="bg-white rounded-lg shadow p-4 text-center hover:shadow-lg transition cursor-pointer"
              >
                <div className={`w-10 h-10 ${chapter.bg} rounded-lg flex items-center justify-center mx-auto mb-2`}>
                  <span className={`${chapter.text} font-bold text-sm`}>{chapter.num}</span>
                </div>
                <p className="text-sm font-medium text-gray-700">{chapter.name}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <footer className="mt-24 text-center text-gray-500">
          <p>© 2026 AI 个性化编程教学平台. All rights reserved.</p>
        </footer>
      </main>
    </div>
  )
}
