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
} from "./auth";

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
} from "./courses";

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
} from "./exercises";

// Challenges
export {
  getChallenges,
  getChallenge,
  startChallenge,
  getUserChallenges,
  type ChallengeSummary,
  type ChallengeDetail,
  type UserChallengeDetail,
} from "./challenges";

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
} from "./achievements";

// Stats
export {
  getUserProgress,
  getChapterProgress,
  updateChapterProgress,
  startLearningSession,
  startStageSession,
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
} from "./stats";

// Profile
export {
  getProfile,
  updateProfile,
  addXp,
  checkin,
  getCheckinStatus,
  getCheckinDetails,
  getCheckinStats,
  type UserProfileResponse,
  type UpdateProfileRequest,
  type CheckinResponse,
  type CheckinStatusResponse,
  type CheckinDetailsResponse,
  type CheckinStatsResponse,
} from "./profile";

// Review
export {
  getReviewQueue,
  completeReview,
  getWeakPoints,
  getTargetPractice,
  getReviewStats,
} from "./review";

// AI
export {
  getChoiceExplanation,
  getCodeReview,
  aiChat,
  aiChatStream,
  analyzeChoice,
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
  type AIConfigResponse,
  type UpdateAIConfigRequest,
  type AIStatusResponse,
  type TestConnectionRequest,
  type TestConnectionResponse,
} from "./ai";

// Code Execution
export {
  executeCode,
  getSupportedLanguages,
  type CodeExecutionRequest,
  type CodeExecutionResponse,
  type LanguageInfo,
} from "./code";

// Trends
export {
  getExercisesTrend,
  getAccuracyTrend,
  getTimeTrend,
  type DailyExercisesTrendResponse,
  type DailyAccuracyTrendResponse,
  type DailyTimeTrendResponse,
} from "./trends";

// Favorites
export {
  addFavorite,
  getFavorites,
  getFavoritesCount,
  getFavoriteFolders,
  updateFavorite,
  removeFavorite,
  batchRemoveFavorites,
  type FavoriteCreate,
  type FavoriteUpdate,
  type FavoriteResponse,
  type FavoriteListResponse,
  type FavoriteCountResponse,
  type FavoriteFoldersListResponse,
  type FavoriteCheckResponse,
  checkFavorite,
} from "./favorites";

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
} from "./notes";

// Client utilities
export {
  fetchWithAuth,
  get,
  post,
  put,
  del,
  postKeepalive,
  API_BASE_URL,
} from "./client";

// Vector Match
export {
  getExerciseRecommendations,
  type ExerciseRecommendItem,
  type ExerciseRecommendRequest,
  type ExerciseRecommendResponse,
} from "./vector";

// Learning Path
export {
  getMasteryOverview,
  getChapterMastery,
  getMasteryExerciseRecommendations,
  getMasteryLeaderboard,
  getArenaLeaderboard,
  getChapterKnowledgeContent,
  generateMasteryQuiz,
  submitMasteryQuiz,
  // Section Base Question APIs
  getSectionBaseQuestions,
  submitBaseAnswers,
  generateEnhancedQuiz,
  submitEnhancedQuiz,
  // Challenge Path APIs (independent of courses)
  startInfiniteSession,
  getChallengeProgress,
  submitChallengeExercise,
  saveChallengeCode,
  switchChallengeExercise,
  appendChallengeExercises,
  getChallengeExercise,
  // Recent Arena Exercises
  getRecentArenaExercises,
  // BKT Mastery APIs
  getSectionMastery,
  getCourseMastery,
  // Types
  type KnowledgePointMastery,
  type SectionMasteryResponse,
  type ChapterMasterySummary,
  type CourseMasteryResponse,
  // Constants
  TIER_THRESHOLDS,
  TIER_NAMES,
  MASTERY_LEVEL_COLORS,
} from "./learning-path";

// Tier
export {
  getTierConfigs,
  getTierInfo,
  getGlobalTierInfo,
  updateStars,
  TIER_COLORS,
} from "./tier";

// Core (智核)
export {
  getCoreBalance,
  spendCores,
  getCoreTransactions,
  getDailyCoreSummary,
  hasEnoughCores,
  AI_HINT_COSTS,
  CORE_REWARDS,
  type CoreBalance,
  type CoreSpendCategory,
  type CoreEarnCategory,
  type CoreTransaction,
  type CoreTransactionList,
  type DailyCoreSummary,
  type SpendRequest,
  type SpendResult,
} from "./core";
