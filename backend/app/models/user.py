import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import String, Boolean, DateTime, Integer, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, TYPE_CHECKING

from app.database import Base
from app.utils.time import utc_now

if TYPE_CHECKING:
    from app.models.stats import ChapterProgress, LearningSession, ActivityLog
    from app.models.achievement import UserAchievement
    from app.models.user_weak_point import UserWeakPoint
    from app.models.spaced_repetition import SpacedRepetition
    from app.models.favorite import Favorite
    from app.models.note import Note
    from app.models.chapter_mastery import ChapterMastery
    from app.models.wrong_question import WrongQuestion
    from app.models.core_transaction import CoreTransaction
    from app.models.ai_hint_cache import AIHintCache
    from app.models.tier_transaction import TierTransaction
    from app.models.mastery_xp_transaction import MasteryXpTransaction


class User(Base):
    """User model for authentication and profile

    扩展字段支持：
    - 课程选课
    - 总经验值
    - 学习连续天数
    - 薄弱知识点
    - 偏好难度
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )
    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    is_admin: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    cores: Mapped[int] = mapped_column(
        Integer,
        default=100,
        nullable=False,
        comment="Core (智核) balance - platform currency"
    )
    cores_total_earned: Mapped[int] = mapped_column(
        Integer,
        default=100,
        nullable=False,
        comment="Total cores earned (starts with 100 initial bonus)"
    )
    cores_total_spent: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Total cores spent"
    )
    # Learning profile fields
    xp: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Experience points (from check-in, etc.)"
    )
    # Mastery path fields
    mastery_xp: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Mastery path experience points (from quizzes)"
    )
    mastery_level: Mapped[str] = mapped_column(
        String(20),
        default="入门",
        nullable=False,
        comment="Mastery level: 入门/学习/练习/熟练/精通"
    )
    streak_days: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Current learning streak in days"
    )
    last_activity_date: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
        comment="Last activity timestamp"
    )
    total_checkin_days: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Total check-in days (cumulative)"
    )
    preferred_languages: Mapped[list] = mapped_column(
        JSON,
        default=list,
        nullable=False,
        comment="Preferred programming languages"
    )
    total_exercises: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Total exercises completed"
    )
    correct_exercises: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Total correct exercises"
    )
    accuracy_rate: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        comment="Accuracy rate percentage"
    )
    # 新增字段 - 课程与学习进度
    courses_enrolled: Mapped[list] = mapped_column(
        JSON,
        default=list,
        nullable=False,
        comment="已选课程ID列表"
    )
    total_xp: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="总经验值（用于排行榜）"
    )
    current_streak: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="当前连续学习天数"
    )
    weak_points: Mapped[list] = mapped_column(
        JSON,
        default=list,
        nullable=False,
        comment="薄弱知识点列表"
    )
    preferred_difficulty: Mapped[int] = mapped_column(
        Integer,
        default=2,
        nullable=False,
        comment="偏好难度（1-5）"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"

    # Relationships to stats models
    chapter_progress: Mapped[List["ChapterProgress"]] = relationship(
        "ChapterProgress", back_populates="user"
    )
    learning_sessions: Mapped[List["LearningSession"]] = relationship(
        "LearningSession", back_populates="user"
    )
    activity_logs: Mapped[List["ActivityLog"]] = relationship(
        "ActivityLog", back_populates="user"
    )
    challenges: Mapped[List["UserChallenge"]] = relationship(
        "UserChallenge", back_populates="user"
    )
    achievements: Mapped[List["UserAchievement"]] = relationship(
        "UserAchievement", back_populates="user"
    )
    weak_point_records: Mapped[List["UserWeakPoint"]] = relationship(
        "UserWeakPoint", back_populates="user"
    )
    spaced_repetitions: Mapped[List["SpacedRepetition"]] = relationship(
        "SpacedRepetition", back_populates="user"
    )
    favorites: Mapped[List["Favorite"]] = relationship(
        "Favorite", back_populates="user"
    )
    notes: Mapped[List["Note"]] = relationship(
        "Note", back_populates="user"
    )
    chapter_masteries: Mapped[List["ChapterMastery"]] = relationship(
        "ChapterMastery", back_populates="user"
    )
    wrong_questions: Mapped[List["WrongQuestion"]] = relationship(
        "WrongQuestion", back_populates="user"
    )
    core_transactions: Mapped[List["CoreTransaction"]] = relationship(
        "CoreTransaction", back_populates="user"
    )
    ai_hint_caches: Mapped[List["AIHintCache"]] = relationship(
        "AIHintCache", back_populates="user"
    )
    tier_transactions: Mapped[List["TierTransaction"]] = relationship(
        "TierTransaction", back_populates="user"
    )
    mastery_xp_transactions: Mapped[List["MasteryXpTransaction"]] = relationship(
        "MasteryXpTransaction", back_populates="user"
    )
