/**
 * Tests for learning statistics API functions
 */

import {
  getUserProgress,
  getChapterProgress,
  updateChapterProgress,
  startLearningSession,
  endLearningSession,
  getActiveSession,
  getLearningStatistics,
  getActivityHistory,
  ChapterProgress,
  LearningStatistics,
  Activity,
} from '@/lib/api'

// Mock fetch
global.fetch = jest.fn()

const mockToken = 'test-token'
const mockUserId = 'test-user-id'

describe('Stats API Functions', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('getUserProgress', () => {
    it('fetches user progress successfully', async () => {
      const mockProgress: ChapterProgress[] = [
        {
          id: '1',
          user_id: mockUserId,
          chapter_id: 1,
          status: 'in_progress',
          progress_percent: 50,
          completed_subsections: [0, 1, 2],
          started_at: '2024-01-01T00:00:00Z',
          completed_at: null,
          updated_at: '2024-01-01T00:00:00Z',
        },
      ]

      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockProgress),
      })

      const result = await getUserProgress(mockToken)
      expect(result).toEqual(mockProgress)
      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/stats/progress',
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: `Bearer ${mockToken}`,
          }),
        })
      )
    })

    it('throws error on API failure', async () => {
      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        json: () => Promise.resolve({ detail: 'Unauthorized' }),
      })

      await expect(getUserProgress(mockToken)).rejects.toThrow('Unauthorized')
    })
  })

  describe('updateChapterProgress', () => {
    it('updates chapter progress successfully', async () => {
      const mockProgress: ChapterProgress = {
        id: '1',
        user_id: mockUserId,
        chapter_id: 1,
        status: 'completed',
        progress_percent: 100,
        completed_subsections: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13],
        started_at: '2024-01-01T00:00:00Z',
        completed_at: '2024-01-02T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
      }

      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockProgress),
      })

      const result = await updateChapterProgress(mockToken, 1, {
        status: 'completed',
        progress_percent: 100,
        completed_subsections: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13],
      })

      expect(result.status).toBe('completed')
      expect(result.progress_percent).toBe(100)
    })
  })

  describe('startLearningSession', () => {
    it('starts a learning session', async () => {
      const mockSession = {
        id: 'session-1',
        user_id: mockUserId,
        chapter_id: 1,
        subsection_index: 0,
        started_at: '2024-01-01T00:00:00Z',
        ended_at: null,
        duration_seconds: 0,
        is_active: true,
      }

      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockSession),
      })

      const result = await startLearningSession(mockToken, 1, 0)
      expect(result.is_active).toBe(true)
      expect(result.chapter_id).toBe(1)
    })
  })

  describe('endLearningSession', () => {
    it('ends a learning session', async () => {
      const mockSession = {
        id: 'session-1',
        user_id: mockUserId,
        chapter_id: 1,
        subsection_index: 0,
        started_at: '2024-01-01T00:00:00Z',
        ended_at: '2024-01-01T01:00:00Z',
        duration_seconds: 3600,
        is_active: false,
      }

      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockSession),
      })

      const result = await endLearningSession(mockToken, 3600)
      expect(result.is_active).toBe(false)
      expect(result.duration_seconds).toBe(3600)
    })
  })

  describe('getLearningStatistics', () => {
    it('fetches learning statistics', async () => {
      const mockStats: LearningStatistics = {
        total_learning_time_seconds: 7200,
        total_sessions: 5,
        completed_chapters: 2,
        in_progress_chapters: 3,
        total_subsections_completed: 25,
        current_streak: 3,
        longest_streak: 7,
      }

      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockStats),
      })

      const result = await getLearningStatistics(mockToken)
      expect(result.completed_chapters).toBe(2)
      expect(result.total_learning_time_seconds).toBe(7200)
    })
  })

  describe('getActivityHistory', () => {
    it('fetches activity history', async () => {
      const mockActivities: Activity[] = [
        {
          id: '1',
          activity_type: 'chapter_started',
          chapter_id: 1,
          subsection_index: null,
          description: '开始学习章节 1',
          extra_data: {},
          created_at: '2024-01-01T00:00:00Z',
        },
        {
          id: '2',
          activity_type: 'session_ended',
          chapter_id: 1,
          subsection_index: null,
          description: '学习时长: 3600秒',
          extra_data: {},
          created_at: '2024-01-01T01:00:00Z',
        },
      ]

      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockActivities),
      })

      const result = await getActivityHistory(mockToken, 10)
      expect(result).toHaveLength(2)
      expect(result[0].activity_type).toBe('chapter_started')
    })
  })
})
