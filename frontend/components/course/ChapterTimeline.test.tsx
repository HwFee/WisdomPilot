import { render, screen } from '@testing-library/react'
import { ChapterTimeline } from './ChapterTimeline'

describe('ChapterTimeline', () => {
  const mockChapters = [
    { id: 1, title: '变量基础', status: 'completed' as const },
    { id: 2, title: '数据类型', status: 'completed' as const },
    { id: 3, title: '运算符', status: 'in_progress' as const, progress: 60 },
    { id: 4, title: '输入输出', status: 'locked' as const },
    { id: 5, title: '条件判断', status: 'locked' as const },
  ]

  it('renders all chapters', () => {
    render(<ChapterTimeline chapters={mockChapters} onChapterClick={() => {}} />)
    expect(screen.getByText(/变量基础/)).toBeInTheDocument()
    expect(screen.getByText(/数据类型/)).toBeInTheDocument()
    expect(screen.getByText(/运算符/)).toBeInTheDocument()
  })

  it('shows completed status for completed chapters', () => {
    render(<ChapterTimeline chapters={mockChapters} onChapterClick={() => {}} />)
    expect(screen.getAllByText(/已完成/).length).toBeGreaterThan(0)
  })

  it('shows in progress status for current chapter', () => {
    render(<ChapterTimeline chapters={mockChapters} onChapterClick={() => {}} />)
    expect(screen.getByText(/进行中/)).toBeInTheDocument()
  })

  it('calls onChapterClick when clicking unlocked chapter', () => {
    const handleClick = jest.fn()
    render(<ChapterTimeline chapters={mockChapters} onChapterClick={handleClick} />)
    // The click handler is on the status icon container (node div)
    // We need to find and click the play icon for the in_progress chapter
    const playIcons = document.querySelectorAll('.bg-card.border-2')
    // Third chapter (index 2) is in_progress, click its container
    playIcons[2].dispatchEvent(new MouseEvent('click', { bubbles: true }))
    expect(handleClick).toHaveBeenCalledWith(3)
  })

  it('does not call onChapterClick when clicking locked chapter', () => {
    const handleClick = jest.fn()
    render(<ChapterTimeline chapters={mockChapters} onChapterClick={handleClick} />)
    // Find locked chapter containers and click - locked ones should not trigger
    const allContainers = document.querySelectorAll('.bg-card.border-2')
    // Fourth chapter (index 3) is locked
    allContainers[3].dispatchEvent(new MouseEvent('click', { bubbles: true }))
    expect(handleClick).not.toHaveBeenCalled()
  })

  it('shows locked text for locked chapters', () => {
    render(<ChapterTimeline chapters={mockChapters} onChapterClick={() => {}} />)
    expect(screen.getAllByText(/完成上一章节解锁/).length).toBeGreaterThan(0)
  })
})
