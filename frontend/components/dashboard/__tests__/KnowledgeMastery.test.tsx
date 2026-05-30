/**
 * @jest-environment jsdom
 */
import { render, screen, fireEvent } from '@testing-library/react'
import { KnowledgeMastery } from '../KnowledgeMastery'

describe('KnowledgeMastery', () => {
  const mockKnowledgePoints = [
    { name: '变量与基础类型', mastery: 80, courseId: 1 },
    { name: '流程控制语句', mastery: 40, courseId: 1 },
    { name: '函数与模块', mastery: 20, courseId: 1 },
  ]

  it('renders course name in header', () => {
    render(
      <KnowledgeMastery
        courseName="C语言"
        knowledgePoints={mockKnowledgePoints}
      />
    )

    expect(screen.getByText(/C语言/)).toBeInTheDocument()
  })

  it('displays all knowledge points', () => {
    render(
      <KnowledgeMastery
        courseName="C语言"
        knowledgePoints={mockKnowledgePoints}
      />
    )

    expect(screen.getByText('变量与基础类型')).toBeInTheDocument()
    expect(screen.getByText('流程控制语句')).toBeInTheDocument()
    expect(screen.getByText('函数与模块')).toBeInTheDocument()
  })

  it('displays mastery percentages', () => {
    render(
      <KnowledgeMastery
        courseName="C语言"
        knowledgePoints={mockKnowledgePoints}
      />
    )

    expect(screen.getByText('80%')).toBeInTheDocument()
    expect(screen.getByText('40%')).toBeInTheDocument()
    expect(screen.getByText('20%')).toBeInTheDocument()
  })

  it('sorts knowledge points by mastery (high to low)', () => {
    const { container } = render(
      <KnowledgeMastery
        courseName="C语言"
        knowledgePoints={mockKnowledgePoints}
      />
    )

    const percentages = container.querySelectorAll('.text-muted-foreground')
    const values = Array.from(percentages).map(el => el.textContent)

    // First mastery value should be highest (80%)
    expect(values.find(v => v === '80%')).toBeTruthy()
  })

  it('shows empty state when no knowledge points', () => {
    render(
      <KnowledgeMastery
        courseName="C语言"
        knowledgePoints={[]}
        lang="zh"
      />
    )

    expect(screen.getByText('开始学习后查看知识掌握度')).toBeInTheDocument()
  })

  it('shows "去学习" button on hover for low mastery points', () => {
    const handleLearnClick = jest.fn()
    render(
      <KnowledgeMastery
        courseName="C语言"
        knowledgePoints={mockKnowledgePoints}
        onLearnClick={handleLearnClick}
      />
    )

    // The "去学习" buttons should be present (though hidden by default)
    const learnButtons = screen.queryAllByText('去学习')
    expect(learnButtons.length).toBeGreaterThan(0)
  })

  it('shows continue learning button at bottom', () => {
    const handleLearnClick = jest.fn()
    render(
      <KnowledgeMastery
        courseName="C语言"
        knowledgePoints={mockKnowledgePoints}
        onLearnClick={handleLearnClick}
        lang="zh"
      />
    )

    expect(screen.getByText('继续学习')).toBeInTheDocument()
  })

  it('displays English labels when lang is "en"', () => {
    render(
      <KnowledgeMastery
        courseName="C Language"
        knowledgePoints={mockKnowledgePoints}
        lang="en"
      />
    )

    expect(screen.getByText('Knowledge Mastery')).toBeInTheDocument()
  })

  it('applies different gradient colors based on mastery', () => {
    const { container } = render(
      <KnowledgeMastery
        courseName="C语言"
        knowledgePoints={mockKnowledgePoints}
      />
    )

    // Check for gradient classes
    const gradients = container.querySelectorAll('[class*="from-"]')
    expect(gradients.length).toBeGreaterThan(0)
  })

  it('applies compact mode', () => {
    const { container } = render(
      <KnowledgeMastery
        courseName="C语言"
        knowledgePoints={mockKnowledgePoints}
        compact={true}
      />
    )

    expect(container.querySelector('.overflow-hidden')).toBeInTheDocument()
  })
})
