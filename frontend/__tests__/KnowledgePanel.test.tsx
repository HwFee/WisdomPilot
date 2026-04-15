/**
 * Tests for Knowledge Panel Component
 *
 * TDD: Testing the knowledge content display for mastery path.
 */

import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import { KnowledgePanel } from '@/components/mastery/KnowledgePanel'
import type { KnowledgeContentResponse } from '@/types/api'

// Mock framer-motion
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: React.PropsWithChildren) => <div {...props}>{children}</div>,
    button: ({ children, ...props }: React.PropsWithChildren) => <button {...props}>{children}</button>,
  },
  AnimatePresence: ({ children }: React.PropsWithChildren) => <>{children}</>,
}))

const mockKnowledgeContent: KnowledgeContentResponse = {
  chapter_id: 1,
  chapter_title: 'C语言基础',
  knowledge_points: [
    {
      id: 'kp_001',
      title: '变量与数据类型',
      content: '变量是存储数据的容器。在C语言中，每个变量都有特定的数据类型。',
      examples: ['int x = 10;', 'float pi = 3.14;'],
      difficulty: 1,
      related_points: [],
    },
    {
      id: 'kp_002',
      title: '运算符',
      content: '运算符用于执行各种运算操作。',
      examples: ['int sum = a + b;', 'int product = a * b;'],
      difficulty: 1,
      related_points: ['kp_001'],
    },
  ],
  total_points: 2,
  estimated_time: 15,
  prerequisites: null,
  next_chapters: null,
}

describe('KnowledgePanel', () => {
  const mockOnStartQuiz = jest.fn()
  const mockOnClose = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should render chapter title', () => {
    render(
      <KnowledgePanel
        content={mockKnowledgeContent}
        onStartQuiz={mockOnStartQuiz}
        onClose={mockOnClose}
      />
    )

    expect(screen.getByText('C语言基础')).toBeInTheDocument()
    expect(screen.getByText(/知识点讲解/)).toBeInTheDocument()
  })

  it('should render all knowledge points', () => {
    render(
      <KnowledgePanel
        content={mockKnowledgeContent}
        onStartQuiz={mockOnStartQuiz}
        onClose={mockOnClose}
      />
    )

    expect(screen.getByText('变量与数据类型')).toBeInTheDocument()
    expect(screen.getByText('运算符')).toBeInTheDocument()
    // First knowledge point is expanded by default
    expect(screen.getByText(/变量是存储数据的容器/)).toBeInTheDocument()
  })

  it('should show code examples', async () => {
    render(
      <KnowledgePanel
        content={mockKnowledgeContent}
        onStartQuiz={mockOnStartQuiz}
        onClose={mockOnClose}
      />
    )

    // First knowledge point is expanded by default, so its examples should be visible
    expect(screen.getByText('int x = 10;')).toBeInTheDocument()
    expect(screen.getByText('float pi = 3.14;')).toBeInTheDocument()
  })

  it('should show estimated time', () => {
    render(
      <KnowledgePanel
        content={mockKnowledgeContent}
        onStartQuiz={mockOnStartQuiz}
        onClose={mockOnClose}
      />
    )

    expect(screen.getByText(/预计学习时间/)).toBeInTheDocument()
    expect(screen.getByText(/15/)).toBeInTheDocument()
  })

  it('should call onStartQuiz when start quiz button is clicked', () => {
    render(
      <KnowledgePanel
        content={mockKnowledgeContent}
        onStartQuiz={mockOnStartQuiz}
        onClose={mockOnClose}
      />
    )

    const startButton = screen.getByRole('button', { name: /开始测试/ })
    fireEvent.click(startButton)

    expect(mockOnStartQuiz).toHaveBeenCalledTimes(1)
  })

  it('should call onClose when close button is clicked', () => {
    render(
      <KnowledgePanel
        content={mockKnowledgeContent}
        onStartQuiz={mockOnStartQuiz}
        onClose={mockOnClose}
      />
    )

    const closeButton = screen.getByRole('button', { name: /关闭/ })
    fireEvent.click(closeButton)

    expect(mockOnClose).toHaveBeenCalledTimes(1)
  })

  it('should show loading state', () => {
    render(
      <KnowledgePanel
        content={null}
        isLoading={true}
        onStartQuiz={mockOnStartQuiz}
        onClose={mockOnClose}
      />
    )

    expect(screen.getByText(/加载中/)).toBeInTheDocument()
  })

  it('should expand knowledge point on click', async () => {
    render(
      <KnowledgePanel
        content={mockKnowledgeContent}
        onStartQuiz={mockOnStartQuiz}
        onClose={mockOnClose}
      />
    )

    // First knowledge point is already expanded by default
    expect(screen.getByText(/变量是存储数据的容器/)).toBeInTheDocument()

    // Click on second knowledge point to expand it
    const operatorButton = screen.getByText('运算符').closest('button')
    if (operatorButton) {
      fireEvent.click(operatorButton)
    }

    // Now second knowledge point content should be visible
    await waitFor(() => {
      expect(screen.getByText(/运算符用于执行各种运算操作/)).toBeInTheDocument()
    })
  })
})
