/**
 * API Module Index - Re-export all API functions
 */

// Auth
export {
  login,
  register,
  getCurrentUser,
  forgotPassword,
  logout,
  getStoredUser,
  getStoredToken,
  isAuthenticated,
  type User,
  type Token,
} from './auth'

// Courses
export {
  getCourses,
  getCourse,
  getCourseByCode,
  getChapter,
  getUserCourseProgress,
  getTodayStats,
  type CourseSummary,
  type CourseDetail,
  type ChapterDetail,
  type CourseProgress,
  type CourseProgressResponse,
  type TodayStatsResponse,
} from './courses'

// Exercises
export {
  getExercises,
  getExercise,
  generateExercises,
  submitExercise,
  verifyExercise,
  type ExerciseSummary,
  type ExerciseDetail,
  type ExerciseSubmitResponse,
} from './exercises'

// Challenges
export {
  getChallenges,
  getChallenge,
  startChallenge,
  getUserChallenges,
  type ChallengeSummary,
  type ChallengeDetail,
  type UserChallengeDetail,
} from './challenges'

// Achievements
export {
  getAchievements,
  getAchievementsWithEarned,
  getAchievement,
  getUserAchievements,
  getLeaderboard,
  getUserRank,
  type AchievementSummary,
  type AchievementDetail,
} from './achievements'

// Stats
export {
  getUserProgress,
  getChapterProgress,
  updateChapterProgress,
  startLearningSession,
  endLearningSession,
  getActiveSession,
  updateSessionSubsection,
  getLearningSessions,
  getLearningStatistics,
  getActivityHistory,
  getChapterExerciseAnswers,
  type ChapterProgress,
  type LearningSession,
  type LearningStatistics,
  type Activity,
  type UpdateProgressRequest,
  type ExerciseAnswer,
  type ChapterExerciseAnswers,
} from './stats'

// Profile
export {
  getProfile,
  updateProfile,
  addXp,
  checkin,
  getCheckinStatus,
  type UserProfileResponse,
  type UpdateProfileRequest,
  type CheckinResponse,
  type CheckinStatusResponse,
} from './profile'

// Stages
export {
  getStage,
  getCourseStages,
  startStage,
  completePractice,
  startVerification,
  submitVerification,
} from './stages'

// Review
export {
  getReviewQueue,
  completeReview,
  getWeakPoints,
  getTargetPractice,
  getReviewStats,
} from './review'

// AI
export {
  getChoiceExplanation,
  getCodeReview,
  aiChat,
  aiChatStream,
  analyzeChoice,
  getCodeFeedback,
  getAIConfig,
  updateAIConfig,
  getAIStatus,
  testAIConnection,
  type ChoiceExplanationRequest,
  type ChoiceExplanationResponse,
  type CodeReviewRequest,
  type CodeReviewResponse,
  type AIChatRequest,
  type AIChatResponse,
  type ChoiceAnalysisRequest,
  type ChoiceAnalysisResponse,
  type CodeFeedbackRequest,
  type CodeFeedbackResponse,
  type AIConfigResponse,
  type UpdateAIConfigRequest,
  type AIStatusResponse,
  type TestConnectionRequest,
  type TestConnectionResponse,
} from './ai'

// Code Execution
export {
  executeCode,
  getSupportedLanguages,
  type CodeExecutionRequest,
  type CodeExecutionResponse,
  type LanguageInfo,
} from './code'

// Trends
export {
  getExercisesTrend,
  getAccuracyTrend,
  getTimeTrend,
  type DailyExercisesTrendResponse,
  type DailyAccuracyTrendResponse,
  type DailyTimeTrendResponse,
} from './trends'

// Favorites
export {
  addFavorite,
  getFavorites,
  getFavoritesCount,
  removeFavorite,
  type FavoriteCreate,
  type FavoriteResponse,
  type FavoriteListResponse,
  type FavoriteCountResponse,
} from './favorites'

// Notes
export {
  createNote,
  getNotes,
  getNotesCount,
  updateNote,
  deleteNote,
  type NoteCreate,
  type NoteUpdate,
  type NoteResponse,
  type NoteListResponse,
  type NoteCountResponse,
} from './notes'

// Client utilities
export { fetchWithAuth, get, post, put, del, API_BASE_URL } from './client'

// Vector Match
export {
  getExerciseRecommendations,
  type ExerciseRecommendItem,
  type ExerciseRecommendRequest,
  type ExerciseRecommendResponse,
} from './vector'

// Learning Path
export {
  getMasteryOverview,
  getChapterMastery,
  getMasteryExerciseRecommendations,
  getArenaProfile,
  startChallengeSession,
  submitChallengeSession,
  getMasteryLeaderboard,
  getArenaLeaderboard,
  TIER_THRESHOLDS,
  TIER_ICONS,
  TIER_NAMES,
  MASTERY_LEVEL_COLORS,
} from './learning-path'
