/**
 * @jest-environment jsdom
 */
import { render, screen, fireEvent } from '@testing-library/react'
import { MyCoursesGrid } from '../MyCoursesGrid'

describe('MyCoursesGrid', () => {
  const mockCourses = [
    { id: 1, name: 'C语言', progress: 50, color: '#0077B6' },
    { id: 2, name: 'Python', progress: 30, color: '#3776AB' },
    { id: 3, name: 'Java', progress: 70, color: '#ED8B00' },
  ]

  const mockRecommendedCourses = [
    { id: 4, name: 'Rust', color: '#CE422B', description: '系统编程新星' },
    { id: 5, name: 'Go', color: '#00ADD8', description: '云原生首选' },
  ]

  const mockOnSelectCourse = jest.fn()

  beforeEach(() => {
    mockOnSelectCourse.mockClear()
  })

  it('renders all courses', () => {
    render(
      <MyCoursesGrid
        courses={mockCourses}
        onSelectCourse={mockOnSelectCourse}
      />
    )

    expect(screen.getByText('C语言')).toBeInTheDocument()
    expect(screen.getByText('Python')).toBeInTheDocument()
    expect(screen.getByText('Java')).toBeInTheDocument()
  })

  it('displays progress percentage', () => {
    render(
      <MyCoursesGrid
        courses={mockCourses}
        onSelectCourse={mockOnSelectCourse}
      />
    )

    expect(screen.getByText('50%')).toBeInTheDocument()
    expect(screen.getByText('30%')).toBeInTheDocument()
    expect(screen.getByText('70%')).toBeInTheDocument()
  })

  it('shows course count in header', () => {
    render(
      <MyCoursesGrid
        courses={mockCourses}
        onSelectCourse={mockOnSelectCourse}
      />
    )

    expect(screen.getByText('(3)')).toBeInTheDocument()
  })

  it('calls onSelectCourse when course is clicked', () => {
    render(
      <MyCoursesGrid
        courses={mockCourses}
        onSelectCourse={mockOnSelectCourse}
      />
    )

    fireEvent.click(screen.getByText('C语言').closest('div')!)
    expect(mockOnSelectCourse).toHaveBeenCalledWith(1)
  })

  it('shows empty state when no courses', () => {
    render(
      <MyCoursesGrid
        courses={[]}
        onSelectCourse={mockOnSelectCourse}
        lang="zh"
      />
    )

    expect(screen.getByText('暂无课程')).toBeInTheDocument()
    expect(screen.getByText('选择一门课程开始学习吧')).toBeInTheDocument()
  })

  it('shows recommended courses in empty state', () => {
    render(
      <MyCoursesGrid
        courses={[]}
        recommendedCourses={mockRecommendedCourses}
        onSelectCourse={mockOnSelectCourse}
        lang="zh"
      />
    )

    expect(screen.getByText('推荐课程')).toBeInTheDocument()
    expect(screen.getByText('Rust')).toBeInTheDocument()
    expect(screen.getByText('Go')).toBeInTheDocument()
  })

  it('shows browse more courses link', () => {
    render(
      <MyCoursesGrid
        courses={mockCourses}
        onSelectCourse={mockOnSelectCourse}
        lang="zh"
      />
    )

    expect(screen.getByText('+ 浏览更多')).toBeInTheDocument()
  })

  it('displays English labels when lang is "en"', () => {
    render(
      <MyCoursesGrid
        courses={mockCourses}
        onSelectCourse={mockOnSelectCourse}
        lang="en"
      />
    )

    expect(screen.getByText('Learning')).toBeInTheDocument()
    // Multiple "Progress" labels exist, use getAllByText
    expect(screen.getAllByText('Progress').length).toBeGreaterThan(0)
  })

  it('applies compact mode', () => {
    const { container } = render(
      <MyCoursesGrid
        courses={mockCourses}
        onSelectCourse={mockOnSelectCourse}
        compact={true}
      />
    )

    // Compact mode should have overflow-hidden
    expect(container.querySelector('.overflow-hidden')).toBeInTheDocument()
  })
})
