"""
Tier Transaction Model - 段位变化记录

Records all tier changes for a user.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, Index, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.time import utc_now

if TYPE_CHECKING:
    from app.models.user import User


class TierTransaction(Base):
    """Records all tier (段位) changes for a user.

    Tracks:
    - Star gains/losses
    - Promotions/demotions
    - Protection uses
    """

    __tablename__ = "tier_transactions"

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
    course_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="课程ID"
    )

    # Tier state before
    tier_before: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="变化前端位"
    )
    sub_tier_before: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="变化前子段位"
    )
    stars_before: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="变化前星星数"
    )

    # Tier state after
    tier_after: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="变化后段位"
    )
    sub_tier_after: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="变化后子段位"
    )
    stars_after: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="变化后星星数"
    )

    # Change details
    stars_change: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="星星变化量（正数获得，负数失去）"
    )
    promoted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否晋级"
    )
    demoted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否降级"
    )
    used_protection: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否使用了段位保护"
    )
    protection_remaining: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="剩余保护次数"
    )

    # Source of change
    source: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        comment="变化来源: arena_challenge, test, admin, etc."
    )
    reference_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="关联ID（如挑战ID）"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="描述"
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
        return f"<TierTransaction user={self.user_id[:8]}... stars={self.stars_change:+d}>"


# Add index for common queries
Index('ix_tier_transactions_user_created', TierTransaction.user_id, TierTransaction.created_at.desc())
Index('ix_tier_transactions_course', TierTransaction.course_id, TierTransaction.user_id)
