'use client'

import { CourseChapter, getChapterTotalExercises } from '@/lib/course-data'
import { cn } from '@/lib/utils'
import { Clock, BookOpen, Sparkles, CheckCircle, FileText, ChevronLeft, ChevronRight, Check, LogOut, X, XCircle } from 'lucide-react'
import { useState, useEffect, useMemo } from 'react'

// Exercise interface
interface Exercise {
  id: number
  type: 'choice' | 'programming'
  question: string
  options?: string[]
  answer: number // index of correct answer (for choice, fallback only)
  template?: string // starter code (for programming)
  expectedOutput?: string // expected output (for programming)
}

// Exercise answer from backend
interface ExerciseAnswer {
  subsection_index: number
  exercise_id: number
  correct_answer_index: number
}

// Exercises for Chapter 1 Section 1 ("数据结构的基本概念")
const chapter1Section1Exercises: Exercise[] = [
  {
    id: 1,
    type: 'programming',
    question: '编程题：输出一行数字',
    template: '# 请在下方编写代码，输出一行：1 2 3\n# 注意：数字之间用空格分隔\n\n',
    expectedOutput: '1 2 3',
    answer: 0,
  },
  {
    id: 2,
    type: 'choice',
    question: '下列哪项不是数据结构研究的内容？',
    options: ['数据的逻辑结构', '数据的存储结构', '算法的执行速度', '数据的操作'],
    answer: 2,
  },
  {
    id: 3,
    type: 'choice',
    question: '良好的数据结构可以提高程序的什么？',
    options: ['运行速度和质量', '代码可读性', '程序员心情', '计算机使用寿命'],
    answer: 0,
  },
]

// Exercises for other sections (placeholder)
const getExercises = (chapterId: number, sectionIndex: number): Exercise[] => {
  if (chapterId === 1 && sectionIndex === 0) {
    return chapter1Section1Exercises
  }
  // Return empty for now - can be expanded later
  return []
}

interface ChapterContentProps {
  chapter: CourseChapter
  activeIndex: number
  onNavigate: (index: number) => void
  onStartIDE: () => void
  onStartIDEWithTemplate?: (template: string) => void  // 编程题打开IDE并传入模板
  isSplitScreen?: boolean  // IDE是否正在显示
  lang: 'zh' | 'en'
  completedExercisesBySubsection?: Record<number, number[]>  // {小节索引: [已完成习题ID列表]}
  onExerciseComplete?: (completedExercisesBySubsection: Record<number, number[]>, completedCount: number, totalCount: number) => void  // 进度更新回调
  exerciseAnswers?: ExerciseAnswer[]  // 后端返回的习题答案列表
}

