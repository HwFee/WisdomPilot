import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Integer, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.utils.time import utc_now


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
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    username: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_test_account: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Test account - first 3 arena exercises pass without verification",
    )
    cores: Mapped[int] = mapped_column(
        Integer,
        default=100,
        nullable=False,
        comment="Core (智核) balance - platform currency",
    )
    cores_total_earned: Mapped[int] = mapped_column(
        Integer,
        default=100,
        nullable=False,
        comment="Total cores earned (starts with 100 initial bonus)",
    )
    cores_total_spent: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="Total cores spent"
    )
    # Learning profile fields
    xp: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Experience points (from check-in, etc.)",
    )
    # Mastery path fields
    mastery_xp: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Mastery path experience points (from quizzes)",
    )
    mastery_level: Mapped[str] = mapped_column(
        String(20),
        default="入门",
        nullable=False,
        comment="Mastery level: 入门/学习/练习/熟练/精通",
    )
    streak_days: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="Current learning streak in days"
    )
    last_activity_date: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, nullable=False, comment="Last activity timestamp"
    )
    total_checkin_days: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="Total check-in days (cumulative)"
    )
    preferred_languages: Mapped[list] = mapped_column(
        JSON, default=list, nullable=False, comment="Preferred programming languages"
    )
    total_exercises: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="Total exercises completed"
    )
    correct_exercises: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="Total correct exercises"
    )
    accuracy_rate: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False, comment="Accuracy rate percentage"
    )
    # 新增字段 - 课程与学习进度
    courses_enrolled: Mapped[list] = mapped_column(
        JSON, default=list, nullable=False, comment="已选课程ID列表"
    )
    weak_points: Mapped[list] = mapped_column(
        JSON, default=list, nullable=False, comment="薄弱知识点列表"
    )
    preferred_difficulty: Mapped[int] = mapped_column(
        Integer, default=2, nullable=False, comment="偏好难度（1-5）"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now, nullable=False
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"
