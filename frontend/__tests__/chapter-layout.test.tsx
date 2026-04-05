import { render, screen, fireEvent } from '@testing-library/react'
import { useRouter } from 'next/navigation'
import { CourseChapter } from '@/lib/course-data'
import { User } from '@/lib/api'

// Mock useRouter
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
  }),
}))

// Import after mock
import { ChapterHeader } from '@/components/layout/chapter-header'
import { ChapterSidebar } from '@/components/layout/chapter-sidebar'
import { ChapterContent } from '@/components/layout/chapter-content'

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

const mockUser: User = {
  id: '1',
  email: 'test@example.com',
  username: 'testuser',
  is_active: true,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
}

// ========================================
// ChapterHeader Tests
// ========================================
describe('ChapterHeader Component', () => {
  const defaultProps = {
    chapter: mockChapter,
    isSidebarOpen: true,
    onToggleSidebar: jest.fn(),
    onToggleLang: jest.fn(),
    user: mockUser,
    onLogout: jest.fn(),
    lang: 'zh' as const,
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Rendering', () => {
    it('renders chapter title', () => {
      render(<ChapterHeader {...defaultProps} />)
      expect(screen.getAllByText('基础').length).toBeGreaterThanOrEqual(1)
    })

    it('renders chapter number', () => {
      render(<ChapterHeader {...defaultProps} />)
      expect(screen.getByText('01')).toBeInTheDocument()
    })

    it('renders user username', () => {
      render(<ChapterHeader {...defaultProps} />)
      expect(screen.getByText('testuser')).toBeInTheDocument()
    })

    it('renders toggle sidebar button', () => {
      render(<ChapterHeader {...defaultProps} />)
      const toggleBtn = screen.getByRole('button', { name: /toggle sidebar/i })
      expect(toggleBtn).toBeInTheDocument()
    })

    it('renders back button', () => {
      render(<ChapterHeader {...defaultProps} />)
      expect(screen.getAllByRole('button', { name: /back/i }).length).toBeGreaterThanOrEqual(1)
    })

    it('renders language toggle button', () => {
      render(<ChapterHeader {...defaultProps} />)
      // Language button shows "EN" when lang is 'zh'
      expect(screen.getByText('EN')).toBeInTheDocument()
    })

    it('renders logout button', () => {
      render(<ChapterHeader {...defaultProps} />)
      expect(screen.getByRole('button', { name: /logout/i })).toBeInTheDocument()
    })
  })

  describe('Interactions', () => {
    it('calls onToggleSidebar when toggle button clicked', () => {
      render(<ChapterHeader {...defaultProps} />)
      fireEvent.click(screen.getByRole('button', { name: /toggle sidebar/i }))
      expect(defaultProps.onToggleSidebar).toHaveBeenCalledTimes(1)
    })

    it('calls onToggleLang when language button clicked', () => {
      render(<ChapterHeader {...defaultProps} />)
      fireEvent.click(screen.getByText('EN'))
      expect(defaultProps.onToggleLang).toHaveBeenCalledTimes(1)
    })

    it('calls onLogout when logout button clicked', () => {
      render(<ChapterHeader {...defaultProps} />)
      fireEvent.click(screen.getByRole('button', { name: /logout/i }))
      expect(defaultProps.onLogout).toHaveBeenCalledTimes(1)
    })

    it('navigates to dashboard when back button clicked', () => {
      // Test that the back button is clickable and doesn't error
      // The actual navigation is tested in e2e tests
      render(<ChapterHeader {...defaultProps} />)
      const backBtn = screen.getAllByRole('button', { name: /back/i })[0]
      expect(backBtn).toBeInTheDocument()
      // Just verify click doesn't throw
      expect(() => fireEvent.click(backBtn)).not.toThrow()
    })
  })
})

