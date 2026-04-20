"""Models package - 数据模型"""

from app.models.user import User
from app.models.session import LoginSession
from app.models.stats import ChapterProgress, LearningSession, ActivityLog
from app.models.course import Course
from app.models.chapter import Chapter
from app.models.section import Section
from app.models.exercise import Exercise
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
from app.models.wrong_question import WrongQuestion
from app.models.section_base_question import SectionBaseQuestion, ChapterBaseQuestion
from app.models.arena_exercise_progress import ArenaExerciseProgress
from app.models.mastery_exercise_progress import MasteryExerciseProgress
from app.models.section import Section
from app.models.section_progress import SectionProgress
from app.models.core_transaction import CoreTransaction
from app.models.ai_hint_cache import AIHintCache
from app.models.knowledge_point_mastery import KnowledgePointMastery
from app.models.answer_history import AnswerHistory
from app.models.section_mastery import SectionMastery
from app.models.course_mastery import CourseMastery
from app.models.tier_transaction import TierTransaction
from app.models.mastery_xp_transaction import MasteryXpTransaction

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
    "Section",
    "Exercise",
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
    # Wrong Questions System
    "WrongQuestion",
    # Section Base Questions
    "SectionBaseQuestion",
    "ChapterBaseQuestion",
    # Arena Progress
    "ArenaExerciseProgress",
    # Mastery Exercise Progress
    "MasteryExerciseProgress",
    # Section
    "Section",
    # Section Progress
    "SectionProgress",
    # Core (智核) System
    "CoreTransaction",
    # AI Hint Cache
    "AIHintCache",
    # BKT Mastery System
    "KnowledgePointMastery",
    "AnswerHistory",
    "SectionMastery",
    "CourseMastery",
    # Tier (段位) System
    "TierTransaction",
    # Mastery XP (精进之路经验) System
    "MasteryXpTransaction",
]
