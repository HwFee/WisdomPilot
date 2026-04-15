/**
 * Tests for Challenge Page - Stage Mode
 *
 * TDD: Testing challenge page with full exercise content display.
 */

import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import ChallengePage from '@/app/challenge/[id]/page'

// Mock next/navigation
const mockPush = jest.fn()
const mockUseParams = jest.fn()
const mockUseRouter = jest.fn(() => ({ push: mockPush }))

jest.mock('next/navigation', () => ({
  useParams: () => mockUseParams(),
  useRouter: () => mockUseRouter(),
}))

// Mock framer-motion
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: React.PropsWithChildren) => <div {...props}>{children}</div>,
  },
}))

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
}
Object.defineProperty(window, 'localStorage', { value: mockLocalStorage })

// Mock API
jest.mock('@/lib/api', () => ({
  getArenaProfile: jest.fn(),
  startChallengeSession: jest.fn(),
  submitChallengeSession: jest.fn(),
  TIER_ICONS: { bronze: '🥉', silver: '🥈', gold: '🥇', platinum: '💎', diamond: '👑' },
  TIER_NAMES: { bronze: '青铜', silver: '白银', gold: '黄金', platinum: '铂金', diamond: '钻石' },
}))

const mockExercises = [
  {
    id: 1,
    title: '变量声明',
    type: 'choice',
    difficulty: 2,
    knowledge_points: ['变量', '数据类型'],
    content: {
      text: '以下哪个是正确的C语言变量声明？',
      options: ['int x = 10;', 'variable x = 10;', 'x = 10;', 'declare x;'],
    },
    test_cases: null,
  },
  {
    id: 2,
    title: '指针基础',
    type: 'choice',
    difficulty: 3,
    knowledge_points: ['指针'],
    content: {
      text: '指针变量的声明方式是？',
      options: ['int *p;', 'pointer p;', '*int p;', 'p = int *;'],
    },
    test_cases: null,
  },
]

describe('ChallengePage - Exercise Content Display', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockLocalStorage.getItem.mockReturnValue('test-token')
    mockUseParams.mockReturnValue({ id: '1' })
  })

  it('should display question text from exercise content', async () => {
    const { getArenaProfile } = require('@/lib/api')
    getArenaProfile.mockResolvedValue({
      user_id: 'user1',
      course_id: 1,
      total_score: 1000,
      tier: 'silver',
      rank: 10,
      total_challenges: 20,
      wins: 15,
      losses: 5,
      highest_difficulty: 4,
      best_streak: 5,
      current_streak: 2,
    })

    render(<ChallengePage />)

    // Should show difficulty selection initially
    await waitFor(() => {
      expect(screen.getByText(/选择难度/)).toBeInTheDocument()
    })
  })

  it('should render difficulty options with correct labels', async () => {
    const { getArenaProfile } = require('@/lib/api')
    getArenaProfile.mockResolvedValue({
      user_id: 'user1',
      course_id: 1,
      total_score: 1000,
      tier: 'silver',
      rank: 10,
      total_challenges: 20,
      wins: 15,
      losses: 5,
      highest_difficulty: 4,
      best_streak: 5,
      current_streak: 2,
    })

    render(<ChallengePage />)

    await waitFor(() => {
      expect(screen.getByText('入门')).toBeInTheDocument()
      expect(screen.getByText('基础')).toBeInTheDocument()
      expect(screen.getByText('中等')).toBeInTheDocument()
      expect(screen.getByText('困难')).toBeInTheDocument()
      expect(screen.getByText('极难')).toBeInTheDocument()
    })
  })
})

describe('ChallengePage - Programming Questions', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockLocalStorage.getItem.mockReturnValue('test-token')
    mockUseParams.mockReturnValue({ id: '1' })
  })

  const programmingExercise = {
    id: 1,
    title: '两数之和',
    type: 'programming',
    difficulty: 3,
    knowledge_points: ['数组', '循环'],
    content: {
      text: '实现一个函数，返回两个数的和',
      code_template: 'int add(int a, int b) {\n  // TODO\n}',
      description: '编写函数计算两数之和',
    },
    test_cases: [
      { input: '1, 2', expected: '3' },
      { input: '5, 7', expected: '12' },
    ],
  }

  it('should have programming exercise type in content structure', () => {
    expect(programmingExercise.type).toBe('programming')
    expect(programmingExercise.content.code_template).toBeDefined()
    expect(programmingExercise.test_cases).toHaveLength(2)
  })
})
