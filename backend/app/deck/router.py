"""训练舱 API 路由（/api/dashboard、review-gym、arena、tutor、certification、ability-map、profile）。

响应结构与 frontend/lib/api/deck/types.ts 逐字段对应。
"""

from datetime import datetime
from urllib.parse import quote
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deck import mastery, service
from app.deck.models import (
    DeckAbilityAxis,
    DeckArenaAttempt,
    DeckArenaChallenge,
    DeckArenaRating,
    DeckCertExam,
    DeckCertification,
    DeckCertQuestion,
    DeckCoreTransaction,
    DeckDailyActivity,
    DeckFeedEvent,
    DeckInjectedDefect,
    DeckKnowledgePoint,
    DeckReviewAttempt,
    DeckReviewSession,
    DeckTutorMessage,
    DeckUserMastery,
)
from app.models import User
from app.utils.deps import get_current_active_user

router = APIRouter(prefix="/api", tags=["deck"])

WEEKDAY_LABELS = ["一", "二", "三", "四", "五", "六", "日"]


# ── 请求体 ──────────────────────────────────────────────


class ReviewMarkIn(BaseModel):
    line: int
    type: str


class ReviewSubmitIn(BaseModel):
    session_id: str
    marks: list[ReviewMarkIn]


class ArenaRunIn(BaseModel):
    challenge_id: str
    code: str


class TutorMessageIn(BaseModel):
    text: str
    mode: str = "socratic"


class FeynmanStartIn(BaseModel):
    topic: str


class FeynmanCheckIn(BaseModel):
    session_id: str
    text: str


class CertAnswerIn(BaseModel):
    question_id: str
    answer: str


class CertSubmitIn(BaseModel):
    exam_id: str
    answers: list[CertAnswerIn]


# ── 主任务构建 ──────────────────────────────────────────


def _review_task(session: DeckReviewSession, stage_no: int) -> dict:
    return {
        "id": session.id,
        "module": "review-gym",
        "module_label": "代码审查室",
        "stage_label": f"第 {stage_no} 关",
        "title": f"这段{session.title}里有 {session.defect_count} 处缺陷，它们藏得很像“能跑的代码”。",
        "highlight": f"{session.defect_count} 处缺陷",
        "desc": "AI 生成的代码 70% 能直接运行，但其中三分之一藏着边界错误。找出它们——这比写出它们更值钱。",
        "difficulty": session.difficulty,
        "eta_minutes": session.eta_minutes,
        "related_weakness": session.related_weakness,
        "target_url": f"/review-gym?session={session.id}",
        "cta_label": "开始审查 →",
        "alternates": [],
    }


