/**
 * @jest-environment jsdom
 */
import { render, screen, fireEvent } from '@testing-library/react'
import { RecentActivity } from '../RecentActivity'

describe('RecentActivity', () => {
  const mockActivities = [
    { id: '1', type: 'exercise_complete', description: '完成了循环练习', created_at: '10分钟前' },
    { id: '2', type: 'chapter_complete', description: '完成了第3章', created_at: '1小时前' },
    { id: '3', type: 'achievement_earned', description: '获得了"坚持学习"成就', created_at: '2小时前' },
  ]

  it('renders activity items', () => {
    render(<RecentActivity activities={mockActivities} />)

    expect(screen.getByText('完成了循环练习')).toBeInTheDocument()
    expect(screen.getByText('完成了第3章')).toBeInTheDocument()
    expect(screen.getByText('获得了"坚持学习"成就')).toBeInTheDocument()
  })

  it('displays activity timestamps', () => {
    render(<RecentActivity activities={mockActivities} />)

    expect(screen.getByText('10分钟前')).toBeInTheDocument()
    expect(screen.getByText('1小时前')).toBeInTheDocument()
    expect(screen.getByText('2小时前')).toBeInTheDocument()
  })

  it('shows empty state when no activities', () => {
    const handleStartLearning = jest.fn()
    render(
      <RecentActivity
        activities={[]}
        onStartLearning={handleStartLearning}
        lang="zh"
      />
    )

    expect(screen.getByText('暂无学习记录')).toBeInTheDocument()
    expect(screen.getByText('开始你的学习之旅吧！')).toBeInTheDocument()
  })

  it('shows start learning button in empty state', () => {
    const handleStartLearning = jest.fn()
    render(
      <RecentActivity
        activities={[]}
        onStartLearning={handleStartLearning}
        lang="zh"
      />
    )

    fireEvent.click(screen.getByText('浏览课程'))
    expect(handleStartLearning).toHaveBeenCalledTimes(1)
  })

  it('displays correct icons for activity types', () => {
    const { container } = render(<RecentActivity activities={mockActivities} />)

    // Check for emoji icons
    expect(container.textContent).toContain('✅') // exercise_complete
    expect(container.textContent).toContain('📚') // chapter_complete
    expect(container.textContent).toContain('🏆') // achievement_earned
  })

  it('limits activities to 5 by default', () => {
    const manyActivities = Array.from({ length: 10 }, (_, i) => ({
      id: `${i}`,
      type: 'exercise_complete',
      description: `Activity ${i}`,
      created_at: `${i}分钟前`,
    }))

    render(<RecentActivity activities={manyActivities} />)

    // Should only show 5 activities
    expect(screen.getByText('Activity 0')).toBeInTheDocument()
    expect(screen.queryByText('Activity 5')).not.toBeInTheDocument()
  })

  it('limits activities to 3 in compact mode', () => {
    const manyActivities = Array.from({ length: 5 }, (_, i) => ({
      id: `${i}`,
      type: 'exercise_complete',
      description: `Activity ${i}`,
      created_at: `${i}分钟前`,
    }))

    render(<RecentActivity activities={manyActivities} compact={true} />)

    // Should only show 3 activities
    expect(screen.getByText('Activity 0')).toBeInTheDocument()
    expect(screen.queryByText('Activity 3')).not.toBeInTheDocument()
  })

  it('displays English labels when lang is "en"', () => {
    render(
      <RecentActivity
        activities={mockActivities}
        lang="en"
      />
    )

    expect(screen.getByText('Recent Activity')).toBeInTheDocument()
  })

  it('displays English empty state', () => {
    render(
      <RecentActivity
        activities={[]}
        lang="en"
      />
    )

    expect(screen.getByText('No activity yet')).toBeInTheDocument()
    expect(screen.getByText('Start your learning journey!')).toBeInTheDocument()
  })

  it('applies compact mode', () => {
    const { container } = render(
      <RecentActivity
        activities={mockActivities}
        compact={true}
      />
    )

    expect(container.querySelector('.overflow-hidden')).toBeInTheDocument()
  })
})
