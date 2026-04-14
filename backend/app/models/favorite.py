"""Favorite model for user exercise favorites"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.time import utc_now

if TYPE_CHECKING:
    from app.models.user import User


class Favorite(Base):
    """User's favorite exercises"""

    __tablename__ = "favorites"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "exercise_id", "chapter_id", "subsection_index",
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
    chapter_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    subsection_index: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    note: Mapped[str | None] = mapped_column(
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
        return f"<Favorite user={self.user_id} exercise={self.exercise_id}>"
