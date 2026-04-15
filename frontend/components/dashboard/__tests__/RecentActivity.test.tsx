/**
 * @jest-environment jsdom
 */
import { render, screen, fireEvent } from '@testing-library/react'
import { RecentActivity } from '../RecentActivity'

describe('RecentActivity', () => {
  const mockActivities = [
    { id: '1', type: 'exercise_complete', description: '完成了循环练习', created_at: new Date(Date.now() - 10 * 60000).toISOString() },
    { id: '2', type: 'chapter_complete', description: '完成了第3章', created_at: new Date(Date.now() - 60 * 60000).toISOString() },
    { id: '3', type: 'achievement_earned', description: '获得了"坚持学习"成就', created_at: new Date(Date.now() - 120 * 60000).toISOString() },
  ]

  it('renders activity items', () => {
    render(<RecentActivity activities={mockActivities} />)

    expect(screen.getByText('完成了循环练习')).toBeInTheDocument()
    expect(screen.getByText('完成了第3章')).toBeInTheDocument()
    expect(screen.getByText('获得了"坚持学习"成就')).toBeInTheDocument()
  })

  it('displays formatted timestamps', () => {
    render(<RecentActivity activities={mockActivities} />)

    // Check for time format exists (component formats ISO dates)
    expect(screen.getByText(/分钟前|mins ago/)).toBeInTheDocument()
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
    const activitiesWithDetails = [
      {
        id: '1',
        type: 'exercise_complete',
        description: '完成了练习',
        details: { is_correct: true }
      },
      {
        id: '2',
        type: 'exercise_complete',
        description: '完成了练习',
        details: { is_correct: false }
      },
      {
        id: '3',
        type: 'exercise_complete',
        description: '完成了练习',
        // No is_correct field
      },
      {
        id: '4',
        type: 'chapter_complete',
        description: '完成了第3章',
      },
      {
        id: '5',
        type: 'achievement_earned',
        description: '获得了成就',
      },
    ]
    const { container } = render(<RecentActivity activities={activitiesWithDetails} />)

    // Check for emoji icons based on details
    expect(container.textContent).toContain('✅') // is_correct: true
    expect(container.textContent).toContain('❌') // is_correct: false
    expect(container.textContent).toContain('📝') // no is_correct field
    expect(container.textContent).toContain('📚') // chapter_complete
    expect(container.textContent).toContain('🏆') // achievement_earned
  })

  it('limits activities to 8 by default', () => {
    const manyActivities = Array.from({ length: 10 }, (_, i) => ({
      id: `${i}`,
      type: 'exercise_complete',
      description: `Activity ${i}`,
      created_at: `${i}分钟前`,
    }))

    render(<RecentActivity activities={manyActivities} />)

    // Should show 8 activities (0-7)
    expect(screen.getByText('Activity 0')).toBeInTheDocument()
    expect(screen.getByText('Activity 7')).toBeInTheDocument()
    expect(screen.queryByText('Activity 8')).not.toBeInTheDocument()
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
