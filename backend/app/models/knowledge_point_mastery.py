"""
Knowledge Point Mastery Model - 知识点 BKT 掌握状态

追踪每个用户对每个知识点的 BKT (Bayesian Knowledge Tracing) 状态。
一个章节可能包含多个知识点，同一知识点可能出现在多个章节。

BKT 四参数模型：
- P(L0): 初始掌握概率
- P(T): 学习率（从未掌握到掌握）
- P(G): 猜测率（未掌握但答对）
- P(S): 失误率（已掌握但答错）
"""

import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING

from app.database import Base
from app.utils.time import utc_now

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.course import Course
    from app.models.chapter import Chapter
    from app.models.section import Section


# 默认 BKT 参数
DEFAULT_P_L0 = 0.15   # 初始掌握概率
DEFAULT_P_T = 0.1     # 学习率
DEFAULT_P_G = 0.2     # 猜测率
DEFAULT_P_S = 0.05    # 失误率

# 掌握阈值
MASTERY_THRESHOLD = 0.95


class KnowledgePointMastery(Base):
    """
    知识点 BKT 掌握状态

    追踪每个用户对每个知识点的掌握状态。
    使用贝叶斯知识追踪算法计算掌握概率。
    """

    __tablename__ = "knowledge_point_mastery"

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
    knowledge_point: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="知识点名称，如：数组、循环、递归"
    )

    # 关联上下文（主要用于显示和统计）
    course_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("courses.id"),
        nullable=True
    )
    chapter_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("chapters.id"),
        nullable=True,
        index=True
    )
    section_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("sections.id"),
        nullable=True,
        index=True,
        comment="关联的小节ID，用于小节级掌握度聚合"
    )

    # BKT 核心参数（支持针对不同知识点定制）
    p_l0: Mapped[float] = mapped_column(
        Float,
        default=DEFAULT_P_L0,
        comment="初始掌握概率 P(L0)"
    )
    p_t: Mapped[float] = mapped_column(
        Float,
        default=DEFAULT_P_T,
        comment="学习率 P(T)"
    )
    p_g: Mapped[float] = mapped_column(
        Float,
        default=DEFAULT_P_G,
        comment="猜测率 P(G)"
    )
    p_s: Mapped[float] = mapped_column(
        Float,
        default=DEFAULT_P_S,
        comment="失误率 P(S)"
    )

    # 当前掌握概率（BKT 计算结果）
    p_l: Mapped[float] = mapped_column(
        Float,
        default=DEFAULT_P_L0,
        comment="当前掌握概率 P(L)"
    )

    # 统计信息
    total_attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="总答题次数（计入掌握度的）"
    )
    correct_attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="正确次数"
    )
    unique_questions: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="不同题目数"
    )

    # 时间戳
    first_attempt_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )
    last_attempt_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )
    mastered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="达到掌握阈值(P(L)>=0.95)的时间"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
    course: Mapped[Optional["Course"]] = relationship("Course")
    chapter: Mapped[Optional["Chapter"]] = relationship("Chapter")
    section: Mapped[Optional["Section"]] = relationship("Section")

    __table_args__ = (
        UniqueConstraint("user_id", "knowledge_point", name="uq_user_knowledge_point"),
        Index("idx_kp_mastery_chapter", "chapter_id"),
        Index("idx_kp_mastery_section", "section_id"),
        Index("idx_kp_mastery_user_chapter", "user_id", "chapter_id"),
        Index("idx_kp_mastery_user_section", "user_id", "section_id"),
    )

    def __repr__(self) -> str:
        return f"<KnowledgePointMastery user={self.user_id[:8]} kp={self.knowledge_point} p_l={self.p_l:.3f}>"

    @property
    def is_mastered(self) -> bool:
        """是否已掌握"""
        return self.p_l >= MASTERY_THRESHOLD

    @property
    def correct_rate(self) -> float:
        """正确率"""
        if self.total_attempts == 0:
            return 0.0
        return self.correct_attempts / self.total_attempts

    @property
    def mastery_score(self) -> float:
        """掌握度分数 (0-100)"""
        return self.p_l * 100

    @property
    def mastery_level(self) -> str:
        """掌握等级"""
        score = self.mastery_score
        if score >= 95:
            return "精通"
        elif score >= 85:
            return "熟练"
        elif score >= 70:
            return "练习"
        elif score >= 50:
            return "学习"
        else:
            return "入门"