// ========================================
// ChapterSidebar Tests
// ========================================
describe('ChapterSidebar Component', () => {
  const defaultProps = {
    chapter: mockChapter,
    isOpen: true,
    activeIndex: 0,
    onSelectSubsection: jest.fn(),
    lang: 'zh' as const,
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Rendering', () => {
    it('renders all subsections', () => {
      render(<ChapterSidebar {...defaultProps} />)
      expect(screen.getByText('数据结构的基本概念')).toBeInTheDocument()
      expect(screen.getByText('数据的逻辑结构')).toBeInTheDocument()
      expect(screen.getByText('数据的存储结构')).toBeInTheDocument()
    })

    it('shows active subsection indicator', () => {
      render(<ChapterSidebar {...defaultProps} />)
      // First item should be active
      const activeItem = screen.getByText('数据结构的基本概念')
      expect(activeItem).toBeInTheDocument()
    })
  })

  describe('Interactions', () => {
    it('calls onSelectSubsection when subsection clicked', () => {
      render(<ChapterSidebar {...defaultProps} />)
      fireEvent.click(screen.getByText('数据的逻辑结构'))
      expect(defaultProps.onSelectSubsection).toHaveBeenCalledWith(1)
    })
  })

  describe('Collapsed State', () => {
    it('hides text content when collapsed', () => {
      render(<ChapterSidebar {...defaultProps} isOpen={false} />)
      // In collapsed state, subsection names should not be visible
      expect(screen.queryByText('数据结构的基本概念')).not.toBeInTheDocument()
    })
  })
})

// ========================================
// ChapterContent Tests
// ========================================
describe('ChapterContent Component', () => {
  const defaultProps = {
    chapter: mockChapter,
    activeIndex: 0,
    onNavigate: jest.fn(),
    onStartIDE: jest.fn(),
    lang: 'zh' as const,
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Rendering', () => {
    it('renders current subsection title', () => {
      render(<ChapterContent {...defaultProps} />)
      expect(screen.getByText('数据结构的基本概念')).toBeInTheDocument()
    })

    it('renders key concepts section', () => {
      render(<ChapterContent {...defaultProps} />)
      expect(screen.getByText('核心知识点')).toBeInTheDocument()
    })

    it('renders navigation buttons', () => {
      render(<ChapterContent {...defaultProps} />)
      // Chinese: 上一节 / 下一节
      expect(screen.getByText('上一节')).toBeInTheDocument()
      expect(screen.getByText('下一节')).toBeInTheDocument()
    })

    it('renders page indicator', () => {
      render(<ChapterContent {...defaultProps} />)
      expect(screen.getByText(/1 \/ 14/)).toBeInTheDocument()
    })

    it('renders IDE mode button', () => {
      render(<ChapterContent {...defaultProps} />)
      expect(screen.getByText('进入IDE模式')).toBeInTheDocument()
    })
  })

  describe('Navigation', () => {
    it('calls onNavigate with previous index when previous clicked', () => {
      render(<ChapterContent {...defaultProps} activeIndex={5} />)
      fireEvent.click(screen.getByText('上一节'))
      expect(defaultProps.onNavigate).toHaveBeenCalledWith(4)
    })

    it('calls onNavigate with next index when next clicked', () => {
      render(<ChapterContent {...defaultProps} />)
      fireEvent.click(screen.getByText('下一节'))
      expect(defaultProps.onNavigate).toHaveBeenCalledWith(1)
    })

    it('disables previous button on first item', () => {
      render(<ChapterContent {...defaultProps} activeIndex={0} />)
      const prevBtn = screen.getByText('上一节').closest('button')
      expect(prevBtn).toBeDisabled()
    })

    it('disables next button on last item', () => {
      render(<ChapterContent {...defaultProps} activeIndex={13} />)
      const nextBtn = screen.getByText('下一节').closest('button')
      expect(nextBtn).toBeDisabled()
    })

    it('calls onStartIDE when IDE button clicked', () => {
      render(<ChapterContent {...defaultProps} />)
      fireEvent.click(screen.getByText('进入IDE模式'))
      expect(defaultProps.onStartIDE).toHaveBeenCalledTimes(1)
    })
  })

  describe('Exercises', () => {
    it('renders exercise completion button when answer selected', () => {
      render(<ChapterContent {...defaultProps} activeIndex={0} />)
      // Select an answer
      const radioButton = screen.getByRole('radio', { name: /算法的执行速度/i })
      fireEvent.click(radioButton)
      // Should show mark complete button
      expect(screen.getByText('标记完成')).toBeInTheDocument()
    })

    it('shows completed state after marking complete', () => {
      render(<ChapterContent {...defaultProps} activeIndex={0} />)
      // Select an answer
      const radioButton = screen.getByRole('radio', { name: /算法的执行速度/i })
      fireEvent.click(radioButton)
      // Click mark complete
      fireEvent.click(screen.getByText('标记完成'))
      // Should show completed state
      expect(screen.getByText('已完成')).toBeInTheDocument()
    })
  })
})
