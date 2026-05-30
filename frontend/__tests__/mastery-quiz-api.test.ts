/**
 * Tests for Mastery Quiz API Client
 *
 * TDD: Testing the mastery quiz API functions.
 */

import {
  getChapterKnowledgeContent,
  generateMasteryQuiz,
  submitMasteryQuiz,
} from '@/lib/api/learning-path'
import * as client from '@/lib/api/client'

// Mock the client module
jest.mock('@/lib/api/client', () => ({
  get: jest.fn(),
  post: jest.fn(),
}))

const mockGet = client.get as jest.MockedFunction<typeof client.get>
const mockPost = client.post as jest.MockedFunction<typeof client.post>

const mockToken = 'test-token-123'

describe('Mastery Quiz API', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('getChapterKnowledgeContent', () => {
    it('should call GET with correct endpoint', async () => {
      const mockResponse = {
        chapter_id: 1,
        chapter_title: 'C语言基础',
        knowledge_points: [
          {
            id: 'kp_001',
            title: '变量与数据类型',
            content: '变量是存储数据的容器...',
            examples: ['int x = 10;'],
            difficulty: 1,
            related_points: [],
          },
        ],
        total_points: 1,
        estimated_time: 15,
        prerequisites: null,
        next_chapters: null,
      }

      mockGet.mockResolvedValueOnce(mockResponse)

      const result = await getChapterKnowledgeContent(1, 1, mockToken)

      expect(mockGet).toHaveBeenCalledWith(
        '/api/learning-path/mastery/1/chapter/1/knowledge',
        mockToken
      )
      expect(result).toEqual(mockResponse)
      expect(result.chapter_title).toBe('C语言基础')
      expect(result.knowledge_points).toHaveLength(1)
    })

    it('should handle chapter not found', async () => {
      mockGet.mockRejectedValueOnce(new Error('章节不存在'))

      await expect(getChapterKnowledgeContent(1, 999, mockToken)).rejects.toThrow('章节不存在')
    })
  })

  describe('generateMasteryQuiz', () => {
    it('should call POST with correct endpoint and request body', async () => {
      const mockRequest = {
        course_id: 1,
        chapter_id: 1,
        question_count: 5,
        question_types: ['choice'],
      }

      const mockResponse = {
        success: true,
        session_id: 'session-123',
        questions: [
          {
            id: 'q_001',
            type: 'choice' as const,
            difficulty: 2,
            content: {
              text: '测试题目',
              options: ['A', 'B', 'C', 'D'],
            },
            solution: { answer: 'A', explanation: '解析' },
            knowledge_points: ['变量'],
          },
        ],
        user_profile_used: true,
        weak_points_addressed: ['指针'],
        message: '成功生成 1 道测试题',
      }

      mockPost.mockResolvedValueOnce(mockResponse)

      const result = await generateMasteryQuiz(1, mockRequest, mockToken)

      expect(mockPost).toHaveBeenCalledWith(
        '/api/learning-path/mastery/1/generate-quiz',
        mockToken,
        mockRequest
      )
      expect(result.success).toBe(true)
      expect(result.session_id).toBe('session-123')
      expect(result.questions).toHaveLength(1)
    })

    it('should handle generation failure', async () => {
      const mockRequest = {
        course_id: 1,
        chapter_id: 999,
      }

      const mockResponse = {
        success: false,
        session_id: '',
        questions: [],
        user_profile_used: false,
        weak_points_addressed: [],
        message: '未找到章节',
      }

      mockPost.mockResolvedValueOnce(mockResponse)

      const result = await generateMasteryQuiz(1, mockRequest, mockToken)

      expect(result.success).toBe(false)
      expect(result.message).toBe('未找到章节')
    })
  })

  describe('submitMasteryQuiz', () => {
    it('should call POST with correct endpoint and answers', async () => {
      const mockRequest = {
        session_id: 'session-123',
        answers: [
          { question_id: 'q_001', answer: 'A', time_spent: 30 },
          { question_id: 'q_002', answer: 'B', time_spent: 45 },
        ],
        total_time: 75,
      }

      const mockResponse = {
        success: true,
        session_id: 'session-123',
        total_questions: 2,
        correct_answers: 2,
        accuracy: 1.0,
        xp_earned: 50,
        mastery_points_earned: 20,
        results: [
          { question_id: 'q_001', is_correct: true, user_answer: 'A', correct_answer: 'A', knowledge_points: ['变量'] },
          { question_id: 'q_002', is_correct: true, user_answer: 'B', correct_answer: 'B', knowledge_points: ['指针'] },
        ],
        recommendations: ['表现优秀！'],
        passed: true,
        message: '提交成功，恭喜通过！',
      }

      mockPost.mockResolvedValueOnce(mockResponse)

      const result = await submitMasteryQuiz(1, mockRequest, mockToken)

      expect(mockPost).toHaveBeenCalledWith(
        '/api/learning-path/mastery/1/submit-quiz',
        mockToken,
        mockRequest
      )
      expect(result.success).toBe(true)
      expect(result.accuracy).toBe(1.0)
      expect(result.passed).toBe(true)
    })

    it('should handle session not found', async () => {
      const mockRequest = {
        session_id: 'invalid-session',
        answers: [],
      }

      const mockResponse = {
        success: false,
        session_id: 'invalid-session',
        total_questions: 0,
        correct_answers: 0,
        accuracy: 0,
        xp_earned: 0,
        mastery_points_earned: 0,
        results: [],
        recommendations: [],
        passed: false,
        message: '会话不存在或已过期',
      }

      mockPost.mockResolvedValueOnce(mockResponse)

      const result = await submitMasteryQuiz(1, mockRequest, mockToken)

      expect(result.success).toBe(false)
      expect(result.message).toBe('会话不存在或已过期')
    })
  })
})
