import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, TYPE_CHECKING

from app.database import Base
from app.utils.time import utc_now

if TYPE_CHECKING:
    from app.models.stats import ChapterProgress, LearningSession, ActivityLog


class User(Base):
    """User model for authentication and profile"""

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
