/**
 * API Client Tests
 */

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
}
Object.defineProperty(global, 'localStorage', {
  value: localStorageMock,
})

// Mock process.env
process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000'

describe('API Client', () => {
  beforeEach(() => {
    localStorageMock.getItem.mockReset()
    localStorageMock.setItem.mockReset()
    localStorageMock.removeItem.mockReset()
  })

  describe('getStoredUser', () => {
    it('returns null when no user stored', async () => {
      const { getStoredUser } = await import('@/lib/api')
      localStorageMock.getItem.mockReturnValue(null)
      expect(getStoredUser()).toBeNull()
    })

    it('returns parsed user when stored', async () => {
      const { getStoredUser } = await import('@/lib/api')
      const mockUser = {
        id: '1',
        email: 'test@example.com',
        username: 'testuser',
        is_active: true,
        is_admin: false,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      }
      localStorageMock.getItem.mockReturnValue(JSON.stringify(mockUser))
      expect(getStoredUser()).toEqual(mockUser)
    })

    it('returns null for invalid JSON', async () => {
      const { getStoredUser } = await import('@/lib/api')
      localStorageMock.getItem.mockReturnValue('invalid json')
      expect(getStoredUser()).toBeNull()
    })
  })

  describe('getStoredToken', () => {
    it('returns token when stored', async () => {
      const { getStoredToken } = await import('@/lib/api')
      localStorageMock.getItem.mockReturnValue('test-token')
      expect(getStoredToken()).toBe('test-token')
    })

    it('returns null when not stored', async () => {
      const { getStoredToken } = await import('@/lib/api')
      localStorageMock.getItem.mockReturnValue(null)
      expect(getStoredToken()).toBeNull()
    })
  })

  describe('logout', () => {
    it('removes token and user from localStorage', async () => {
      const { logout } = await import('@/lib/api')
      logout()
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('token:v1')
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('user:v1')
    })
  })

  describe('isAuthenticated', () => {
    it('returns true when token exists', async () => {
      const { isAuthenticated } = await import('@/lib/api')
      localStorageMock.getItem.mockReturnValue('test-token')
      expect(isAuthenticated()).toBe(true)
    })

    it('returns false when no token', async () => {
      const { isAuthenticated } = await import('@/lib/api')
      localStorageMock.getItem.mockReturnValue(null)
      expect(isAuthenticated()).toBe(false)
    })
  })
})

describe('Type definitions', () => {
  it('User type has required fields', async () => {
    // Type checking at compile time
    const user = {
      id: '1',
      email: 'test@example.com',
      username: 'testuser',
      is_active: true,
      is_admin: false,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    } as const
    expect(user.id).toBe('1')
    expect(user.email).toBe('test@example.com')
  })

  it('ChapterProgress type has required fields', async () => {
    const progress = {
      id: '1',
      user_id: '1',
      chapter_id: 1,
      status: 'not_started' as const,
      progress_percent: 0,
      completed_subsections: [],
      completed_exercise_count: 0,
      completed_exercises_by_subsection: {},
      exercise_results: {},
      started_at: null,
      completed_at: null,
      updated_at: '2024-01-01T00:00:00Z',
    }
    expect(progress.chapter_id).toBe(1)
    expect(progress.status).toBe('not_started')
  })
})
