"""Favorite model for user exercise favorites"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.time import utc_now

if TYPE_CHECKING:
    from app.models.user import User


class Favorite(Base):
    """User's favorite exercises

    Supports favorites from:
    - 精进之路 (chapter exercises): chapter_id required
    - 挑战之路 (arena challenges): challenge_session_id used instead
    - 错题本 (wrong questions): referenced by exercise_id
    """

    __tablename__ = "favorites"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "exercise_id", "chapter_id", "subsection_index", "challenge_session_id",
            name="uq_user_exercise_favorite"
        ),
    )

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
    exercise_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    # 精进之路来源
    chapter_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )
    subsection_index: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    # 挑战之路来源
    challenge_session_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True
    )
    # 收藏夹分类
    folder: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="收藏夹分类名称"
    )
    note: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="favorites")

    def __repr__(self) -> str:
        source = f"chapter={self.chapter_id}" if self.chapter_id else f"challenge={self.challenge_session_id}"
        return f"<Favorite user={self.user_id} exercise={self.exercise_id} {source}>"
