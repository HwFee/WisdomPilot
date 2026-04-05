import { render, screen } from '@testing-library/react'
import { useRouter } from 'next/navigation'
import { CourseContent } from '@/components/ui/course-content'
import { CourseChapter } from '@/lib/course-data'

// Mock useRouter
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
  }),
}))

// Chapter 2: Stack & Queue - for testing subsection content
const mockChapter2: CourseChapter = {
  id: 2,
  title: '栈与队列',
  titleEn: 'Stack & Queue',
  num: '02',
  color: '#10b981',
  bg: 'from-emerald-500/20 to-teal-500/20',
  topics: ['栈', '队列', '循环队列', '双端队列'],
  subsections: [
    '栈的基本概念',
    '栈的基本操作',
    '栈的顺序存储',
    '栈的链式存储',
    '栈的应用',
    '表达式求值',
    '括号匹配',
    '递归实现',
    '队列的基本概念',
    '队列的基本操作',
    '循环队列',
    '双端队列',
    '链式队列',
  ],
  progress: 100,
  status: 'completed',
  lessons: 10,
}

// Chapter 3: String - for testing
const mockChapter3: CourseChapter = {
  id: 3,
  title: '字符串',
  titleEn: 'String',
  num: '03',
  color: '#8b5cf6',
  bg: 'from-violet-500/20 to-purple-500/20',
  topics: ['字符串匹配', 'KMP', 'BM', 'Trie'],
  subsections: [
    '串的基本概念',
    'KMP算法',
    'KMPnext数组',
    'BM算法',
    'Trie树',
  ],
  progress: 85,
  status: 'learning',
  lessons: 8,
}

describe('CourseContent Subsection Navigation', () => {
  describe('Chapter 2: Stack & Queue', () => {
    it('shows all subsections in sidebar navigation', () => {
      render(<CourseContent chapter={mockChapter2} />)
      // getAllByText returns all matches - we expect at least one for each subsection
      expect(screen.getAllByText('栈的基本概念').length).toBeGreaterThanOrEqual(1)
      expect(screen.getAllByText('循环队列').length).toBeGreaterThanOrEqual(1)
      expect(screen.getAllByText('双端队列').length).toBeGreaterThanOrEqual(1)
    })

    it('shows chapter number and title correctly', () => {
      render(<CourseContent chapter={mockChapter2} />)
      expect(screen.getByText('#02')).toBeInTheDocument()
      expect(screen.getAllByText('栈与队列').length).toBeGreaterThanOrEqual(1)
    })

    it('shows correct lesson count', () => {
      render(<CourseContent chapter={mockChapter2} />)
      expect(screen.getByText(/10.*课时/)).toBeInTheDocument()
    })

    it('shows progress percentage', () => {
      render(<CourseContent chapter={mockChapter2} />)
      expect(screen.getByText('100%')).toBeInTheDocument()
    })
  })

  describe('Chapter 3: String', () => {
    it('shows all subsections in sidebar', () => {
      render(<CourseContent chapter={mockChapter3} />)
      expect(screen.getByText('KMP算法')).toBeInTheDocument()
      expect(screen.getByText('KMPnext数组')).toBeInTheDocument()
      expect(screen.getByText('Trie树')).toBeInTheDocument()
    })

    it('shows chapter number and title correctly', () => {
      render(<CourseContent chapter={mockChapter3} />)
      expect(screen.getByText('#03')).toBeInTheDocument()
      expect(screen.getAllByText('字符串').length).toBeGreaterThanOrEqual(1)
    })
  })

  describe('Content Area Display', () => {
    it('has a content area with test id', () => {
      render(<CourseContent chapter={mockChapter2} />)
      expect(screen.getByTestId('content-area')).toBeInTheDocument()
    })

    it('shows subsection number in content header', () => {
      render(<CourseContent chapter={mockChapter2} />)
      // Should show "第1节" initially
      expect(screen.getByText(/第.*1.*节/)).toBeInTheDocument()
    })

    it('has navigation section with page indicator', () => {
      render(<CourseContent chapter={mockChapter2} />)
      // Page indicator shows "1 / 13" format
      expect(screen.getByText(/1 \/ 13/)).toBeInTheDocument()
    })
  })

  describe('Subsection Content Rendering', () => {
    it('displays key concepts section', () => {
      render(<CourseContent chapter={mockChapter2} />)
      expect(screen.getByText('核心知识点')).toBeInTheDocument()
    })

    it('displays related concepts section', () => {
      render(<CourseContent chapter={mockChapter2} />)
      expect(screen.getByText('相关概念')).toBeInTheDocument()
    })

    it('displays difficulty indicator', () => {
      render(<CourseContent chapter={mockChapter2} />)
      expect(screen.getByText(/学习难度/)).toBeInTheDocument()
    })

    it('displays estimated time', () => {
      render(<CourseContent chapter={mockChapter2} />)
      expect(screen.getByText(/约.*分钟/)).toBeInTheDocument()
    })
  })
})
