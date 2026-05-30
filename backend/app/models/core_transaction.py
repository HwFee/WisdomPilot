"""
Core Transaction Model - 智核交易记录

Records all earning and spending of cores (智核), the platform's currency.
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


class CoreTransaction(Base):
    """Records all core (智核) transactions for a user.

    Categories for earning:
    - mastery: Earning from mastery path (精进之路)
    - arena: Earning from challenge path (挑战之路)
    - checkin: Daily check-in reward
    - study_time: Learning time reward
    - daily_exercises: Daily exercise count reward
    - daily_accuracy: Daily accuracy reward
    - bonus: Manual bonus from admin or special events

    Categories for spending:
    - ai_hint_light: Light AI hint (1 core)
    - ai_hint_medium: Medium AI hint (3 cores)
    - ai_hint_deep: Deep AI explanation (5 cores)
    """

    __tablename__ = "core_transactions"

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
        comment="Source or destination of cores"
    )
    amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Amount of cores (always positive)"
    )
    balance_after: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Balance after this transaction"
    )
    reference_type: Mapped[Optional[str]] = mapped_column(
        String(30),
        nullable=True,
        comment="Reference type: 'exercise', 'chapter', 'challenge', etc."
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
    user: Mapped["User"] = relationship("User", back_populates="core_transactions")

    def __repr__(self) -> str:
        return f"<CoreTransaction user={self.user_id[:8]}... type={self.type} amount={self.amount}>"


# Add index for common queries
Index('ix_core_transactions_user_created', CoreTransaction.user_id, CoreTransaction.created_at.desc())
