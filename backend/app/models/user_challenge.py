"""UserChallenge model - tracks user challenge progress"""

import uuid
import enum
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.time import utc_now

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.challenge import Challenge


class UserChallengeStatus(str, enum.Enum):
    """User challenge status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class UserChallenge(Base):
    """Tracks user's challenge progress"""

    __tablename__ = "user_challenges"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )
    challenge_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("challenges.id"),
        nullable=False,
        index=True
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default=UserChallengeStatus.NOT_STARTED.value,
        nullable=False
    )
    current_progress: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Current progress value"
    )
    target_value: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Target value to complete"
    )
    attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="challenges")
    challenge: Mapped["Challenge"] = relationship("Challenge", back_populates="user_challenges")

    def __repr__(self) -> str:
        return f"<UserChallenge user={self.user_id} challenge={self.challenge_id} status={self.status}>"
