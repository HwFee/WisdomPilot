"""训练舱数据模型（全新表，与旧系统无关）。

表名统一 deck_ 前缀，避免与 legacy 表冲突。
schema 契约：frontend/lib/api/deck/types.ts（docs/backend-api/01-target-design.md）。
"""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.utils.time import utc_now


def _uuid() -> str:
    return str(uuid.uuid4())


class DeckKnowledgePoint(Base):
    """知识点（种子内置，按三轴分组）"""

    __tablename__ = "deck_knowledge_points"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    axis: Mapped[str] = mapped_column(String(20), nullable=False)  # review/debug/implement
    # 费曼检验评分要点：[{"keys": [同义词...], "label": 要点名}]，种子内置
    key_points: Mapped[list | None] = mapped_column(JSON, nullable=True)


class DeckUserMastery(Base):
    """用户知识点掌握度缓存。p_l=HLR 回忆概率、level=掌握等级，事件表才是事实源。
    存在任意行即视为已定级（has_placement）"""

    __tablename__ = "deck_user_mastery"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), primary_key=True)
    kp_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("deck_knowledge_points.id"), primary_key=True
    )
    p_l: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    level: Mapped[str] = mapped_column(String(10), default="初识", nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)


class DeckMasteryEvent(Base):
    """掌握度事件流（事实源）：每次答题/检验一条，p_l 与 level 由它重放推导"""

    __tablename__ = "deck_mastery_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    kp_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("deck_knowledge_points.id"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    source: Mapped[str] = mapped_column(String(20), nullable=False)  # review_gym/arena/feynman/certification/placement
    correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    grade: Mapped[str | None] = mapped_column(String(10), nullable=True)  # 费曼评级
    hints_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)


class DeckAbilityAxis(Base):
    """三轴经验。等级 = 1 + xp//400，xp_next = level*400"""

    __tablename__ = "deck_ability_axes"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), primary_key=True)
    axis: Mapped[str] = mapped_column(String(20), primary_key=True)
    xp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class DeckReviewSession(Base):
    """代码审查室关卡（种子内容）"""

    __tablename__ = "deck_review_sessions"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)  # REVIEW-0247
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    language: Mapped[str] = mapped_column(String(20), nullable=False)
    code: Mapped[str] = mapped_column(Text, nullable=False)
    defect_count: Mapped[int] = mapped_column(Integer, nullable=False)
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False)
    eta_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    related_weakness: Mapped[str | None] = mapped_column(String(100), nullable=True)


class DeckInjectedDefect(Base):
    """注入缺陷（服务端秘密，绝不下发）"""

    __tablename__ = "deck_injected_defects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("deck_review_sessions.id"), nullable=False, index=True
    )
    line: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)


class DeckReviewAttempt(Base):
    """审查提交记录（幂等键 user_id+session_id 由 service 层保证）"""

    __tablename__ = "deck_review_attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    session_id: Mapped[str] = mapped_column(String(20), ForeignKey("deck_review_sessions.id"))
    marks: Mapped[list] = mapped_column(JSON, nullable=False)
    verdict: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class DeckArenaChallenge(Base):
    """调试竞技场挑战（种子内容，按日轮换）"""

    __tablename__ = "deck_arena_challenges"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)  # DEBUG-0091
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    language: Mapped[str] = mapped_column(String(20), nullable=False)
    code: Mapped[str] = mapped_column(Text, nullable=False)
    failing_output: Mapped[str] = mapped_column(Text, nullable=False)
    time_limit_sec: Mapped[int] = mapped_column(Integer, nullable=False)
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False)


class DeckArenaAttempt(Base):

    __tablename__ = "deck_arena_attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    challenge_id: Mapped[str] = mapped_column(String(20), ForeignKey("deck_arena_challenges.id"))
    solved: Mapped[bool] = mapped_column(Integer, default=0, nullable=False)
    passed: Mapped[int] = mapped_column(Integer, default=0)
    total: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class DeckArenaRating(Base):

    __tablename__ = "deck_arena_ratings"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), primary_key=True)
    rating: Mapped[int] = mapped_column(Integer, default=1200, nullable=False)
    win_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)


class DeckTutorMessage(Base):

    __tablename__ = "deck_tutor_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    role: Mapped[str] = mapped_column(String(10), nullable=False)  # user/tutor
    mode: Mapped[str] = mapped_column(String(10), nullable=False)  # socratic/feynman
    text: Mapped[str] = mapped_column(Text, nullable=False)
    grade: Mapped[str | None] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class DeckCoreTransaction(Base):
    """智核一本账（唯一变动途径）"""

    __tablename__ = "deck_core_transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    delta: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(200), nullable=False)
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class DeckCertExam(Base):
    """认证考试（种子内容；id=placement 为定级测试）"""

    __tablename__ = "deck_cert_exams"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)  # cert-pointer / placement
    topic: Mapped[str] = mapped_column(String(50), nullable=False)
    time_limit_min: Mapped[int] = mapped_column(Integer, nullable=False)
    pass_score: Mapped[int] = mapped_column(Integer, nullable=False)


class DeckCertQuestion(Base):
    """认证题目（答案不下发）"""

    __tablename__ = "deck_cert_questions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    exam_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("deck_cert_exams.id"), nullable=False, index=True
    )
    qid: Mapped[str] = mapped_column(String(10), nullable=False)  # q1/p1，前端用
    kind: Mapped[str] = mapped_column(String(10), nullable=False)  # mcq/code
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[list | None] = mapped_column(JSON, nullable=True)
    starter_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    answer_correct: Mapped[str | None] = mapped_column(String(500), nullable=True)  # mcq 答案
    answer_includes: Mapped[list | None] = mapped_column(JSON, nullable=True)  # code 关键片段
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class DeckCertification(Base):
    """能力凭证"""

    __tablename__ = "deck_certifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    topic: Mapped[str] = mapped_column(String(50), nullable=False)
    level: Mapped[str] = mapped_column(String(20), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    verify_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class DeckDailyActivity(Base):
    """每日活动（节奏柱图 / 今日统计 / 连续天数）"""

    __tablename__ = "deck_daily_activity"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), primary_key=True)
    day: Mapped[date] = mapped_column(Date, primary_key=True)
    minutes: Mapped[int] = mapped_column(Integer, default=0)
    exercises: Mapped[int] = mapped_column(Integer, default=0)
    correct: Mapped[int] = mapped_column(Integer, default=0)


class DeckFeedEvent(Base):
    """动态流。payload.segments 与前端 FeedItem.segments 同构"""

    __tablename__ = "deck_feed_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class DeckUserBadge(Base):
    """已解锁徽章（事实表）。徽章定义不入库，见 app/training/badges.py"""

    __tablename__ = "deck_user_badges"
    __table_args__ = (
        UniqueConstraint("user_id", "badge_id", name="uq_deck_user_badge"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    badge_id: Mapped[str] = mapped_column(String(40), nullable=False)
    unlocked_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