def _arena_task(challenge: DeckArenaChallenge) -> dict:
    return {
        "id": challenge.id,
        "module": "arena",
        "module_label": "调试竞技场",
        "stage_label": "今日挑战",
        "title": f"{challenge.title}——限时让测试全部变绿。",
        "highlight": None,
        "desc": "失败输出已经摆在你面前。速度和准确率都算分，全站唯一的排行榜只认这个。",
        "difficulty": challenge.difficulty,
        "eta_minutes": max(1, challenge.time_limit_sec // 60),
        "related_weakness": None,
        "target_url": f"/arena?challenge={challenge.id}",
        "cta_label": "开始调试 →",
        "alternates": [],
    }


def _tutor_task(topic: str) -> dict:
    return {
        "id": f"TUTOR-{topic}",
        "module": "tutor",
        "module_label": "苏格拉底导师",
        "stage_label": "费曼检验",
        "title": f"用自己的话，向导师讲清楚「{topic}」。",
        "highlight": topic,
        "desc": "能讲明白才是真懂。导师会追问你的每一个模糊点，直到没有盲区。",
        "difficulty": 2,
        "eta_minutes": 5,
        "related_weakness": topic,
        "target_url": f"/tutor?topic={topic}",
        "cta_label": "开始对话 →",
        "alternates": [],
    }


def _cert_task() -> dict:
    return {
        "id": "CERT-TODAY",
        "module": "certification",
        "module_label": "基本功认证",
        "stage_label": "无 AI 环境",
        "title": "来一场没有 AI 的基本功认证，证明你不靠 AI 也会。",
        "highlight": "不靠 AI 也会",
        "desc": "限时手写，没有提示。通过后获得可分享的能力凭证。",
        "difficulty": 3,
        "eta_minutes": 15,
        "related_weakness": None,
        "target_url": "/certification",
        "cta_label": "开始认证 →",
        "alternates": [],
    }


async def _weakest_kp_names(db: AsyncSession, user_id: str, limit: int = 3) -> list[str]:
    rows = (
        await db.execute(
            select(DeckKnowledgePoint.name)
            .join(DeckUserMastery, DeckUserMastery.kp_id == DeckKnowledgePoint.id)
            .where(DeckUserMastery.user_id == user_id)
            .order_by(DeckUserMastery.p_l.asc())
            .limit(limit)
        )
    ).scalars().all()
    if rows:
        return list(rows)
    # 未定级兜底：种子前三个
    fallback = (
        await db.execute(select(DeckKnowledgePoint.name).limit(limit))
    ).scalars().all()
    return list(fallback)


async def _next_review_session(db: AsyncSession, user_id: str) -> DeckReviewSession | None:
    sessions = (
        await db.execute(select(DeckReviewSession).order_by(DeckReviewSession.id))
    ).scalars().all()
    attempted = set(
        (
            await db.execute(
                select(DeckReviewAttempt.session_id).where(DeckReviewAttempt.user_id == user_id)
            )
        ).scalars().all()
    )
    for s in sessions:
        if s.id not in attempted:
            return s
    return sessions[0] if sessions else None


async def _today_challenge(db: AsyncSession) -> DeckArenaChallenge | None:
    challenges = (
        await db.execute(select(DeckArenaChallenge).order_by(DeckArenaChallenge.id))
    ).scalars().all()
    if not challenges:
        return None
    return challenges[service.today_bjt().toordinal() % len(challenges)]


async def build_main_task(db: AsyncSession, user: User, axes: list[dict]) -> dict | None:
    """主任务分发（docs/backend-api/01 §2）：未定级 null；实现轴<LV.3 走认证/导师；否则最低轴模块"""
    if not await service.has_placement(db, user.id):
        return None

    weakest_names = await _weakest_kp_names(db, user.id, 1)
    weakest = weakest_names[0] if weakest_names else "递归出口设计"
    implement = next(a for a in axes if a["key"] == "implement")
    session = await _next_review_session(db, user.id)
    challenge = await _today_challenge(db)
    cooldown = await service.next_cert_available_days(db, user.id)

    candidates: dict[str, dict] = {}
    if session:
        stage_no = 1
        candidates["review"] = _review_task(session, stage_no)
    if challenge:
        candidates["debug"] = _arena_task(challenge)
    candidates["implement"] = _tutor_task(weakest)
    cert_task = _cert_task()

    if implement["level"] < 3:
        primary = cert_task if not cooldown else _tutor_task(weakest)
    else:
        lowest = min(axes, key=lambda a: a["level"])
        primary = candidates.get(lowest["key"], _tutor_task(weakest))

    pool = [t for t in [*candidates.values(), cert_task] if t["id"] != primary["id"]]
    primary["alternates"] = pool[:2]
    return primary


# ── Dashboard / ability-map / profile ────────────────────


@router.get("/dashboard")
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> dict:
    axes = await service.get_axes(db, user.id)
    main_task = await build_main_task(db, user, axes)

    # 模块 stat-line
    today_done, avg_accuracy = await service.attempts_today(db, user.id)
    streak = await service.streak_days(db, user.id)
    rating = await service.get_or_create_rating(db, user.id)
    rank = await service.week_rank(db, rating.rating)
    today_used = await service.today_cores_used(db, user.id)
    certs = (
        await db.execute(
            select(DeckCertification).where(DeckCertification.user_id == user.id)
        )
    ).scalars().all()
    cooldown = await service.next_cert_available_days(db, user.id)

    modules = [
        {
            "key": "review-gym",
            "stats": [
                {"label": "今日完成", "value": str(today_done)},
                {"label": "命中率", "value": f"{round(avg_accuracy * 100)}%"},
                *([{"label": f"连续 {streak} 天", "trend": "up"}] if streak >= 2 else []),
            ],
        },
        {
            "key": "arena",
            "stats": [
                {"label": "段位", "value": service.tier_of(rating.rating)},
                {"label": "本周排名", "value": f"#{rank}"},
                *([{"label": f"连对 {rating.win_streak} 场", "trend": "up"}] if rating.win_streak >= 2 else []),
            ],
        },
        {
            "key": "tutor",
            "stats": [
                {"label": "智核余额", "value": str(user.cores)},
                {"label": "今日已用", "value": str(today_used // max(service.TUTOR_COST, 1))},
            ],
        },
        {
            "key": "certification",
            "stats": [
                {"label": "已认证", "value": " / ".join(c.topic for c in certs) or "暂无"},
                {
                    "label": "下次可考",
                    "value": "随时" if not cooldown else f"{cooldown} 天后",
                },
            ],
        },
    ]

    # 弱点（p_l 最低 3 个）
    weak_rows = (
        await db.execute(
            select(DeckKnowledgePoint.name, DeckKnowledgePoint.category, DeckUserMastery.p_l)
            .join(DeckUserMastery, DeckUserMastery.kp_id == DeckKnowledgePoint.id)
            .where(DeckUserMastery.user_id == user.id)
            .order_by(DeckUserMastery.p_l.asc())
            .limit(3)
        )
    ).all()
    weak_points = [{"name": n, "category": c, "p_l": p} for n, c, p in weak_rows]

    # 7 天节奏
    today = service.today_bjt()
    activity_rows = (
        await db.execute(
            select(DeckDailyActivity).where(DeckDailyActivity.user_id == user.id)
        )
    ).scalars().all()
    minutes_map = {r.day: r.minutes for r in activity_rows}
    from datetime import timedelta

    days = []
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        days.append(
            {
                "label": WEEKDAY_LABELS[day.weekday()],
                "minutes": minutes_map.get(day, 0),
                "is_today": day == today,
            }
        )

    # 复盘待清（与 /api/review/queue 同源）
    queue_items = await _build_review_queue(db, user)
    due_total = len(queue_items)

    # 动态
    feed_rows = (
        await db.execute(
            select(DeckFeedEvent)
            .where(DeckFeedEvent.user_id == user.id)
            .order_by(DeckFeedEvent.created_at.desc())
            .limit(4)
        )
    ).scalars().all()
    feed = [
        {"time": service.feed_time_label(e.created_at), "segments": e.payload["segments"]}
        for e in feed_rows
    ]

    return {
        "user": {"name": user.username, "cores": user.cores},
        "main_task": main_task,
        "ability_map": {
            "axes": axes,
            "has_placement": await service.has_placement(db, user.id),
        },
        "modules": modules,
        "weak_points": weak_points,
        "rhythm": {"days": days, "streak_days": streak},
        "review_due": {"total": due_total, "due_today": min(2, due_total)},
        "feed": feed,
    }


@router.get("/ability-map")
async def get_ability_map(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> dict:
    axes = await service.get_axes(db, user.id)
    kps = (await db.execute(select(DeckKnowledgePoint))).scalars().all()
    mastery_rows = (
        await db.execute(
            select(DeckUserMastery).where(DeckUserMastery.user_id == user.id)
        )
    ).scalars().all()
    mastery_map = {m.kp_id: m for m in mastery_rows}
    trend_map = await service.mastery_trends(db, user.id)
    return {
        "axes": axes,
        "has_placement": await service.has_placement(db, user.id),
        "knowledge_points": [
            {
                "name": kp.name,
                "category": kp.category,
                "axis": kp.axis,
                "p_l": mastery_map[kp.id].p_l if kp.id in mastery_map else 0.5,
                "level": mastery_map[kp.id].level if kp.id in mastery_map else "初识",
                "trend": trend_map.get(kp.id, "flat"),
            }
            for kp in kps
        ],
    }


@router.get("/profile")
async def get_profile(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> dict:
    rating = await service.get_or_create_rating(db, user.id)
    rank = await service.week_rank(db, rating.rating)
    transactions = (
        await db.execute(
            select(DeckCoreTransaction)
            .where(DeckCoreTransaction.user_id == user.id)
            .order_by(DeckCoreTransaction.created_at.desc())
            .limit(50)
        )
    ).scalars().all()
    certs = (
        await db.execute(
            select(DeckCertification)
            .where(DeckCertification.user_id == user.id)
            .order_by(DeckCertification.created_at.desc())
        )
    ).scalars().all()
    top_rows = (
        await db.execute(
            select(DeckArenaRating, User.username)
            .join(User, DeckArenaRating.user_id == User.id)
            .order_by(DeckArenaRating.rating.desc())
            .limit(10)
        )
    ).all()
    solved_today_map = await _solved_today_map(db, [r.user_id for r, _ in top_rows] + [user.id])
    leaderboard = [
        {
            "rank": i + 1,
            "name": name,
            "rating": r.rating,
            "solved_today": solved_today_map.get(r.user_id, 0),
            "is_self": r.user_id == user.id,
        }
        for i, (r, name) in enumerate(top_rows)
    ]
    if not any(e["is_self"] for e in leaderboard):
        leaderboard.append(
            {
                "rank": rank,
                "name": user.username,
                "rating": rating.rating,
                "solved_today": solved_today_map.get(user.id, 0),
                "is_self": True,
            }
        )
    feed_rows = (
        await db.execute(
            select(DeckFeedEvent)
            .where(DeckFeedEvent.user_id == user.id)
            .order_by(DeckFeedEvent.created_at.desc())
            .limit(4)
        )
    ).scalars().all()

    joined_days = max(1, (datetime.now() - user.created_at.replace(tzinfo=None)).days + 1)
    return {
        "user": {"name": user.username, "joined_days": joined_days},
        "cores": {
            "balance": user.cores,
            "transactions": [
                {
                    "time": service.feed_time_label(t.created_at),
                    "delta": t.delta,
                    "reason": t.reason,
                }
                for t in transactions
            ],
        },
        "arena": {
            "tier": service.tier_of(rating.rating),
            "rating": rating.rating,
            "week_rank": rank,
            "rank_delta": 0,
            "win_streak": rating.win_streak,
        },
        "certifications": [
            {
                "topic": c.topic,
                "level": c.level,
                "date": c.created_at.date().isoformat(),
                "score": c.score,
                "verify_code": c.verify_code,
            }
            for c in certs
        ],
        "leaderboard": leaderboard,
        "recent": [
            {"time": service.feed_time_label(e.created_at), "segments": e.payload["segments"]}
            for e in feed_rows
        ],
    }


# ── 排行榜共用 ──────────────────────────────────────────


async def _solved_today_map(db: AsyncSession, user_ids: list[str]) -> dict[str, int]:
    """各用户今日竞技场攻克数"""
    if not user_ids:
        return {}
    rows = (
        await db.execute(
            select(DeckArenaAttempt.user_id, func.count())
            .where(
                DeckArenaAttempt.user_id.in_(user_ids),
                DeckArenaAttempt.solved == 1,
                func.date(DeckArenaAttempt.created_at) == service.today_bjt().isoformat(),
            )
            .group_by(DeckArenaAttempt.user_id)
        )
    ).all()
    return {uid: cnt for uid, cnt in rows}


async def _build_leaderboard(
    db: AsyncSession, user: User, rating: DeckArenaRating, rank: int
) -> list[dict]:
    """全站前 10 + 自己（不在榜时追加）"""
    top_rows = (
        await db.execute(
            select(DeckArenaRating, User.username)
            .join(User, DeckArenaRating.user_id == User.id)
            .order_by(DeckArenaRating.rating.desc())
            .limit(10)
        )
    ).all()
    solved_map = await _solved_today_map(db, [r.user_id for r, _ in top_rows] + [user.id])
    entries = [
        {
            "rank": i + 1,
            "name": name,
            "rating": r.rating,
            "solved_today": solved_map.get(r.user_id, 0),
            "is_self": r.user_id == user.id,
        }
        for i, (r, name) in enumerate(top_rows)
    ]
    if not any(e["is_self"] for e in entries):
        entries.append(
            {
                "rank": rank,
                "name": user.username,
                "rating": rating.rating,
                "solved_today": solved_map.get(user.id, 0),
                "is_self": True,
            }
        )
    return entries


# ── 代码审查室 /api/review-gym ───────────────────────────


def _session_out(s: DeckReviewSession) -> dict:
    """下发会话（绝不含注入缺陷）"""
    return {
        "id": s.id,
        "title": s.title,
        "language": s.language,
        "code": s.code,
        "defect_count": s.defect_count,
        "difficulty": s.difficulty,
        "eta_minutes": s.eta_minutes,
        "related_weakness": s.related_weakness,
    }


async def _record_review_mastery(
    db: AsyncSession, user_id: str, weakness_name: str | None, gained: int
) -> None:
    """审查关掌握度结算：related_weakness 命中的知识点每新增一处命中记一条答对事件"""
    if not weakness_name or not gained:
        return
    kp = (
        await db.execute(
            select(DeckKnowledgePoint).where(DeckKnowledgePoint.name == weakness_name)
        )
    ).scalar_one_or_none()
    if kp is None:
        return
    for _ in range(gained):
        await service.record_mastery_event(db, user_id, kp.id, "review_gym", True)


@router.get("/review-gym/session")
async def get_review_session(
    id: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> dict:
    if id:
        session = await db.get(DeckReviewSession, id)
    else:
        session = await _next_review_session(db, user.id)
    if session is None:
        raise HTTPException(status_code=404, detail="没有可用的审查关卡")
    return _session_out(session)


@router.post("/review-gym/submit")
async def submit_review(
    body: ReviewSubmitIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> dict:
    session = await db.get(DeckReviewSession, body.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="审查关卡不存在")

    defect_rows = (
        await db.execute(
            select(DeckInjectedDefect).where(DeckInjectedDefect.session_id == session.id)
        )
    ).scalars().all()
    defects = [
        {"line": d.line, "type": d.type, "explanation": d.explanation} for d in defect_rows
    ]
    marks = [m.model_dump() for m in body.marks]

    existing = (
        await db.execute(
            select(DeckReviewAttempt).where(
                DeckReviewAttempt.user_id == user.id,
                DeckReviewAttempt.session_id == body.session_id,
            )
        )
    ).scalar_one_or_none()

    if existing is not None:
        old = existing.verdict
        if not old.get("missed") and not old.get("false_alarms"):
            # 已全中：幂等返回旧判定，不再结算
            return old
        # 复盘重做：重新判定，只按「新增命中」结算，防止刷经验
        verdict = service.judge_marks(defects, marks)
        gained = max(0, len(verdict["hits"]) - len(old.get("hits", [])))
        existing.marks = marks
        existing.verdict = verdict
        if gained:
            await service.add_axis_xp(db, user.id, "review", 20 * gained)
            await _record_review_mastery(db, user.id, session.related_weakness, gained)
        await service.touch_activity(
            db, user.id, minutes=session.eta_minutes, correct=len(verdict["hits"])
        )
        clean_now = not verdict["missed"] and not verdict["false_alarms"]
        if clean_now and defects:
            # 全中奖励每关至多一次：attempt 变全中后上面的幂等分支直接返回
            await service.change_cores(db, user, 5, "代码审查全命中")
        await service.add_feed(
            db,
            user.id,
            "review",
            [
                {"t": "重审 "},
                {"t": session.id, "tone": "strong"},
                {
                    "t": f"，命中 {len(verdict['hits'])}/{len(defects)}",
                    "tone": "ok" if clean_now else "bad",
                },
            ],
        )
        await db.commit()
        return verdict

    verdict = service.judge_marks(defects, marks)
    db.add(
        DeckReviewAttempt(
            user_id=user.id, session_id=session.id, marks=marks, verdict=verdict
        )
    )

    hits = len(verdict["hits"])
    await service.add_axis_xp(db, user.id, "review", 20 * hits)
    await _record_review_mastery(db, user.id, session.related_weakness, hits)
    await service.touch_activity(db, user.id, minutes=session.eta_minutes, correct=hits)
    clean = hits == len(defects) and not verdict["false_alarms"]
    await service.add_feed(
        db,
        user.id,
        "review",
        [
            {"t": "完成代码审查 "},
            {"t": session.id, "tone": "strong"},
            {
                "t": f"，命中 {hits}/{len(defects)}",
                "tone": "ok" if not verdict["missed"] else "bad",
            },
        ],
    )
    if clean and defects:
        await service.change_cores(db, user, 5, "代码审查全命中")
    await db.commit()
    return verdict


# ── 复盘 /api/review ─────────────────────────────────────

WEAK_MASTERY_THRESHOLD = 0.6


async def _build_review_queue(db: AsyncSession, user: User) -> list[dict]:
    """错题/失败项聚合：审查漏报、竞技场未攻克、弱知识点（费曼检验入口）"""
    items: list[dict] = []

    # 1. 审查关：当前判定有漏报或误报（重做全中后自动出队）
    review_attempts = (
        await db.execute(
            select(DeckReviewAttempt).where(DeckReviewAttempt.user_id == user.id)
        )
    ).scalars().all()
    session_map = {
        s.id: s for s in (await db.execute(select(DeckReviewSession))).scalars().all()
    }
    for attempt in review_attempts:
        missed = len(attempt.verdict.get("missed", []))
        false_alarms = len(attempt.verdict.get("false_alarms", []))
        if not missed and not false_alarms:
            continue
        s = session_map.get(attempt.session_id)
        items.append(
            {
                "id": f"rg-{attempt.session_id}",
                "kind": "review-gym",
                "title": f"重审 {attempt.session_id}" + (f" · {s.title}" if s else ""),
                "detail": f"漏报 {missed} 处" + (f" · 误报 {false_alarms} 处" if false_alarms else ""),
                "target_url": f"/review-gym?session={attempt.session_id}",
                "cta_label": "重新审查 →",
                "last_at": service.feed_time_label(attempt.created_at),
            }
        )

    # 2. 竞技场：尝试过但从未攻克的挑战
    arena_rows = (
        await db.execute(
            select(
                DeckArenaAttempt.challenge_id,
                func.max(DeckArenaAttempt.solved),
                func.max(DeckArenaAttempt.created_at),
            )
            .where(DeckArenaAttempt.user_id == user.id)
            .group_by(DeckArenaAttempt.challenge_id)
        )
    ).all()
    for challenge_id, best_solved, last_at in arena_rows:
        if best_solved:
            continue
        challenge = await db.get(DeckArenaChallenge, challenge_id)
        if challenge is None:
            continue
        items.append(
            {
                "id": f"ar-{challenge_id}",
                "kind": "arena",
                "title": f"再战 {challenge.id} · {challenge.title}",
                "detail": "尚未让测试全部变绿",
                "target_url": "/arena",
                "cta_label": "继续调试 →",
                "last_at": service.feed_time_label(last_at),
            }
        )

    # 3. 弱知识点：p_l 低于阈值 → 费曼检验入口
    weak_rows = (
        await db.execute(
            select(DeckKnowledgePoint.name, DeckUserMastery.p_l)
            .join(DeckUserMastery, DeckUserMastery.kp_id == DeckKnowledgePoint.id)
            .where(
                DeckUserMastery.user_id == user.id,
                DeckUserMastery.p_l < WEAK_MASTERY_THRESHOLD,
            )
            .order_by(DeckUserMastery.p_l.asc())
        )
    ).all()
    for name, p_l in weak_rows:
        items.append(
            {
                "id": f"kp-{name}",
                "kind": "knowledge",
                "title": f"费曼检验 · {name}",
                "detail": f"掌握度 {round(p_l * 100)}%",
                "target_url": f"/tutor?topic={quote(name)}",
                "cta_label": "去讲清楚 →",
                "last_at": "",
            }
        )

    return items


@router.get("/review/queue")
async def get_review_queue(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> dict:
    items = await _build_review_queue(db, user)
    return {"items": items, "total": len(items)}


# ── 调试竞技场 /api/arena ────────────────────────────────


@router.get("/arena/home")
async def get_arena_home(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> dict:
    rating = await service.get_or_create_rating(db, user.id)
    rank = await service.week_rank(db, rating.rating)
    challenge = await _today_challenge(db)
    if challenge is None:
        raise HTTPException(status_code=404, detail="今日挑战尚未配置")
    return {
        "profile": {
            "tier": service.tier_of(rating.rating),
            "rating": rating.rating,
            "week_rank": rank,
            "rank_delta": 0,
            "win_streak": rating.win_streak,
        },
        "challenge": {
            "id": challenge.id,
            "title": challenge.title,
            "language": challenge.language,
            "code": challenge.code,
            "failing_output": challenge.failing_output,
            "time_limit_sec": challenge.time_limit_sec,
            "difficulty": challenge.difficulty,
        },
        "leaderboard": await _build_leaderboard(db, user, rating, rank),
    }


@router.post("/arena/run")
async def run_arena(
    body: ArenaRunIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> dict:
    challenge = await db.get(DeckArenaChallenge, body.challenge_id)
    if challenge is None:
        raise HTTPException(status_code=404, detail="挑战不存在")

    result = service.judge_arena_code(body.code, challenge.failing_output)
    db.add(
        DeckArenaAttempt(
            user_id=user.id,
            challenge_id=challenge.id,
            solved=1 if result["solved"] else 0,
            passed=result["passed"],
            total=result["total"],
        )
    )

    rating = await service.get_or_create_rating(db, user.id)
    if result["solved"]:
        rating.rating += result["score_delta"]
        rating.win_streak += 1
        await service.add_axis_xp(db, user.id, "debug", result["score_delta"])
        await service.add_feed(
            db,
            user.id,
            "arena",
            [
                {"t": "拿下今日挑战 "},
                {"t": challenge.id, "tone": "strong"},
                {"t": f"，积分 +{result['score_delta']}", "tone": "ok"},
            ],
        )
        if rating.win_streak >= 3:
            await service.change_cores(db, user, 10, "竞技场三连胜奖励")
    else:
        rating.win_streak = 0
    await service.touch_activity(
        db, user.id, minutes=max(1, challenge.time_limit_sec // 60), correct=result["passed"]
    )
    await db.commit()
    return result


# ── 苏格拉底导师 /api/tutor ──────────────────────────────


def _message_out(m: DeckTutorMessage) -> dict:
    return {"id": m.id, "role": m.role, "mode": m.mode, "text": m.text}


@router.get("/tutor/state")
async def get_tutor_state(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> dict:
    messages = (
        await db.execute(
            select(DeckTutorMessage)
            .where(DeckTutorMessage.user_id == user.id)
            .order_by(DeckTutorMessage.created_at.desc())
            .limit(20)
        )
    ).scalars().all()
    return {
        "cores_balance": user.cores,
        "today_used": await service.today_cores_used(db, user.id),
        "cost_per_question": service.TUTOR_COST,
        "messages": [_message_out(m) for m in reversed(messages)],
        "suggested_topics": await _weakest_kp_names(db, user.id, 3),
    }


@router.post("/tutor/message")
async def send_tutor_message(
    body: TutorMessageIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> dict:
    db.add(DeckTutorMessage(user_id=user.id, role="user", mode=body.mode, text=body.text))

    if user.cores < service.TUTOR_COST:
        # 契约：余额不足返回 200 + 提示消息，不扣费
        text = "你的智核余额不足了。去基本功认证通过一场考试，或者明天再来——每日登录会补充 5 智核。"
    else:
        history_len = await db.scalar(
            select(func.count())
            .select_from(DeckTutorMessage)
            .where(DeckTutorMessage.user_id == user.id)
        )
        text = service.socratic_reply(body.text, int(history_len or 0))
        await service.change_cores(db, user, -service.TUTOR_COST, "苏格拉底导师 · 追问")
        await service.touch_activity(db, user.id, minutes=1)

    reply = DeckTutorMessage(user_id=user.id, role="tutor", mode=body.mode, text=text)
    db.add(reply)
    await db.commit()
    await db.refresh(reply)
    return {"message": _message_out(reply), "cores_balance": user.cores}


# 费曼会话（内存态，dev 后端够用）：session_id → {user_id, kp_id, created_at}
FEYNMAN_SESSIONS: dict[str, dict] = {}


@router.post("/tutor/feynman")
async def start_feynman(
    body: FeynmanStartIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> dict:
    kp = (
        await db.execute(
            select(DeckKnowledgePoint).where(DeckKnowledgePoint.name == body.topic)
        )
    ).scalar_one_or_none()
    if kp is None:
        raise HTTPException(status_code=404, detail="知识点不存在")

    session_id = str(uuid4())
    FEYNMAN_SESSIONS[session_id] = {
        "user_id": user.id,
        "kp_id": kp.id,
        "created_at": datetime.now(),
    }
    reply = DeckTutorMessage(
        user_id=user.id,
        role="tutor",
        mode="feynman",
        text=service.feynman_opening(body.topic),
    )
    db.add(reply)
    await db.commit()
    await db.refresh(reply)
    return {
        "message": _message_out(reply),
        "cores_balance": user.cores,
        "feynman_session_id": session_id,
    }


@router.post("/tutor/feynman/check")
async def check_feynman(
    body: FeynmanCheckIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> dict:
    session = FEYNMAN_SESSIONS.get(body.session_id)
    if session is None or session["user_id"] != user.id:
        raise HTTPException(status_code=404, detail="费曼会话不存在或已过期")
    kp = await db.get(DeckKnowledgePoint, session["kp_id"])
    if kp is None:
        raise HTTPException(status_code=404, detail="知识点不存在")

    result = mastery.feynman_grade(body.text, kp.key_points)
    grade = result["grade"]
    verdict = service.feynman_feedback(grade, result["covered"], result["missed"])

    p_l_before, p_l_after, level = await service.record_mastery_event(
        db, user.id, kp.id, "feynman", correct=grade != "待加强", grade=grade
    )

    await service.change_cores(db, user, -service.TUTOR_COST, "费曼检验 · 点评")
    await service.touch_activity(db, user.id, minutes=3)
    reply = DeckTutorMessage(
        user_id=user.id, role="tutor", mode="feynman", text=verdict, grade=grade
    )
    db.add(reply)
    await db.commit()
    await db.refresh(reply)
    return {
        "message": _message_out(reply),
        "cores_balance": user.cores,
        "grade": grade,
        "mastery_update": {
            "kp_name": kp.name,
            "p_l_before": p_l_before,
            "p_l_after": p_l_after,
            "level": level,
        },
    }


# ── 基本功认证 /api/certification ───────────────────────


def _cert_record(c: DeckCertification) -> dict:
    return {
        "topic": c.topic,
        "level": c.level,
        "date": c.created_at.date().isoformat(),
        "score": c.score,
        "verify_code": c.verify_code,
    }


async def _exam_info(db: AsyncSession, exam: DeckCertExam) -> dict:
    count = await db.scalar(
        select(func.count())
        .select_from(DeckCertQuestion)
        .where(DeckCertQuestion.exam_id == exam.id)
    )
    return {
        "id": exam.id,
        "topic": exam.topic,
        "question_count": int(count or 0),
        "time_limit_min": exam.time_limit_min,
        "pass_score": exam.pass_score,
    }


@router.get("/certification/home")
async def get_certification_home(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> dict:
    certs = (
        await db.execute(
            select(DeckCertification)
            .where(DeckCertification.user_id == user.id)
            .order_by(DeckCertification.created_at.desc())
        )
    ).scalars().all()
    exams = (
        await db.execute(
            select(DeckCertExam).where(DeckCertExam.id != "placement")
        )
    ).scalars().all()
    return {
        "has_placement": await service.has_placement(db, user.id),
        "certified": [_cert_record(c) for c in certs],
        "available_exams": [await _exam_info(db, e) for e in exams],
        "next_available_days": await service.next_cert_available_days(db, user.id),
    }


@router.get("/certification/exam")
async def get_certification_exam(
    id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> dict:
    exam = await db.get(DeckCertExam, id)
    if exam is None:
        raise HTTPException(status_code=404, detail="试卷不存在")
    questions = (
        await db.execute(
            select(DeckCertQuestion)
            .where(DeckCertQuestion.exam_id == exam.id)
            .order_by(DeckCertQuestion.sort_order)
        )
    ).scalars().all()
    return {
        "info": await _exam_info(db, exam),
        "questions": [
            {  # 绝不下发答案字段
                "id": q.qid,
                "kind": q.kind,
                "prompt": q.prompt,
                **({"options": q.options} if q.options else {}),
                **({"starter_code": q.starter_code} if q.starter_code else {}),
            }
            for q in questions
        ],
    }


PLACEMENT_PASS_SCORE = 60  # 定级测试达到该分数，定级事件记为「已掌握起点」


def _cert_level(score: int) -> str:
    if score >= 90:
        return "精通"
    if score >= 75:
        return "熟练"
    return "合格"


@router.post("/certification/submit")
async def submit_certification(
    body: CertSubmitIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> dict:
    exam = await db.get(DeckCertExam, body.exam_id)
    if exam is None:
        raise HTTPException(status_code=404, detail="试卷不存在")
    questions = (
        await db.execute(
            select(DeckCertQuestion).where(DeckCertQuestion.exam_id == exam.id)
        )
    ).scalars().all()
    q_map = {q.qid: q for q in questions}

    per_question = []
    for answer in body.answers:
        q = q_map.get(answer.question_id)
        correct = bool(
            q
            and service.judge_cert_answer(
                q.kind, answer.answer, q.answer_correct, q.answer_includes
            )
        )
        per_question.append({"question_id": answer.question_id, "correct": correct})
    total = len(questions) or 1
    score = round(sum(1 for p in per_question if p["correct"]) / total * 100)

    certificate = None
    if exam.id == "placement":
        # 定级测试：每个知识点写一条定级事件（事件是事实源，p_l/level 由重放推导），
        # 并写三轴初始经验。correct 沿用原 score 语义：60 分及以上视为掌握起点
        placement_correct = score >= PLACEMENT_PASS_SCORE
        kps = (await db.execute(select(DeckKnowledgePoint))).scalars().all()
        for kp in kps:
            await service.record_mastery_event(
                db, user.id, kp.id, "placement", placement_correct
            )
        base_level = 1 + min(4, score // 25)
        for axis, level in (
            ("review", base_level),
            ("implement", base_level),
            ("debug", max(1, base_level - 1)),
        ):
            db.add(
                DeckAbilityAxis(
                    user_id=user.id, axis=axis, xp=(level - 1) * 400 + 200
                )
            )
        await service.add_feed(
            db,
            user.id,
            "cert",
            [
                {"t": "完成定级测试，"},
                {"t": f"{score} 分", "tone": "strong"},
                {"t": "，能力图谱已生成", "tone": "ok"},
            ],
        )
        passed = False
    else:
        passed = score >= exam.pass_score
        if passed:
            record = DeckCertification(
                user_id=user.id,
                topic=exam.topic,
                level=_cert_level(score),
                score=score,
                verify_code=service.new_verify_code("WP-PTR"),
            )
            db.add(record)
            await db.flush()  # 让 created_at 等默认值生效后再读
            await service.change_cores(db, user, 20, f"通过认证 · {exam.topic}")
            await service.add_axis_xp(db, user.id, "implement", 40)
            await service.add_feed(
                db,
                user.id,
                "cert",
                [
                    {"t": "通过基本功认证 "},
                    {"t": exam.topic, "tone": "strong"},
                    {"t": f" · {score} 分", "tone": "ok"},
                ],
            )
            certificate = _cert_record(record)

    await service.touch_activity(db, user.id, minutes=exam.time_limit_min,
                                 correct=sum(1 for p in per_question if p["correct"]))
    await db.commit()
    return {
        "score": score,
        "passed": passed,
        "certificate": certificate,
        "per_question": per_question,
    }
