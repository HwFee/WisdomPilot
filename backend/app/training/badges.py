"""徽章系统：定义清单（常量，不入库）+ 事实聚合 + 幂等评估引擎。

判定风格参照 mastery.py：规则是纯函数 `check(facts, ctx) -> bool`，不各自查库；
`collect_facts` 一次性聚合全部事实表，`evaluate_and_award` 在提交端点事务内
commit 前调用，已解锁的跳过（deck_user_badges 复合唯一约束兜底）。

`ctx` 是本次提交的瞬时上下文（dict，回填时为 None），目前支持：
- arena_win_streak: 本次竞技场提交后的当前连胜（历史峰值不落库，只能靠当前值触发）
- cert_score: 本次认证考试得分
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.training import service
from app.training.models import (
    DeckArenaAttempt,
    DeckArenaRating,
    DeckCertification,
    DeckKnowledgePoint,
    DeckMasteryEvent,
    DeckReviewAttempt,
    DeckTutorMessage,
    DeckUserBadge,
    DeckUserMastery,
)
from app.auth.models import User

# ── 奖励常量（分级轻奖励，全部解锁共 165 智核）─────────────

TIER_BRONZE = "bronze"
TIER_SILVER = "silver"
TIER_GOLD = "gold"

BRONZE_REWARD = 5
SILVER_REWARD = 10
GOLD_REWARD = 20

NIGHT_OWL_END_HOUR = 5          # 夜猫子：北京时间 00:00–05:00（不含 5 点）
PERFECT_ACCURACY = 1.0          # 复习舱单次判定全命中
PERFECT_SCORE = 100             # 认证满分
ARENA_STREAK_TARGET = 3         # 竞技场三连胜
STREAK_3_DAYS = 3
STREAK_7_DAYS = 7
MULTI_TOPIC_TARGET = 2          # 博览：认证覆盖主题数
FEYNMAN_TOP_GRADE = "优秀"
FEYNMAN_PASS_GRADES = frozenset({"良好", "优秀"})
CERT_LEVEL_ADEPT = "熟练"
CERT_LEVEL_MASTER = "精通"

HIDDEN_PLACEHOLDER = "???"      # 隐藏徽章未解锁时的脱敏文案


# ── 事实与规则 ──────────────────────────────────────────


@dataclass(frozen=True)
class BadgeFacts:
    """一次评估所需的全部事实（collect_facts 聚合，规则只读它）"""

    has_placement: bool
    cert_count: int
    cert_levels: frozenset[str]
    cert_topic_count: int
    cert_max_score: int
    review_attempt_count: int
    review_has_perfect: bool
    arena_win_count: int
    arena_win_streak: int
    feynman_pass_count: int
    feynman_best_grade: str | None
    streak_days: int
    night_event_count: int
    topic_all_mastered: bool
    has_comeback: bool


@dataclass(frozen=True)
class BadgeDef:
    id: str
    tier: str
    title: str
    hidden: bool
    condition_desc: str
    reward_cores: int
    check: Callable[[BadgeFacts, dict | None], bool]


def _ctx_int(ctx: dict | None, key: str) -> int:
    """读瞬时上下文里的整数，缺失/回填时按 0 处理"""
    if not ctx:
        return 0
    return int(ctx.get(key) or 0)


BADGES: list[BadgeDef] = [
    # ── 铜（+5）──
    BadgeDef("placement-done", TIER_BRONZE, "知己知彼", False,
             "完成定级测试", BRONZE_REWARD,
             lambda facts, ctx: facts.has_placement),
    BadgeDef("first-cert", TIER_BRONZE, "初露锋芒", False,
             "通过首次能力认证", BRONZE_REWARD,
             lambda facts, ctx: facts.cert_count >= 1),
    BadgeDef("review-first", TIER_BRONZE, "复盘首秀", False,
             "首次完成复习舱判定", BRONZE_REWARD,
             lambda facts, ctx: facts.review_attempt_count >= 1),
    BadgeDef("arena-first-win", TIER_BRONZE, "首胜", False,
             "竞技场首次全题通过", BRONZE_REWARD,
             lambda facts, ctx: facts.arena_win_count >= 1),
    BadgeDef("feynman-first", TIER_BRONZE, "以教为学", False,
             "首次费曼检验合格", BRONZE_REWARD,
             lambda facts, ctx: facts.feynman_pass_count >= 1),
    BadgeDef("streak-3", TIER_BRONZE, "三日不断", False,
             "连续学习 3 天", BRONZE_REWARD,
             lambda facts, ctx: facts.streak_days >= STREAK_3_DAYS),
    BadgeDef("night-owl", TIER_BRONZE, "夜猫子", True,
             "00:00–05:00 间完成一次有效提交", BRONZE_REWARD,
             lambda facts, ctx: facts.night_event_count >= 1),
    # ── 银（+10）──
    BadgeDef("cert-adept", TIER_SILVER, "游刃有余", False,
             "获得首个「熟练」级认证", SILVER_REWARD,
             lambda facts, ctx: CERT_LEVEL_ADEPT in facts.cert_levels
             or CERT_LEVEL_MASTER in facts.cert_levels),
    BadgeDef("cert-multi-topic", TIER_SILVER, "博览", False,
             "认证覆盖 2 个不同主题", SILVER_REWARD,
             lambda facts, ctx: facts.cert_topic_count >= MULTI_TOPIC_TARGET),
    BadgeDef("review-perfect", TIER_SILVER, "弹无虚发", False,
             "复习舱单次判定全命中", SILVER_REWARD,
             lambda facts, ctx: facts.review_has_perfect),
    BadgeDef("arena-streak-3", TIER_SILVER, "连战连捷", False,
             "竞技场三连胜", SILVER_REWARD,
             lambda facts, ctx: facts.arena_win_streak >= ARENA_STREAK_TARGET
             or _ctx_int(ctx, "arena_win_streak") >= ARENA_STREAK_TARGET),
    BadgeDef("feynman-star", TIER_SILVER, "讲明白了", False,
             "费曼检验拿到最高评级", SILVER_REWARD,
             lambda facts, ctx: facts.feynman_best_grade == FEYNMAN_TOP_GRADE),
    BadgeDef("streak-7", TIER_SILVER, "七日之约", False,
             "连续学习 7 天", SILVER_REWARD,
             lambda facts, ctx: facts.streak_days >= STREAK_7_DAYS),
    BadgeDef("perfect-score", TIER_SILVER, "满分答卷", True,
             "认证考试得分 100", SILVER_REWARD,
             lambda facts, ctx: facts.cert_max_score >= PERFECT_SCORE
             or _ctx_int(ctx, "cert_score") >= PERFECT_SCORE),
    # ── 金（+20）──
    BadgeDef("cert-master", TIER_GOLD, "登峰造极", False,
             "获得首个「精通」级认证", GOLD_REWARD,
             lambda facts, ctx: CERT_LEVEL_MASTER in facts.cert_levels),
    BadgeDef("topic-ascend", TIER_GOLD, "一域通天", False,
             "单主题全部知识点达「精通」", GOLD_REWARD,
             lambda facts, ctx: facts.topic_all_mastered),
    BadgeDef("comeback", TIER_GOLD, "起死回生", True,
             "同一知识点先答错、后在复习舱答对", GOLD_REWARD,
             lambda facts, ctx: facts.has_comeback),
]

BADGE_BY_ID: dict[str, BadgeDef] = {b.id: b for b in BADGES}


# ── 事实聚合 ────────────────────────────────────────────


async def _cert_facts(db: AsyncSession, user_id: str) -> tuple[int, frozenset, int, int]:
    rows = (
        await db.execute(
            select(DeckCertification).where(DeckCertification.user_id == user_id)
        )
    ).scalars().all()
    levels = frozenset(r.level for r in rows)
    topic_count = len({r.topic for r in rows})
    max_score = max((r.score for r in rows), default=0)
    return len(rows), levels, topic_count, max_score


async def _review_facts(db: AsyncSession, user_id: str) -> tuple[int, bool]:
    verdicts = (
        await db.execute(
            select(DeckReviewAttempt.verdict).where(DeckReviewAttempt.user_id == user_id)
        )
    ).scalars().all()
    has_perfect = any(v.get("accuracy") == PERFECT_ACCURACY for v in verdicts)
    return len(verdicts), has_perfect


async def _arena_facts(db: AsyncSession, user_id: str) -> tuple[int, int]:
    attempts = (
        await db.execute(
            select(DeckArenaAttempt.solved).where(DeckArenaAttempt.user_id == user_id)
        )
    ).scalars().all()
    rating = await db.get(DeckArenaRating, user_id)
    win_streak = rating.win_streak if rating else 0
    return sum(1 for s in attempts if s), win_streak


async def _feynman_facts(db: AsyncSession, user_id: str) -> tuple[int, str | None]:
    grades = (
        await db.execute(
            select(DeckTutorMessage.grade).where(
                DeckTutorMessage.user_id == user_id,
                DeckTutorMessage.mode == "feynman",
                DeckTutorMessage.grade.is_not(None),
            )
        )
    ).scalars().all()
    pass_count = sum(1 for g in grades if g in FEYNMAN_PASS_GRADES)
    best = FEYNMAN_TOP_GRADE if FEYNMAN_TOP_GRADE in grades else (
        "良好" if "良好" in grades else (grades[0] if grades else None)
    )
    return pass_count, best


def _scan_events(events: list[DeckMasteryEvent]) -> tuple[int, bool]:
    """扫一遍掌握度事件：夜间（北京时间 0–5 点）事件数 + comeback 序列判定"""
    night_count = 0
    wrong_seen: set[str] = set()
    has_comeback = False
    for e in sorted(events, key=lambda x: x.created_at):
        hour = e.created_at.replace(tzinfo=timezone.utc).astimezone(service.BJT).hour
        if hour < NIGHT_OWL_END_HOUR:
            night_count += 1
        if not e.correct:
            wrong_seen.add(e.kp_id)
        elif e.source == "review_gym" and e.kp_id in wrong_seen:
            has_comeback = True
    return night_count, has_comeback


async def _topic_all_mastered(db: AsyncSession, user_id: str) -> bool:
    """是否存在某个主题（知识点 category）其全部知识点都达「精通」"""
    kps = (await db.execute(select(DeckKnowledgePoint))).scalars().all()
    mastery_rows = (
        await db.execute(
            select(DeckUserMastery).where(DeckUserMastery.user_id == user_id)
        )
    ).scalars().all()
    level_by_kp = {m.kp_id: m.level for m in mastery_rows}
    by_topic: dict[str, list[str]] = {}
    for kp in kps:
        by_topic.setdefault(kp.category, []).append(kp.id)
    return any(
        all(level_by_kp.get(kp_id) == CERT_LEVEL_MASTER for kp_id in kp_ids)
        for kp_ids in by_topic.values()
    )


async def collect_facts(db: AsyncSession, user_id: str) -> BadgeFacts:
    """集中聚合各事实表（规则不各自查库）。在提交事务内调用时靠 autoflush 看到本次写入"""
    cert_count, cert_levels, cert_topic_count, cert_max_score = await _cert_facts(db, user_id)
    review_count, review_has_perfect = await _review_facts(db, user_id)
    arena_wins, arena_win_streak = await _arena_facts(db, user_id)
    feynman_pass, feynman_best = await _feynman_facts(db, user_id)
    events = (
        await db.execute(
            select(DeckMasteryEvent).where(DeckMasteryEvent.user_id == user_id)
        )
    ).scalars().all()
    night_count, has_comeback = _scan_events(list(events))
    return BadgeFacts(
        has_placement=await service.has_placement(db, user_id),
        cert_count=cert_count,
        cert_levels=cert_levels,
        cert_topic_count=cert_topic_count,
        cert_max_score=cert_max_score,
        review_attempt_count=review_count,
        review_has_perfect=review_has_perfect,
        arena_win_count=arena_wins,
        arena_win_streak=arena_win_streak,
        feynman_pass_count=feynman_pass,
        feynman_best_grade=feynman_best,
        streak_days=await service.streak_days(db, user_id),
        night_event_count=night_count,
        topic_all_mastered=await _topic_all_mastered(db, user_id),
        has_comeback=has_comeback,
    )


# ── 评估引擎 ────────────────────────────────────────────


def _unlock_out(badge: BadgeDef) -> dict:
    return {
        "id": badge.id,
        "tier": badge.tier,
        "title": badge.title,
        "reward_cores": badge.reward_cores,
    }


async def evaluate_and_award(
    db: AsyncSession, user_id: str, ctx: dict | None = None
) -> list[dict]:
    """全量跑规则，新达成的写表 + 发智核 + 写动态。幂等：已解锁的跳过。

    在提交端点事务内 commit 前调用；返回本次新解锁列表（供前端播解锁动画）。
    """
    user = await db.get(User, user_id)
    if user is None:
        return []
    facts = await collect_facts(db, user_id)
    unlocked_ids = set(
        (
            await db.execute(
                select(DeckUserBadge.badge_id).where(DeckUserBadge.user_id == user_id)
            )
        ).scalars().all()
    )

    new_badges: list[dict] = []
    for badge in BADGES:
        if badge.id in unlocked_ids or not badge.check(facts, ctx):
            continue
        db.add(DeckUserBadge(user_id=user_id, badge_id=badge.id))
        await service.change_cores(
            db, user, badge.reward_cores, f"解锁徽章 · {badge.title}"
        )
        await service.add_feed(
            db,
            user_id,
            "badge",
            [
                {"t": "解锁徽章 "},
                {"t": badge.title, "tone": "strong"},
                {"t": f" · +{badge.reward_cores} 智核", "tone": "ok"},
            ],
        )
        new_badges.append(_unlock_out(badge))
    return new_badges


async def list_badges(db: AsyncSession, user_id: str) -> list[dict]:
    """徽章墙：全量 17 枚 + 解锁状态。hidden 且未解锁时 title/desc 脱敏为 ???"""
    rows = (
        await db.execute(
            select(DeckUserBadge).where(DeckUserBadge.user_id == user_id)
        )
    ).scalars().all()
    unlocked_at_by_id = {r.badge_id: r.unlocked_at for r in rows}

    infos: list[dict] = []
    for badge in BADGES:
        unlocked_at = unlocked_at_by_id.get(badge.id)
        unlocked = unlocked_at is not None
        mask = badge.hidden and not unlocked
        infos.append(
            {
                "id": badge.id,
                "tier": badge.tier,
                "title": HIDDEN_PLACEHOLDER if mask else badge.title,
                "condition_desc": HIDDEN_PLACEHOLDER if mask else badge.condition_desc,
                "hidden": badge.hidden,
                "unlocked": unlocked,
                "reward_cores": badge.reward_cores,
                "unlocked_at": unlocked_at.isoformat() if unlocked else None,
            }
        )
    return infos
