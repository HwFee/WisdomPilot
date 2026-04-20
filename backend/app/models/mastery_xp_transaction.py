"""
Mastery XP Transaction Model - 精进之路经验变化记录

Records all mastery XP changes for a user.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.time import utc_now

if TYPE_CHECKING:
    from app.models.user import User


class MasteryXpTransaction(Base):
    """Records all mastery XP (精进之路经验) changes for a user.

    Categories for earning:
    - base_test: Base test questions correct answer
    - mastery_quiz: Mastery quiz completion
    - achievement: Achievement reward
    - bonus: Manual bonus from admin or special events

    Categories for spending:
    - Currently mastery XP is only earned, not spent
    """

    __tablename__ = "mastery_xp_transactions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    type: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="'earn' or 'spend'"
    )
    category: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        comment="Source or destination of XP"
    )
    amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Amount of XP (always positive)"
    )
    balance_after: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Balance after this transaction"
    )
    level_before: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Level before this transaction"
    )
    level_after: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Level after this transaction"
    )
    level_up: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        comment="Whether user leveled up"
    )
    reference_type: Mapped[Optional[str]] = mapped_column(
        String(30),
        nullable=True,
        comment="Reference type: 'exercise', 'chapter', 'quiz', etc."
    )
    reference_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="ID of the referenced entity"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Human-readable description"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
        index=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User")

    def __repr__(self) -> str:
        return f"<MasteryXpTransaction user={self.user_id[:8]}... type={self.type} amount={self.amount}>"


# Add index for common queries
Index('ix_mastery_xp_transactions_user_created', MasteryXpTransaction.user_id, MasteryXpTransaction.created_at.desc())
