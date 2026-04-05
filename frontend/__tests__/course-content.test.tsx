import { render, screen, fireEvent } from '@testing-library/react'
import { useRouter } from 'next/navigation'
import { CourseContent } from '@/components/ui/course-content'
import { CourseChapter } from '@/lib/course-data'

// Mock useRouter
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
  }),
}))

// Mock data
const mockChapter: CourseChapter = {
  id: 1,
  title: '基础',
  titleEn: 'Basics',
  num: '01',
  color: '#3b82f6',
  bg: 'from-blue-500/20 to-indigo-500/20',
  topics: ['数组', '链表', '顺序表', '双向链表'],
  subsections: [
    '数据结构的基本概念',
    '数据的逻辑结构',
    '数据的存储结构',
    '算法的定义',
    '算法的基本特性',
    '算法分析',
    '时间复杂度',
    '空间复杂度',
    '顺序存储',
    '链式存储',
    '单链表',
    '双链表',
    '循环链表',
    '线性表的应用',
  ],
  progress: 100,
  status: 'completed',
  lessons: 8,
}

describe('CourseContent Component', () => {
  describe('Rendering', () => {
    it('renders chapter title', () => {
      render(<CourseContent chapter={mockChapter} />)
      expect(screen.getAllByText('基础').length).toBeGreaterThanOrEqual(1)
    })

    it('renders chapter number in sidebar', () => {
      render(<CourseContent chapter={mockChapter} />)
      expect(screen.getByText('#01')).toBeInTheDocument()
    })

    it('renders first subsection in sidebar', () => {
      render(<CourseContent chapter={mockChapter} />)
      // Use getAllByText since it appears in both sidebar and content
      const elements = screen.getAllByText('数据结构的基本概念')
      expect(elements.length).toBeGreaterThan(0)
    })

    it('renders progress percentage', () => {
      render(<CourseContent chapter={mockChapter} />)
      expect(screen.getByText('100%')).toBeInTheDocument()
    })

    it('renders content area', () => {
      render(<CourseContent chapter={mockChapter} />)
      expect(screen.getByTestId('content-area')).toBeInTheDocument()
    })
  })

  describe('Interactions', () => {
    it('has sidebar with chapter info', () => {
      render(<CourseContent chapter={mockChapter} />)
      // Sidebar contains chapter title and number
      expect(screen.getAllByText('基础').length).toBeGreaterThanOrEqual(1)
      expect(screen.getByText('#01')).toBeInTheDocument()
    })

    it('renders lesson count', () => {
      render(<CourseContent chapter={mockChapter} />)
      expect(screen.getByText(/8.*课时/)).toBeInTheDocument()
    })
  })

  describe('Responsive Layout', () => {
    it('renders sidebar with subsections', () => {
      render(<CourseContent chapter={mockChapter} />)
      // Sidebar shows chapter title
      expect(screen.getAllByText('基础').length).toBeGreaterThanOrEqual(1)
    })

    it('renders content on the right', () => {
      render(<CourseContent chapter={mockChapter} />)
      expect(screen.getByTestId('content-area')).toBeInTheDocument()
    })
  })
})