export function ChapterContent({
  chapter,
  activeIndex,
  onNavigate,
  onStartIDE,
  onStartIDEWithTemplate,
  isSplitScreen = false,
  lang,
  completedExercisesBySubsection = {},
  onExerciseComplete,
  exerciseAnswers = [],
}: ChapterContentProps) {
  const t = (zh: string, en: string) => (lang === 'zh' ? zh : en)
  const [completedExercises, setCompletedExercises] = useState<number[]>([])
  const [selectedAnswers, setSelectedAnswers] = useState<Record<number, number>>({})
  const [submittedChoiceExercises, setSubmittedChoiceExercises] = useState<Record<number, boolean>>({})

  // 使用 useMemo 缓存 exercises，避免每次渲染创建新数组
  const exercises = useMemo(() => getExercises(chapter.id, activeIndex), [chapter.id, activeIndex])

  // 从后端答案列表中获取某道题的正确答案索引
  const getCorrectAnswerIndex = (exerciseId: number): number | null => {
    const answer = exerciseAnswers.find(
      a => Number(a.exercise_id) === exerciseId && Number(a.subsection_index) === activeIndex
    )
    return answer?.correct_answer_index ?? null
  }

  // 格式化选项标签 (A. xxx)
  const formatOptionLabel = (index: number, option: string): string => {
    return `${String.fromCharCode(65 + index)}. ${option}`
  }

  // 当 activeIndex 变化时，恢复已完成状态，但保留当前小节的用户作答状态
  useEffect(() => {
    const completedInCurrentSection = completedExercisesBySubsection[activeIndex] || []
    setCompletedExercises(completedInCurrentSection)
    // 不重置 selectedAnswers 和 submittedChoiceExercises，保留用户的选择
  }, [activeIndex])

  // 当 completedExercisesBySubsection 从后端加载变化时，同步 completedExercises
  useEffect(() => {
    const completedInCurrentSection = completedExercisesBySubsection[activeIndex] || []
    setCompletedExercises(completedInCurrentSection)
  }, [completedExercisesBySubsection, activeIndex])

  const handleAnswerSelect = (exerciseId: number, answerIndex: number) => {
    setSelectedAnswers(prev => ({ ...prev, [exerciseId]: answerIndex }))
  }

  // 选择题提交判题
  const handleSubmitChoice = (exerciseId: number) => {
    const selectedAnswer = selectedAnswers[exerciseId]
    if (selectedAnswer === undefined) return

    const correctAnswer = getCorrectAnswerIndex(exerciseId)
    if (correctAnswer !== null && selectedAnswer === correctAnswer) {
      // 答对了，标记完成
      handleMarkComplete(exerciseId)
    }
    // 标记为已提交（显示结果）
    setSubmittedChoiceExercises(prev => ({ ...prev, [exerciseId]: true }))
  }

  const handleMarkComplete = (exerciseId: number) => {
    // 只通知父组件，不直接设置 completedExercises
    // completedExercises 通过 useEffect 从 completedExercisesBySubsection prop 同步更新
    if (onExerciseComplete) {
      const currentCompleted = completedExercisesBySubsection[activeIndex] || []
      if (!currentCompleted.includes(exerciseId)) {
        const newCompleted = [...currentCompleted, exerciseId]
        const totalExercises = getChapterTotalExercises(chapter)
        const newCompletedExercisesBySubsection = {
          ...completedExercisesBySubsection,
          [activeIndex]: newCompleted,
        }
        onExerciseComplete(newCompletedExercisesBySubsection, newCompleted.length, totalExercises)
      }
    }
  }

  const activeSubsection = chapter.subsections[activeIndex]

  // Get content for the current subsection
  const getSubsectionContent = (subsection: string): { title: string; content: string[] } => {
    const contentMap: Record<string, { title: string; content: string[] }> = {
      // Chapter 1 content samples
      '数据结构的基本概念': {
        title: '数据结构的基本概念',
        content: [
          '数据结构是计算机存储、组织数据的方式。',
          '数据结构包括线性结构、树形结构和图形结构三大类。',
          '好的数据结构可以提高程序的效率和质量。',
        ],
      },
      '数据的逻辑结构': {
        title: '数据的逻辑结构',
        content: [
          '逻辑结构描述的是数据元素之间的逻辑关系。',
          '分为集合结构、线性结构、树形结构和图形结构。',
        ],
      },
      '数据的存储结构': {
        title: '数据的存储结构',
        content: [
          '存储结构是逻辑结构在计算机中的存储表示。',
          '分为顺序存储结构和链式存储结构两大类。',
        ],
      },
      '算法的定义': {
        title: '算法的定义',
        content: [
          '算法是解题步骤的描述。',
          '算法必须具有可行性、有穷性、确定性等基本特性。',
        ],
      },
      '算法的基本特性': {
        title: '算法的基本特性',
        content: [
          '有穷性：算法必须在有限步骤内完成。',
          '确定性：每条指令有明确的含义。',
          '可行性：算法可以执行。',
          '输入：算法有零个或多个输入。',
          '输出：算法至少有一个输出。',
        ],
      },
      '算法分析': {
        title: '算法分析',
        content: [
          '算法分析主要关注时间复杂度和空间复杂度。',
          '通过分析可以评估算法的效率。',
        ],
      },
      '时间复杂度': {
        title: '时间复杂度',
        content: [
          '时间复杂度表示算法运行所需时间与输入规模的关系。',
          '常用大O表示法：O(1)、O(log n)、O(n)、O(n log n)、O(n²)、O(2ⁿ)等。',
          '常数阶 O(1)：直接输出、简单计算',
          '对数阶 O(log n)：二分查找',
          '线性阶 O(n)：遍历数组',
          '平方阶 O(n²)：双重循环',
        ],
      },
      '空间复杂度': {
        title: '空间复杂度',
        content: [
          '空间复杂度表示算法所需内存空间与输入规模的关系。',
          '包括固定部分和可变部分。',
        ],
      },
      '顺序存储': {
        title: '顺序存储结构',
        content: [
          '顺序存储使用一段连续的存储单元存储数据。',
          '优点：可以实现随机访问。',
          '缺点：插入、删除操作需要移动大量元素。',
        ],
      },
      '链式存储': {
        title: '链式存储结构',
        content: [
          '链式存储使用指针将数据元素链接起来。',
          '优点：插入、删除操作方便。',
          '缺点：不能随机访问。',
        ],
      },
    }

    // For other subsections, return a default
    return contentMap[subsection] || {
      title: subsection,
      content: [
        `这是「${subsection}」的知识点内容。`,
        '理解这个概念对于掌握数据结构与算法至关重要。',
        '建议结合实际例子进行学习。',
      ],
    }
  }

  const content = getSubsectionContent(activeSubsection)

  const getDifficulty = () => {
    if (activeIndex < 4) return t('入门', 'Beginner')
    if (activeIndex < 8) return t('基础', 'Basic')
    if (activeIndex < 11) return t('进阶', 'Intermediate')
    return t('高级', 'Advanced')
  }

  return (
    <main className="h-full min-h-0 overflow-y-auto bg-gray-50" data-testid="content-area">
      <div className="max-w-3xl mx-auto px-6 py-8">
        {/* Content Header */}
        <div className="mb-8">
          {/* Breadcrumb */}
          <div className="flex items-center gap-2 text-sm text-gray-500 mb-3">
            <span
              className="px-2 py-0.5 rounded text-xs font-medium"
              style={{
                backgroundColor: `${chapter.color}15`,
                color: chapter.color,
              }}
            >
              {t(chapter.title, chapter.titleEn)}
            </span>
            <span className="text-gray-300">/</span>
            <span className="text-gray-400">
              {t('第', '')}{activeIndex + 1}{t('节', '')} / {chapter.subsections.length}
            </span>
          </div>

          {/* Title */}
          <h1 className="text-2xl font-bold text-gray-900 mb-4">
            {activeIndex + 1}. {activeSubsection}
          </h1>

          {/* Meta */}
          <div className="flex items-center gap-4 text-sm text-gray-500">
            <div className="flex items-center gap-1">
              <Clock className="w-4 h-4" />
              <span>
                {t('约', '')} 15 {t('分钟', 'min')}
              </span>
            </div>
            <div className="flex items-center gap-1">
              <BookOpen className="w-4 h-4" />
              <span>
                {t('学习难度', 'Difficulty')}: {getDifficulty()}
              </span>
            </div>
          </div>
        </div>

        {/* Content Body */}
        <div className="space-y-6">
          {/* Key Concepts Card */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <div className="flex items-start gap-4 mb-4">
              <div
                className="w-12 h-12 rounded-xl flex items-center justify-center shrink-0"
                style={{ backgroundColor: `${chapter.color}15` }}
              >
                <Sparkles className="w-6 h-6" style={{ color: chapter.color }} />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 mb-1">{content.title}</h3>
                <p className="text-sm text-gray-500">{t('核心知识点', 'Key Concepts')}</p>
              </div>
            </div>

            <ul className="space-y-3">
              {content.content.map((item, idx) => (
                <li key={idx} className="flex items-start gap-3">
                  <CheckCircle
                    className="w-5 h-5 shrink-0 mt-0.5"
                    style={{ color: chapter.color }}
                  />
                  <span className="text-gray-700 leading-relaxed">{item}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Related Concepts */}
          <div className="bg-gradient-to-r from-gray-50 to-gray-100 rounded-xl p-6">
            <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <FileText className="w-4 h-4" />
              {t('相关概念', 'Related Concepts')}
            </h4>
            <div className="flex flex-wrap gap-2">
              {chapter.topics.slice(0, 3).map((topic) => (
                <span
                  key={topic}
                  className="px-3 py-1 bg-white rounded-full text-sm text-gray-600 border border-gray-200"
                >
                  {topic}
                </span>
              ))}
              <span className="px-3 py-1 bg-white rounded-full text-sm text-gray-600 border border-gray-200">
                +{chapter.subsections.length - 3} {t('个小节', ' subsections')}
              </span>
            </div>
          </div>

          {/* Exercises Section */}
          {exercises.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <h4 className="font-semibold text-gray-900 flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-purple-600" />
                  {t('课后习题', 'Exercises')}
                </h4>
                <span className="text-sm text-gray-500">
                  {completedExercises.length}/{exercises.length} {t('已完成', 'completed')}
                </span>
              </div>
              <div className="space-y-6">
                {exercises.map((exercise) => (
                  <div key={exercise.id} className="border-b border-gray-100 pb-4 last:border-b-0 last:pb-0">
                    <p className="font-medium text-gray-800 mb-3">
                      {exercise.id}. {exercise.question}
                    </p>
                    {exercise.type === 'programming' ? (
                      // Programming exercise
                      <div className="bg-gray-50 rounded-lg p-4">
                        <div className="mb-3">
                          <span className="text-sm text-gray-500">{t('预期输出', 'Expected Output')}: </span>
                          <code className="text-sm bg-white px-2 py-1 rounded border">{exercise.expectedOutput}</code>
                        </div>
                        <button
                          onClick={() => {
                            if (isSplitScreen) {
                              // IDE is open, close it
                              onStartIDE()
                            } else if (exercise.template && onStartIDEWithTemplate) {
                              onStartIDEWithTemplate(exercise.template)
                            } else {
                              onStartIDE()
                            }
                          }}
                          className={cn(
                            'flex items-center gap-2 px-4 py-2 text-sm rounded-lg transition-colors',
                            isSplitScreen
                              ? 'bg-red-600 text-white hover:bg-red-700'
                              : 'bg-green-600 text-white hover:bg-green-700'
                          )}
                        >
                          {isSplitScreen ? (
                            <LogOut className="w-4 h-4" />
                          ) : (
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                            </svg>
                          )}
                          {isSplitScreen ? t('退出IDE', 'Exit IDE') : t('进入IDE作答', 'Open IDE')}
                        </button>
                      </div>
                    ) : (
                      // Choice exercise
                      <>
                        {exercise.options && (
                          <div className="space-y-2 mb-3">
                            {exercise.options.map((option, idx) => {
                              const isCompleted = completedExercises.includes(exercise.id)
                              const isSubmitted = submittedChoiceExercises[exercise.id]
                              const isSelected = selectedAnswers[exercise.id] === idx
                              const correctAnswer = getCorrectAnswerIndex(exercise.id)
                              const isCorrect = correctAnswer !== null ? idx === correctAnswer : idx === exercise.answer
                              const isWrong = isSubmitted && isSelected && !isCorrect

                              // 只有已提交或已完成时才显示结果
                              const showResult = isSubmitted || isCompleted

                              return (
                                <label
                                  key={idx}
                                  className={cn(
                                    'flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all',
                                    isWrong
                                      ? 'border-red-500 bg-red-50'
                                      : showResult && isCorrect
                                        ? isSelected
                                          ? 'border-green-500 bg-green-50'
                                          : 'border-green-300 bg-green-50/50'
                                        : isSelected
                                          ? 'border-purple-500 bg-purple-50'
                                          : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                                  )}
                                >
                                  <div
                                  className={cn(
                                    'w-4 h-4 rounded-full border-2 flex items-center justify-center transition-colors',
                                    isWrong
                                      ? 'border-red-500 bg-red-500'
                                      : showResult && isCorrect
                                        ? 'border-green-500 bg-green-500'
                                        : isSelected
                                          ? 'border-purple-500 bg-purple-500'
                                          : 'border-gray-400 bg-white'
                                  )}
                                >
                                  {isSelected && !isWrong && (
                                    <div className="w-2 h-2 bg-white rounded-full" />
                                  )}
                                  {showResult && isCorrect && !isSelected && (
                                    <Check className="w-3 h-3 text-white" />
                                  )}
                                </div>
                                  <input
                                    type="radio"
                                    name={`exercise-${exercise.id}`}
                                    checked={isSelected}
                                    onChange={() => handleAnswerSelect(exercise.id, idx)}
                                    disabled={isCompleted}
                                    style={{ display: 'none' }}
                                  />
                                  <span className={cn(
                                    'text-sm',
                                    showResult && isCorrect ? 'text-green-700 font-medium' : 'text-gray-700'
                                  )}>
                                    {option}
                                  </span>
                                  {showResult && isCorrect && (
                                    <Check className="w-4 h-4 text-green-600 ml-auto" />
                                  )}
                                  {isWrong && (
                                    <X className="w-4 h-4 text-red-600 ml-auto" />
                                  )}
                                </label>
                              )
                            })}
                          </div>
                        )}
                        {/* 选择题：已选择但未提交时显示提交按钮 */}
                        {selectedAnswers[exercise.id] !== undefined && !submittedChoiceExercises[exercise.id] && !completedExercises.includes(exercise.id) && (
                          <button
                            onClick={() => handleSubmitChoice(exercise.id)}
                            className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white text-sm rounded-lg hover:bg-purple-700 transition-colors"
                          >
                            <Check className="w-4 h-4" />
                            {t('确认答案', 'Submit Answer')}
                          </button>
                        )}
                        {/* 选择题结果区域：已提交或已完成时显示 */}
                        {(submittedChoiceExercises[exercise.id] || completedExercises.includes(exercise.id)) && (
                          <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-100">
                            {(() => {
                              const correctAnswer = getCorrectAnswerIndex(exercise.id)
                              const userAnswer = selectedAnswers[exercise.id]
                              const isCorrect = correctAnswer !== null ? userAnswer === correctAnswer : userAnswer === exercise.answer
                              if (isCorrect) {
                                return (
                                  <div className="flex items-center gap-2 text-green-600 text-sm">
                                    <CheckCircle className="w-4 h-4" />
                                    {t('已完成', 'Completed')}
                                  </div>
                                )
                              } else {
                                const correctIdx = correctAnswer !== null ? correctAnswer : exercise.answer
                                const correctOptionText = exercise.options?.[correctIdx]
                                return (
                                  <div className="flex items-center gap-2 text-red-600 text-sm">
                                    <XCircle className="w-4 h-4" />
                                    {t('回答错误', 'Wrong Answer')} · {t('正确答案：', 'Correct: ')}
                                    <span className="font-medium text-green-600">
                                      {correctOptionText ? formatOptionLabel(correctIdx, correctOptionText) : ''}
                                    </span>
                                  </div>
                                )
                              }
                            })()}
                          </div>
                        )}
                      </>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* DEBUG: Reset button */}
        <div className="fixed bottom-4 right-4 z-50">
          <button
            onClick={() => {
              setSelectedAnswers({})
              setSubmittedChoiceExercises({})
              setCompletedExercises([])
              alert('已重置所有答题状态（仅本地）')
            }}
            className="px-4 py-2 bg-yellow-500 text-white text-sm rounded-lg hover:bg-yellow-600 shadow-lg"
          >
            [DEBUG] 重置答题
          </button>
        </div>

        {/* Navigation Footer */}
        <div className="flex items-center justify-between mt-8 pt-6 border-t border-gray-200 relative z-50 bg-gray-50">
          <button
            onClick={() => onNavigate(Math.max(0, activeIndex - 1))}
            disabled={activeIndex === 0}
            className={`
              flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium
              transition-colors
              ${
                activeIndex === 0
                  ? 'text-gray-300 cursor-not-allowed'
                  : 'text-gray-600 hover:bg-gray-100'
              }
            `}
          >
            <ChevronLeft className="w-4 h-4" />
            {t('上一节', 'Previous')}
          </button>

          <span className="text-sm text-gray-500">
            {activeIndex + 1} / {chapter.subsections.length}
          </span>

          <button
            onClick={() => onNavigate(Math.min(chapter.subsections.length - 1, activeIndex + 1))}
            disabled={activeIndex === chapter.subsections.length - 1}
            className={`
              flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium
              transition-colors
              ${
                activeIndex === chapter.subsections.length - 1
                  ? 'text-gray-300 cursor-not-allowed'
                  : 'text-blue-600 hover:bg-blue-50'
              }
            `}
          >
            {t('下一节', 'Next')}
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </main>
  )
}
