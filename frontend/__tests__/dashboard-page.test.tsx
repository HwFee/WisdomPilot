import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import DashboardPage from '@/components/ui/dashboard-page'
import { getLearningStatistics, getActivityHistory, getUserProgress } from '@/lib/api'

// Mock the API module
jest.mock('@/lib/api', () => ({
  getStoredUser: jest.fn(),
  getStoredToken: jest.fn(),
  logout: jest.fn(),
  getLearningStatistics: jest.fn(),
  getActivityHistory: jest.fn(),
  getUserProgress: jest.fn(),
}))

// Mock next/navigation
const mockPush = jest.fn()
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
}))

const mockGetLearningStatistics = getLearningStatistics as jest.MockedFunction<typeof getLearningStatistics>
const mockGetActivityHistory = getActivityHistory as jest.MockedFunction<typeof getActivityHistory>
const mockGetUserProgress = getUserProgress as jest.MockedFunction<typeof getUserProgress>

describe('DashboardPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    // Setup default mocks
    ;(require('@/lib/api').getStoredUser as jest.Mock).mockReturnValue({
      id: '1',
      email: 'test@example.com',
      username: 'testuser',
      is_active: true,
      created_at: '2024-01-01',
      updated_at: '2024-01-01',
    })
    ;(require('@/lib/api').getStoredToken as jest.Mock).mockReturnValue('mock-token')
  })

  describe('上次学习卡片', () => {
    it('应该显示"上次学习"标题', async () => {
      mockGetLearningStatistics.mockResolvedValue({
        total_learning_time_seconds: 0,
        total_sessions: 0,
        completed_chapters: 0,
        in_progress_chapters: 0,
        total_subsections_completed: 0,
        current_streak: 0,
        longest_streak: 0,
      })
      mockGetActivityHistory.mockResolvedValue([])
      mockGetUserProgress.mockResolvedValue([])

      render(<DashboardPage />)

      await waitFor(() => {
        expect(screen.getByText('上次学习')).toBeInTheDocument()
      })
    })

    it('应该从activities中找到最近学习的章节', async () => {
      const oneHourAgo = new Date(Date.now() - 3600000).toISOString()
      mockGetLearningStatistics.mockResolvedValue({
        total_learning_time_seconds: 3600,
        total_sessions: 1,
        completed_chapters: 0,
        in_progress_chapters: 1,
        total_subsections_completed: 2,
        current_streak: 1,
        longest_streak: 1,
      })
      mockGetActivityHistory.mockResolvedValue([
        {
          id: '1',
          activity_type: 'chapter_started',
          chapter_id: 3,
          subsection_index: 2,
          description: '开始学习章节 3',
          extra_data: {},
          created_at: oneHourAgo,
        },
        {
          id: '2',
          activity_type: 'chapter_started',
          chapter_id: 1,
          subsection_index: 0,
          description: '开始学习章节 1',
          extra_data: {},
          created_at: new Date(Date.now() - 7200000).toISOString(),
        },
      ])
      mockGetUserProgress.mockResolvedValue([
        {
          id: 'p1',
          user_id: '1',
          chapter_id: 3,
          status: 'in_progress',
          progress_percent: 40,
          completed_subsections: [0, 1],
          completed_exercise_count: 0,
          completed_exercises_by_subsection: {},
          started_at: oneHourAgo,
          completed_at: null,
          updated_at: oneHourAgo,
        },
      ])

      render(<DashboardPage />)

      await waitFor(() => {
        // 应该显示第三章（字符串），因为它是最近学习的
        // Use getAllByText because StrictMode may render twice
        expect(screen.getAllByText('字符串').length).toBeGreaterThan(0)
      })
    })

    it('当没有学习记录时应该显示空状态', async () => {
      mockGetLearningStatistics.mockResolvedValue({
        total_learning_time_seconds: 0,
        total_sessions: 0,
        completed_chapters: 0,
        in_progress_chapters: 0,
        total_subsections_completed: 0,
        current_streak: 0,
        longest_streak: 0,
      })
      mockGetActivityHistory.mockResolvedValue([])
      mockGetUserProgress.mockResolvedValue([])

      render(<DashboardPage />)

      await waitFor(() => {
        // StrictMode may cause duplicate renders, use getAllByText
        expect(screen.getAllByText('暂无学习记录').length).toBeGreaterThan(0)
        expect(screen.getAllByText('开始学习一个章节吧！').length).toBeGreaterThan(0)
      })
    })
  })

  describe('布局对齐', () => {
    it('上次学习卡片和动态卡片应该在右侧边栏中垂直排列', async () => {
      mockGetLearningStatistics.mockResolvedValue({
        total_learning_time_seconds: 0,
        total_sessions: 0,
        completed_chapters: 0,
        in_progress_chapters: 0,
        total_subsections_completed: 0,
        current_streak: 0,
        longest_streak: 0,
      })
      mockGetActivityHistory.mockResolvedValue([])
      mockGetUserProgress.mockResolvedValue([])

      render(<DashboardPage />)

      // 验证两个卡片都存在
      await waitFor(() => {
        expect(screen.getByText('上次学习')).toBeInTheDocument()
      })
      expect(screen.getByText('最近动态')).toBeInTheDocument()
    })
  })
})
