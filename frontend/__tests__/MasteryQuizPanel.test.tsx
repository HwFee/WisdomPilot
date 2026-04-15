/**
 * Tests for Mastery Quiz Panel Component
 *
 * TDD: Testing the quiz panel for mastery path.
 */

import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import { MasteryQuizPanel } from '@/components/mastery/MasteryQuizPanel'
import type { MasteryQuizQuestion } from '@/types/api'

// Mock framer-motion
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: React.PropsWithChildren) => <div {...props}>{children}</div>,
    button: ({ children, ...props }: React.PropsWithChildren) => <button {...props}>{children}</button>,
  },
  AnimatePresence: ({ children }: React.PropsWithChildren) => <>{children}</>,
}))

const mockQuestions: MasteryQuizQuestion[] = [
  {
    id: 'q_001',
    type: 'choice',
    difficulty: 2,
    content: {
      text: '以下哪个是正确的C语言变量声明？',
      options: ['int x = 10;', 'variable x = 10;', 'x = 10;', 'declare x as int'],
    },
    solution: { answer: 'A', explanation: '在C语言中，变量声明需要指定类型' },
    knowledge_points: ['变量声明', '数据类型'],
  },
  {
    id: 'q_002',
    type: 'choice',
    difficulty: 1,
    content: {
      text: 'C语言中，用于输出的函数是？',
      options: ['printf', 'print', 'output', 'display'],
    },
    solution: { answer: 'A', explanation: 'printf是C语言标准输出函数' },
    knowledge_points: ['输入输出'],
  },
]

describe('MasteryQuizPanel', () => {
  const mockOnSubmit = jest.fn()
  const mockOnClose = jest.fn()
  const mockOnOpenEditor = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should render quiz title and progress', () => {
    render(
      <MasteryQuizPanel
        questions={mockQuestions}
        onSubmit={mockOnSubmit}
        onClose={mockOnClose}
        onOpenEditor={mockOnOpenEditor}
      />
    )

    expect(screen.getByText(/精进之路测试/)).toBeInTheDocument()
    expect(screen.getByText(/1 \/ 2/)).toBeInTheDocument()
  })

  it('should render question content', () => {
    render(
      <MasteryQuizPanel
        questions={mockQuestions}
        onSubmit={mockOnSubmit}
        onClose={mockOnClose}
        onOpenEditor={mockOnOpenEditor}
      />
    )

    expect(screen.getByText(/以下哪个是正确的C语言变量声明/)).toBeInTheDocument()
  })

  it('should render options for choice questions', () => {
    render(
      <MasteryQuizPanel
        questions={mockQuestions}
        onSubmit={mockOnSubmit}
        onClose={mockOnClose}
        onOpenEditor={mockOnOpenEditor}
      />
    )

    expect(screen.getByText('A. int x = 10;')).toBeInTheDocument()
    expect(screen.getByText('B. variable x = 10;')).toBeInTheDocument()
    expect(screen.getByText('C. x = 10;')).toBeInTheDocument()
    expect(screen.getByText('D. declare x as int')).toBeInTheDocument()
  })

  it('should allow selecting an option', () => {
    render(
      <MasteryQuizPanel
        questions={mockQuestions}
        onSubmit={mockOnSubmit}
        onClose={mockOnClose}
        onOpenEditor={mockOnOpenEditor}
      />
    )

    const optionA = screen.getByText('A. int x = 10;').closest('button')
    if (optionA) {
      fireEvent.click(optionA)
    }

    // Should show selected state
    expect(optionA).toHaveClass('ring-2')
  })

  it('should navigate to next question', async () => {
    render(
      <MasteryQuizPanel
        questions={mockQuestions}
        onSubmit={mockOnSubmit}
        onClose={mockOnClose}
        onOpenEditor={mockOnOpenEditor}
      />
    )

    // Select an option
    const optionA = screen.getByText('A. int x = 10;').closest('button')
    if (optionA) {
      fireEvent.click(optionA)
    }

    // Click next
    const nextButton = screen.getByRole('button', { name: /下一题/ })
    fireEvent.click(nextButton)

    // Should show second question
    await waitFor(() => {
      expect(screen.getByText(/C语言中，用于输出的函数是/)).toBeInTheDocument()
    })
  })

  it('should call onSubmit after answering all questions', async () => {
    render(
      <MasteryQuizPanel
        questions={mockQuestions}
        onSubmit={mockOnSubmit}
        onClose={mockOnClose}
        onOpenEditor={mockOnOpenEditor}
      />
    )

    // Answer first question
    const optionA = screen.getByText('A. int x = 10;').closest('button')
    if (optionA) {
      fireEvent.click(optionA)
    }
    fireEvent.click(screen.getByRole('button', { name: /下一题/ }))

    // Answer second question
    await waitFor(() => {
      const optionA2 = screen.getByText('A. printf').closest('button')
      if (optionA2) {
        fireEvent.click(optionA2)
      }
    })

    // Submit
    await waitFor(() => {
      const submitButton = screen.getByRole('button', { name: /提交/ })
      fireEvent.click(submitButton)
    })

    expect(mockOnSubmit).toHaveBeenCalled()
  })

  it('should show difficulty badge', () => {
    render(
      <MasteryQuizPanel
        questions={mockQuestions}
        onSubmit={mockOnSubmit}
        onClose={mockOnClose}
        onOpenEditor={mockOnOpenEditor}
      />
    )

    expect(screen.getByText('基础')).toBeInTheDocument()
  })

  it('should disable next button until option is selected', () => {
    render(
      <MasteryQuizPanel
        questions={mockQuestions}
        onSubmit={mockOnSubmit}
        onClose={mockOnClose}
        onOpenEditor={mockOnOpenEditor}
      />
    )

    const nextButton = screen.getByRole('button', { name: /下一题/ })
    expect(nextButton).toBeDisabled()
  })
})

