/**
 * Tests for check-in API functions
 */

import { checkin, getCheckinStatus, CheckinResponse, CheckinStatusResponse } from '@/lib/api/profile'

// Mock fetch
global.fetch = jest.fn()

const mockToken = 'test-token'
const DEFAULT_API_BASE_URL = 'http://127.0.0.1:8000'

describe('Checkin API Functions', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('checkin', () => {
    it('calls checkin endpoint successfully', async () => {
      const mockResponse: CheckinResponse = {
        streak_days: 5,
        checked_in_today: true,
        xp_earned: 10,
        last_checkin_date: '2024-01-15T10:30:00Z',
        total_checkin_days: 15,
        streak_multiplier: 1.0,
        new_achievements: [],
      }

      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      })

      const result = await checkin(mockToken)
      expect(result).toEqual(mockResponse)
      expect(fetch).toHaveBeenCalledWith(
        `${DEFAULT_API_BASE_URL}/api/users/checkin`,
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            Authorization: `Bearer ${mockToken}`,
          }),
        })
      )
    })

    it('returns xp_earned as 0 for duplicate check-in', async () => {
      const mockResponse: CheckinResponse = {
        streak_days: 5,
        checked_in_today: true,
        xp_earned: 0,
        last_checkin_date: '2024-01-15T10:30:00Z',
        total_checkin_days: 15,
        streak_multiplier: 1.0,
        new_achievements: [],
      }

      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      })

      const result = await checkin(mockToken)
      expect(result.xp_earned).toBe(0)
      expect(result.streak_days).toBe(5)
    })

    it('throws error on API failure', async () => {
      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 403,
        statusText: 'Forbidden',
        text: () => Promise.resolve(JSON.stringify({ detail: 'Unauthorized' })),
      })

      await expect(checkin(mockToken)).rejects.toThrow('Unauthorized')
    })
  })

  describe('getCheckinStatus', () => {
    it('fetches check-in status successfully', async () => {
      const mockResponse: CheckinStatusResponse = {
        streak_days: 7,
        checked_in_today: false,
        last_checkin_date: '2024-01-14T08:00:00Z',
        total_checkin_days: 20,
      }

      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      })

      const result = await getCheckinStatus(mockToken)
      expect(result).toEqual(mockResponse)
      expect(result.streak_days).toBe(7)
      expect(result.checked_in_today).toBe(false)
    })

    it('throws error on API failure', async () => {
      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 403,
        statusText: 'Forbidden',
        text: () => Promise.resolve(JSON.stringify({ detail: 'Token expired' })),
      })

      await expect(getCheckinStatus(mockToken)).rejects.toThrow('Token expired')
    })
  })
})
