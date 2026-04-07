const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface User {
  id: string
  email: string
  username: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

export interface ApiError {
  detail: string
}

export async function register(
  email: string,
  username: string,
  password: string
): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, username, password }),
  })

  const data = await response.json()

  if (!response.ok) {
    throw new Error((data as ApiError).detail || 'Registration failed')
  }

  // Store token in localStorage
  localStorage.setItem('token', (data as AuthResponse).access_token)
  localStorage.setItem('user', JSON.stringify((data as AuthResponse).user))

  return data as AuthResponse
}

export async function login(email: string, password: string): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  })

  const data = await response.json()

  if (!response.ok) {
    throw new Error((data as ApiError).detail || 'Login failed')
  }

  // Store token in localStorage
  localStorage.setItem('token', (data as AuthResponse).access_token)
  localStorage.setItem('user', JSON.stringify((data as AuthResponse).user))

  return data as AuthResponse
}

export async function getCurrentUser(token: string): Promise<User> {
  const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  const data = await response.json()

  if (!response.ok) {
    throw new Error((data as ApiError).detail || 'Failed to get user')
  }

  return data as User
}

export function logout(): void {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
}

export function getStoredUser(): User | null {
  const userStr = localStorage.getItem('user')
  if (!userStr) return null
  try {
    return JSON.parse(userStr) as User
  } catch {
    return null
  }
}

export function getStoredToken(): string | null {
  return localStorage.getItem('token')
}

export function isAuthenticated(): boolean {
  return !!getStoredToken()
}

export async function forgotPassword(email: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/auth/forgot-password`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email }),
  })

  if (!response.ok) {
    const data = await response.json()
    throw new Error((data as ApiError).detail || 'Failed to send reset email')
  }
}

// ========================================
// Learning Statistics Types
// ========================================

export interface ChapterProgress {
  id: string
  user_id: string
  chapter_id: number
  status: 'not_started' | 'in_progress' | 'completed'
  progress_percent: number
  completed_subsections: number[]
  completed_exercise_count: number
  completed_exercises_by_subsection: Record<number, number[]>  // {小节索引: [已完成习题ID列表]}
  exercise_results: Record<string, string>  // {exerciseKey: "correct" | "wrong"}
  started_at: string | null
  completed_at: string | null
  updated_at: string
}

export interface ExerciseAnswer {
  subsection_index: number
  exercise_id: number
  correct_answer_index: number
}

export interface ChapterExerciseAnswers {
  chapter_id: number
  answers: ExerciseAnswer[]
}

export interface LearningSession {
  id: string
  user_id: string
  chapter_id: number
  subsection_index: number
  started_at: string
  ended_at: string | null
  duration_seconds: number
  is_active: boolean
}

export interface LearningStatistics {
  total_learning_time_seconds: number
  total_sessions: number
  completed_chapters: number
  in_progress_chapters: number
  total_subsections_completed: number
  current_streak: number
  longest_streak: number
}

export interface Activity {
  id: string
  activity_type: string
  chapter_id: number | null
  subsection_index: number | null
  description: string
  extra_data: Record<string, unknown>
  created_at: string
}

export interface UpdateProgressData {
  status?: string
  progress_percent?: number
  completed_subsections?: number[]
  completed_exercise_count?: number
  total_exercises?: number
  completed_exercises_by_subsection?: Record<number, number[]>  // {小节索引: [已完成习题ID列表]}
  exercise_results?: Record<string, string>  // {exerciseKey: "correct" | "wrong"}
}

// ========================================
// Learning Statistics API Functions
// ========================================

async function fetchWithAuth(url: string, token: string, options: RequestInit = {}): Promise<Response> {
  const response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    const data = await response.json()
    throw new Error((data as ApiError).detail || 'API request failed')
  }

  return response
}

export async function getUserProgress(token: string): Promise<ChapterProgress[]> {
  const response = await fetchWithAuth(`${API_BASE_URL}/api/stats/progress`, token)
  return response.json()
}

export async function getChapterProgress(token: string, chapterId: number): Promise<ChapterProgress> {
  const response = await fetchWithAuth(`${API_BASE_URL}/api/stats/progress/${chapterId}`, token)
  return response.json()
}

export async function updateChapterProgress(
  token: string,
  chapterId: number,
  data: UpdateProgressData
): Promise<ChapterProgress> {
  const response = await fetchWithAuth(`${API_BASE_URL}/api/stats/progress/${chapterId}`, token, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
  return response.json()
}

export async function startLearningSession(
  token: string,
  chapterId: number,
  subsectionIndex: number = 0
): Promise<LearningSession> {
  const response = await fetchWithAuth(`${API_BASE_URL}/api/stats/sessions/start`, token, {
    method: 'POST',
    body: JSON.stringify({ chapter_id: chapterId, subsection_index: subsectionIndex }),
  })
  return response.json()
}

export async function endLearningSession(
  token: string,
  durationSeconds: number
): Promise<LearningSession> {
  const response = await fetchWithAuth(`${API_BASE_URL}/api/stats/sessions/end`, token, {
    method: 'POST',
    body: JSON.stringify({ duration_seconds: durationSeconds }),
  })
  return response.json()
}

export async function getActiveSession(token: string): Promise<LearningSession | null> {
  const response = await fetchWithAuth(`${API_BASE_URL}/api/stats/sessions/active`, token)
  return response.json()
}

export async function updateSessionSubsection(
  token: string,
  subsectionIndex: number
): Promise<LearningSession> {
  const response = await fetchWithAuth(`${API_BASE_URL}/api/stats/sessions/subsection`, token, {
    method: 'POST',
    body: JSON.stringify({ subsection_index: subsectionIndex }),
  })
  return response.json()
}

export async function getLearningSessions(token: string, limit: number = 50): Promise<LearningSession[]> {
  const response = await fetchWithAuth(`${API_BASE_URL}/api/stats/sessions?limit=${limit}`, token)
  return response.json()
}

export async function getLearningStatistics(token: string): Promise<LearningStatistics> {
  const response = await fetchWithAuth(`${API_BASE_URL}/api/stats/statistics`, token)
  return response.json()
}

export async function getActivityHistory(token: string, limit: number = 20): Promise<Activity[]> {
  const response = await fetchWithAuth(`${API_BASE_URL}/api/stats/activities?limit=${limit}`, token)
  return response.json()
}

export async function getChapterExerciseAnswers(token: string, chapterId: number): Promise<ChapterExerciseAnswers> {
  const response = await fetchWithAuth(`${API_BASE_URL}/api/stats/exercises/answers/${chapterId}`, token)
  return response.json()
}