describe('MasteryQuizPanel - Programming Questions', () => {
  const mockOnSubmit = jest.fn()
  const mockOnClose = jest.fn()
  const mockOnOpenEditor = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  const programmingQuestion: MasteryQuizQuestion = {
    id: 'q_prog_001',
    type: 'programming',
    difficulty: 3,
    content: {
      text: '实现一个函数，计算两个数的和',
      code_template: 'int add(int a, int b) {\n  // TODO: implement\n}',
      test_cases: [
        { input: '1, 2', expected: '3' },
        { input: '5, 7', expected: '12' },
      ],
    },
    solution: { answer: 'return a + b;', explanation: '直接返回两数之和' },
    knowledge_points: ['函数', '运算'],
  }

  it('should render code template for programming questions', () => {
    render(
      <MasteryQuizPanel
        questions={[programmingQuestion]}
        onSubmit={mockOnSubmit}
        onClose={mockOnClose}
        onOpenEditor={mockOnOpenEditor}
      />
    )

    expect(screen.getByText(/int add\(int a, int b\)/)).toBeInTheDocument()
  })

  it('should render test cases for programming questions', () => {
    render(
      <MasteryQuizPanel
        questions={[programmingQuestion]}
        onSubmit={mockOnSubmit}
        onClose={mockOnClose}
        onOpenEditor={mockOnOpenEditor}
      />
    )

    expect(screen.getByText(/测试用例/)).toBeInTheDocument()
    // Multiple test cases have "输入:" label
    expect(screen.getAllByText(/输入:/)).toHaveLength(2)
    expect(screen.getByText('1, 2')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
    expect(screen.getByText('5, 7')).toBeInTheDocument()
    expect(screen.getByText('12')).toBeInTheDocument()
  })

  it('should call onOpenEditor when open editor button is clicked', () => {
    render(
      <MasteryQuizPanel
        questions={[programmingQuestion]}
        onSubmit={mockOnSubmit}
        onClose={mockOnClose}
        onOpenEditor={mockOnOpenEditor}
      />
    )

    const openEditorButton = screen.getByRole('button', { name: /打开编辑器/ })
    fireEvent.click(openEditorButton)

    expect(mockOnOpenEditor).toHaveBeenCalledWith(
      'int add(int a, int b) {\n  // TODO: implement\n}',
      '实现一个函数，计算两个数的和'
    )
  })
})
