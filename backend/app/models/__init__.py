"""Models package - 数据模型"""

from app.models.user import User
from app.models.session import LoginSession
from app.models.stats import ChapterProgress, LearningSession, ActivityLog
from app.models.course import Course
from app.models.chapter import Chapter
from app.models.exercise import Exercise
from app.models.stage import Stage
from app.models.user_stage import UserStageProgress, StageStatus
from app.models.user_weak_point import UserWeakPoint
from app.models.spaced_repetition import SpacedRepetition
from app.models.challenge import Challenge, ChallengeType
from app.models.user_challenge import UserChallenge, UserChallengeStatus
from app.models.achievement import Achievement, AchievementType, UserAchievement
from app.models.favorite import Favorite
from app.models.note import Note
from app.models.chapter_mastery import ChapterMastery
from app.models.challenge_session import ChallengeSession
from app.models.user_arena import UserArenaProfile

__all__ = [
    # User & Auth
    "User",
    "LoginSession",
    # Learning Progress
    "ChapterProgress",
    "LearningSession",
    "ActivityLog",
    # Course Structure
    "Course",
    "Chapter",
    "Exercise",
    # Stage System
    "Stage",
    "UserStageProgress",
    "StageStatus",
    # Review System
    "UserWeakPoint",
    "SpacedRepetition",
    # Challenge System
    "Challenge",
    "ChallengeType",
    "UserChallenge",
    "UserChallengeStatus",
    # Achievement System
    "Achievement",
    "AchievementType",
    "UserAchievement",
    # Favorites & Notes
    "Favorite",
    "Note",
    # Mastery System
    "ChapterMastery",
    # Challenge Path System
    "ChallengeSession",
    "UserArenaProfile",
]
