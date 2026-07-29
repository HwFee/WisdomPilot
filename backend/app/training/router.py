"""训练舱 API 路由（/api/dashboard、review-gym、arena、tutor、certification、ability-map、profile）。

模块职责
========
本文件是训练舱后端所有 HTTP API 端点的定义所在，使用 FastAPI 的 APIRouter。

响应结构与 frontend/lib/api/deck/types.ts 逐字段对应。

覆盖的端点模块：
1. **Dashboard**（GET /api/dashboard）：首页数据聚合（能力轴、主任务、模块统计、弱点、节奏图、动态）
2. **能力图谱**（GET /api/ability-map）：三大能力轴 + 全部知识点掌握度
3. **个人主页**（GET /api/profile）：用户信息、智核账单、竞技场积分、认证记录、排行榜
4. **代码审查室**（GET/POST /api/review-gym/*）：获取审查会话、提交判定
5. **复盘队列**（GET /api/review/queue）：聚合错题/失败项
6. **调试竞技场**（GET/POST /api/arena/*）：获取今日挑战、提交代码运行
7. **苏格拉底导师**（GET/POST /api/tutor/*）：对话状态、发送消息、费曼检验
8. **基本功认证**（GET/POST /api/certification/*）：考试首页、获取试卷、提交答案

设计要点
========
- 所有端点都通过 ``Depends(get_db)`` 获取异步数据库会话
- 所有端点都通过 ``Depends(get_current_active_user)`` 校验 JWT 身份
- 涉及数据变更的端点（POST）在事务内完成判定 → 写事件 → 算徽章 → commit
- 返回结构中的 field 名保持 snake_case（Pydantic BaseModel 不做 camelCase 转换）
"""

from datetime import datetime
from urllib.parse import quote  # URL 编码，用于生成带中文参数的 target_url
from uuid import uuid4  # 生成唯一 ID（费曼检验会话）

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.training import badges, mastery, service
from app.training.models import (
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
from app.auth.models import User
from app.auth.dependencies import get_current_active_user

# 创建路由实例，所有端点前缀为 /api，在 Swagger UI 中归入 deck 标签组
router = APIRouter(prefix="/api", tags=["deck"])

# 星期中文标签（0=周一）：用于 Dashboard 7 天节奏图
WEEKDAY_LABELS = ["一", "二", "三", "四", "五", "六", "日"]


# ── 请求体 ──────────────────────────────────────────────
# FastAPI 的 Pydantic BaseModel 定义，用于自动校验前端请求的 JSON body。
# 每个请求体都是 immutably simple：只定义必要的字段，不做业务逻辑。


class ReviewMarkIn(BaseModel):
    """代码审查提交：单个缺陷标记的请求体"""
    line: int   # 标记的代码行号
    type: str   # 缺陷类型（如 "logic"、"boundary" 等）


class ReviewSubmitIn(BaseModel):
    """代码审查提交：整体请求体"""
    session_id: str       # 审查会话 ID
    marks: list[ReviewMarkIn]  # 用户标记的缺陷列表


class ArenaRunIn(BaseModel):
    """竞技场提交：代码运行请求体"""
    challenge_id: str  # 挑战 ID
    code: str          # 用户编写的修正代码


class TutorMessageIn(BaseModel):
    """导师对话：发送消息请求体"""
    text: str           # 用户消息文本
    mode: str = "socratic"  # 对话模式：socratic（苏格拉底追问）或 feynman（费曼检验）


class FeynmanStartIn(BaseModel):
    """费曼检验：开始请求体"""
    topic: str  # 要讲解的知识点名称


class FeynmanCheckIn(BaseModel):
    """费曼检验：提交讲解请求体"""
    session_id: str  # 费曼会话 ID（由 start_feynman 返回）
    text: str        # 用户的讲解文本


class CertAnswerIn(BaseModel):
    """认证考试：单题答案请求体"""
    question_id: str  # 题目 ID
    answer: str       # 用户答案


class CertSubmitIn(BaseModel):
    """认证考试：整体提交请求体"""
    exam_id: str                  # 试卷 ID
    answers: list[CertAnswerIn]   # 所有题目的答案列表


# ── 主任务构建 ──────────────────────────────────────────
# Dashboard 主任务（main_task）的构建逻辑。
# 主任务是一个推荐式的引导卡片：根据用户能力状态，推荐今天应该做什么。
# 分发策略见 docs/backend-api/01-target-design.md §2。

def _review_task(session: DeckReviewSession, stage_no: int) -> dict:
    """构建代码审查室主任务卡片。

    Args:
        session: 审查会话记录
        stage_no: 关卡编号

    Returns:
        主任务 card 的 dict 结构，含 module/module_label/stage_label/title 等字段
    """
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
    """构建竞技场主任务卡片。

    Args:
        challenge: 今日竞技场挑战记录
    """
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
    """构建苏格拉底导师主任务卡片（费曼检验入口）。

    Args:
        topic: 推荐讲解的知识点名称
    """
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
    """构建基本功认证主任务卡片。"""
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
    """获取用户掌握度最低的 N 个知识点名称。

    按 p_l（回忆概率）升序排列，p_l 越小表示越薄弱。
    未定级时兜底返回种子数据的前 N 个知识点名称。

    Args:
        db: 异步数据库会话
        user_id: 用户 ID
        limit: 返回数量上限（默认 3）

    Returns:
        知识点名称列表（按掌握度从低到高排列）
    """
    # 已定级用户：按 p_l 升序取最低的 N 个
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
    # 未定级兜底：取种子数据的前 N 个知识点名称
    fallback = (
        await db.execute(select(DeckKnowledgePoint.name).limit(limit))
    ).scalars().all()
    return list(fallback)


async def _next_review_session(db: AsyncSession, user_id: str) -> DeckReviewSession | None:
    """获取用户尚未完成的下一关审查会话。

    按顺序遍历所有审查会话，返回第一个未被该用户提交过的。
    用户全部完成后兜底返回第一个（可重做）。

    Args:
        db: 异步数据库会话
        user_id: 用户 ID

    Returns:
        下一个审查会话，全部完成时返回 None
    """
    # 获取全部审查会话，按 ID 排序
    sessions = (
        await db.execute(select(DeckReviewSession).order_by(DeckReviewSession.id))
    ).scalars().all()
    # 收集用户已提交过的会话 ID
    attempted = set(
        (
            await db.execute(
                select(DeckReviewAttempt.session_id).where(DeckReviewAttempt.user_id == user_id)
            )
        ).scalars().all()
    )
    # 返回第一个未尝试的
    for s in sessions:
        if s.id not in attempted:
            return s
    # 全部完成了：兜底返回第一个（允许重做）
    return sessions[0] if sessions else None


async def _today_challenge(db: AsyncSession) -> DeckArenaChallenge | None:
    """获取今日竞技场挑战（按日期轮替）。

    用今天日期的序数（toordinal）对挑战总数取模来轮替，
    保证每天挑战不同且可预测。

    Args:
        db: 异步数据库会话

    Returns:
        今日挑战记录，无挑战时返回 None
    """
    challenges = (
        await db.execute(select(DeckArenaChallenge).order_by(DeckArenaChallenge.id))
    ).scalars().all()
    if not challenges:
        return None
    # 用日期的「序数」取模：同一天总是同一道题，过天自动切换
    return challenges[service.today_bjt().toordinal() % len(challenges)]


async def build_main_task(db: AsyncSession, user: User, axes: list[dict]) -> dict | None:
    """主任务分发（docs/backend-api/01 §2）：未定级 null；实现轴<LV.3 走认证/导师；否则最低轴模块

    Dashboard 首页的核心推荐逻辑：
    1. 未定级 → 返回 null（前端引导用户先定级）
    2. 实现轴等级 < 3 → 优先推荐认证考试（若有冷却则退到费曼检验）
    3. 实现轴等级 ≥ 3 → 推荐能力最低轴的模块

    候选池：审查室（review）、竞技场（debug）、费曼检验（implement）、认证考试（cert）
    主任务会带最多 2 个备用任务（alternates）供用户选择。

    Args:
        db: 异步数据库会话
        user: 当前登录用户
        axes: 用户的三轴能力列表

    Returns:
        主任务卡片 dict，未定级时返回 None
    """
    # 1. 未定级检查
    if not await service.has_placement(db, user.id):
        return None

    # 取最弱点知识点（用于导师推荐话题）
    weakest_names = await _weakest_kp_names(db, user.id, 1)
    weakest = weakest_names[0] if weakest_names else "递归出口设计"
    implement = next(a for a in axes if a["key"] == "implement")
    session = await _next_review_session(db, user.id)
    challenge = await _today_challenge(db)
    cooldown = await service.next_cert_available_days(db, user.id)

    # 构建候选池：当前可用的模块任务
    candidates: dict[str, dict] = {}
    if session:
        stage_no = 1
        candidates["review"] = _review_task(session, stage_no)
    if challenge:
        candidates["debug"] = _arena_task(challenge)
    candidates["implement"] = _tutor_task(weakest)
    cert_task = _cert_task()

    # 2. 分发策略
    if implement["level"] < 3:
        # 实现轴偏低：优先认证（无冷却时），否则退到费曼检验
        primary = cert_task if not cooldown else _tutor_task(weakest)
    else:
        # 实现轴达标：推荐最低能力轴的模块
        lowest = min(axes, key=lambda a: a["level"])
        primary = candidates.get(lowest["key"], _tutor_task(weakest))

    # 3. 构建备用任务列表（排除主任务自身，最多 2 个）
    pool = [t for t in [*candidates.values(), cert_task] if t["id"] != primary["id"]]
    primary["alternates"] = pool[:2]
    return primary


# ── Dashboard / ability-map / profile ────────────────────
# Dashboard 是训练舱首页，聚合用户所有核心数据。
# ability-map 展示能力图谱详情，profile 展示个人主页和竞技排行。


@router.get("/dashboard")
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> dict:
    """Dashboard 首页数据聚合。

    这是训练舱最复杂的查询端点，一次性返回首页所需全部数据：
    - 能力轴（三轴等级、经验、短板知识点）
    - 主任务推荐卡片
    - 四大模块的统计行（stat-line）
    - 最薄弱 3 个知识点
    - 7 天学习节奏图
    - 复盘待清队列数量
    - 最新 4 条动态

    认证方式：JWT Bearer Token（通过 get_current_active_user 依赖）
    """
    # ========== 基础数据 ==========
    axes = await service.get_axes(db, user.id)
    main_task = await build_main_task(db, user, axes)

    # ========== 模块 stat-line（四模块的统计指标）==========
    today_done, avg_accuracy = await service.attempts_today(db, user.id)  # 审查室今日数据
    streak = await service.streak_days(db, user.id)                        # 连续学习天数
    rating = await service.get_or_create_rating(db, user.id)              # 竞技场积分
    rank = await service.week_rank(db, rating.rating)                     # 本周排名
    today_used = await service.today_cores_used(db, user.id)              # 今日已用智核
    # 认证记录（用于展示已认证主题）
    certs = (
        await db.execute(
            select(DeckCertification).where(DeckCertification.user_id == user.id)
        )
    ).scalars().all()
    cooldown = await service.next_cert_available_days(db, user.id)

    # 组装四模块统计行
    modules = [
        {
            "key": "review-gym",
            "stats": [
                {"label": "今日完成", "value": str(today_done)},
                {"label": "命中率", "value": f"{round(avg_accuracy * 100)}%"},
                # 连续 2 天及以上才显示 ticker（trend: "up"）
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
                # 今日消耗显示为次数（总消耗 // 每次花费）
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

    # ========== 弱点（p_l 最低 3 个知识点）==========
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

    # ========== 7 天节奏图 ==========
    today = service.today_bjt()
    activity_rows = (
        await db.execute(
            select(DeckDailyActivity).where(DeckDailyActivity.user_id == user.id)
        )
    ).scalars().all()
    # day -> minutes 的映射，用于填充 7 天柱状图
    minutes_map = {r.day: r.minutes for r in activity_rows}
    from datetime import timedelta

    days = []
    # 从 6 天前到今天，共 7 天
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        days.append(
            {
                "label": WEEKDAY_LABELS[day.weekday()],  # 星期几（一/二/.../日）
                "minutes": minutes_map.get(day, 0),       # 当天练习时长
                "is_today": day == today,
            }
        )

    # ========== 复盘待清 ==========
    queue_items = await _build_review_queue(db, user)
    due_total = len(queue_items)

    # ========== 最新动态 ==========
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
    """能力图谱详情页数据。

    返回三大能力轴 + 全部知识点的掌握度信息（p_l、等级、趋势）。
    用于独立页面的能力图谱可视化展示。

    Args:
        db: 异步数据库会话（依赖注入）
        user: 当前登录用户（JWT 校验注入）

    Returns:
        axes: 三大能力轴（同 Dashboard）
        has_placement: 是否已定级
        knowledge_points: 所有知识点的掌握状态列表
    """
    axes = await service.get_axes(db, user.id)
    # 取全部知识点定义
    kps = (await db.execute(select(DeckKnowledgePoint))).scalars().all()
    # 取用户的掌握度缓存
    mastery_rows = (
        await db.execute(
            select(DeckUserMastery).where(DeckUserMastery.user_id == user.id)
        )
    ).scalars().all()
    mastery_map = {m.kp_id: m for m in mastery_rows}
    # 取各知识点的 7 天趋势
    trend_map = await service.mastery_trends(db, user.id)
    return {
        "axes": axes,
        "has_placement": await service.has_placement(db, user.id),
        "knowledge_points": [
            {
                "name": kp.name,
                "category": kp.category,
                "axis": kp.axis,
                # 已定级取实际 p_l，未定级兜底 0.5（既不偏对也不偏错）
                "p_l": mastery_map[kp.id].p_l if kp.id in mastery_map else 0.5,
                "level": mastery_map[kp.id].level if kp.id in mastery_map else "初识",
                # 无事件的知识点趋势为 "flat"（平）
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
    """个人主页数据。

    返回用户信息、智核账单（最近 50 条）、竞技场积分段位、
    认证记录、排行榜（前 10 + 自己）、最近动态。

    Args:
        db: 异步数据库会话
        user: 当前登录用户

    Returns:
        个人主页全套数据
    """
    # ========== 竞技场数据 ==========
    rating = await service.get_or_create_rating(db, user.id)
    rank = await service.week_rank(db, rating.rating)

    # ========== 智核账单（最近 50 条交易流水）==========
    transactions = (
        await db.execute(
            select(DeckCoreTransaction)
            .where(DeckCoreTransaction.user_id == user.id)
            .order_by(DeckCoreTransaction.created_at.desc())
            .limit(50)
        )
    ).scalars().all()

    # ========== 认证记录 ==========
    certs = (
        await db.execute(
            select(DeckCertification)
            .where(DeckCertification.user_id == user.id)
            .order_by(DeckCertification.created_at.desc())
        )
    ).scalars().all()

    # ========== 排行榜（前 10）==========
    top_rows = (
        await db.execute(
            select(DeckArenaRating, User.username)
            .join(User, DeckArenaRating.user_id == User.id)
            .order_by(DeckArenaRating.rating.desc())
            .limit(10)
        )
    ).all()

    # 今日攻克数（排行榜上每人 + 自己）
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
# _solved_today_map 和 _build_leaderboard 是 profile 和 arena/home 共享的工具函数。


async def _solved_today_map(db: AsyncSession, user_ids: list[str]) -> dict[str, int]:
    """各用户今日竞技场攻克数。

    批量查询：传入多个 user_id，一次性返回每个人的今日攻克数。
    用于排行榜中展示「今日剑数」。

    Args:
        db: 异步数据库会话
        user_ids: 要查询的用户 ID 列表

    Returns:
        user_id -> 今日攻克数的映射字典
    """
    if not user_ids:
        return {}
    rows = (
        await db.execute(
            select(DeckArenaAttempt.user_id, func.count())
            .where(
                DeckArenaAttempt.user_id.in_(user_ids),
                DeckArenaAttempt.solved == 1,  # 只统计攻克成功的
                func.date(DeckArenaAttempt.created_at) == service.today_bjt().isoformat(),
            )
            .group_by(DeckArenaAttempt.user_id)
        )
    ).all()
    return {uid: cnt for uid, cnt in rows}


async def _build_leaderboard(
    db: AsyncSession, user: User, rating: DeckArenaRating, rank: int
) -> list[dict]:
    """全站前 10 + 自己（不在榜时追加）。

    排行榜展示规则：
    - 取积分最高的前 10 名
    - 每名标注 is_self 标记（当前用户高亮）
    - 如果当前用户不在前 10，在末尾追加自己的一行

    Args:
        db: 异步数据库会话
        user: 当前用户
        rating: 当前用户的竞技场积分记录
        rank: 当前用户本周排名

    Returns:
        排行榜条目列表（每条含 rank/name/rating/solved_today/is_self）
    """
    # 取全站前 10
    top_rows = (
        await db.execute(
            select(DeckArenaRating, User.username)
            .join(User, DeckArenaRating.user_id == User.id)
            .order_by(DeckArenaRating.rating.desc())
            .limit(10)
        )
    ).all()
    # 批量查今日攻克数
    solved_map = await _solved_today_map(db, [r.user_id for r, _ in top_rows] + [user.id])
    entries = [
        {
            "rank": i + 1,
            "name": name,
            "rating": r.rating,
            "solved_today": solved_map.get(r.user_id, 0),
            "is_self": r.user_id == user.id,  # 标记当前用户以便前端高亮
        }
        for i, (r, name) in enumerate(top_rows)
    ]
    # 当前用户不在榜上时追加
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
# 代码审查室（Review Gym）：用户查看一段有缺陷的代码，标记发现的缺陷位置和类型。
# 后端判定用户标记与实际注入缺陷的匹配度，计算命中/漏报/误报。

def _session_out(s: DeckReviewSession) -> dict:
    """下发会话（绝不含注入缺陷）。

    安全设计：返回给前端的审查会话数据中不包含 injected defects 的行号和类型。
    这些数据只在 submit 时用于后端判定，确保用户无法通过查看 API 返回作弊。

    Args:
        s: 审查会话 ORM 对象

    Returns:
        前端展示所需的会话数据（code/defect_count/难度等，不含缺陷位置）
    """
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
    """审查关掌握度结算：related_weakness 命中的知识点每新增一处命中记一条答对事件。

    每个关卡有一个关联弱点知识点（related_weakness），
    用户在审查中每命中一处缺陷就对该知识点记录一次正确事件，
    从而提升该知识点的 p_l。

    Args:
        db: 异步数据库会话
        user_id: 用户 ID
        weakness_name: 关联弱点知识点名称（可能为 None）
        gained: 本次新增命中数
    """
    if not weakness_name or not gained:
        return
    # 按名称查找对应的知识点
    kp = (
        await db.execute(
            select(DeckKnowledgePoint).where(DeckKnowledgePoint.name == weakness_name)
        )
    ).scalar_one_or_none()
    if kp is None:
        return
    # 每条新增命中记一条掌握度事件
    for _ in range(gained):
        await service.record_mastery_event(db, user_id, kp.id, "review_gym", True)


@router.get("/review-gym/session")
async def get_review_session(
    id: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> dict:
    """获取审查会话代码。

    - 传 id：返回指定会话（用于重做）
    - 不传 id：返回下一个未完成的会话

    Args:
        id: 会话 ID（可选查询参数）
    """
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
    """提交审查标记，返回判定结果。

    核心业务逻辑：
    1. 从数据库读取该会话的全部注入缺陷（实际缺陷）
    2. 调用 judge_marks 判定用户标记的命中/漏报/误报
    3. 已提交过的会话支持重做：只结算新增命中（防止刷经验）
    4. 结算：加经验（review 轴）、记录掌握度事件、写活动、写动态
    5. 每次提交后评估徽章

    幂等处理：已全中的重做请求直接返回旧判定（不再结算）。
    """
    session = await db.get(DeckReviewSession, body.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="审查关卡不存在")

    # 读取该会话的全部注入缺陷
    defect_rows = (
        await db.execute(
            select(DeckInjectedDefect).where(DeckInjectedDefect.session_id == session.id)
        )
    ).scalars().all()
    defects = [
        {"line": d.line, "type": d.type, "explanation": d.explanation} for d in defect_rows
    ]
    # Pydantic 模型转 dict
    marks = [m.model_dump() for m in body.marks]

    # 检查是否已有提交记录（同一会话 + 同一用户）
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
        # ── 复盘重做分支 ──
        # 重新判定，只按「新增命中」结算，防止刷经验
        verdict = service.judge_marks(defects, marks)
        gained = max(0, len(verdict["hits"]) - len(old.get("hits", [])))
        existing.marks = marks
        existing.verdict = verdict
        if gained:
            # 每次新增命中加 20 审查轴经验
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
        verdict["new_badges"] = await badges.evaluate_and_award(db, user.id)
        await db.commit()
        return verdict

    # ── 首次提交分支 ──
    verdict = service.judge_marks(defects, marks)
    # 写入审查尝试记录
    db.add(
        DeckReviewAttempt(
            user_id=user.id, session_id=session.id, marks=marks, verdict=verdict
        )
    )

    hits = len(verdict["hits"])
    # 结算：加能力轴经验（每命中 20 XP）、记录掌握度事件、更新活动
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
        # 全中奖励 5 智核
        await service.change_cores(db, user, 5, "代码审查全命中")
    # 徽章评估（每个提交端点统一在 commit 前调用）
    verdict["new_badges"] = await badges.evaluate_and_award(db, user.id)
    await db.commit()
    return verdict


# ── 复盘 /api/review ─────────────────────────────────────
# 复盘队列（Review Queue）：聚合用户所有待改进的项目。
# 三种来源：审查漏报/误报、竞技场未攻克挑战、弱知识点（费曼检验入口）。
# 用户在复盘队列中点击任一项目可直接跳转到对应模块进行针对性练习。

# 弱知识点阈值：p_l 低于 0.6 的知识点自动出现在复盘队列中
WEAK_MASTERY_THRESHOLD = 0.6


async def _build_review_queue(db: AsyncSession, user: User) -> list[dict]:
    """错题/失败项聚合：审查漏报、竞技场未攻克、弱知识点（费曼检验入口）。

    三种复盘来源：
    1. 审查关：有未命中（漏报或误报）的会话自动入队，全部命中后出队
    2. 竞技场：曾尝试但从未攻克（solved=0）的挑战自动入队
    3. 弱知识点：p_l < 0.6 的知识点，引导用户做费曼检验以巩固理解
    """
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
# 调试竞技场（Arena）：每日一道有 bug 的代码，用户在限时内让所有测试变绿。
# 后端用脚本式判定（后续换 Judge0），攻克后获得积分和 debug 轴经验。


@router.get("/arena/home")
async def get_arena_home(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> dict:
    """竞技场首页数据：用户段位信息 + 今日挑战 + 排行榜。

    返回三部分：
    - profile: 用户竞技场段位/积分/连胜
    - challenge: 今日挑战的代码、失败输出、时限等
    - leaderboard: 全站前 10 排行榜
    """
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
            "rank_delta": 0,  # 排名变化（预留字段，暂未实现）
            "win_streak": rating.win_streak,
        },
        "challenge": {
            "id": challenge.id,
            "title": challenge.title,
            "language": challenge.language,
            "code": challenge.code,              # 有 bug 的原始代码
            "failing_output": challenge.failing_output,  # 测试失败的输出
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
    """提交竞技场代码，返回判定结果。

    业务流程：
    1. 验证挑战存在
    2. 调用 judge_arena_code 判定（脚本式，后续换 Judge0）
    3. 写入试图记录
    4. 更新积分（攻克 +23）、连胜（攻克 +1，失败归零）
    5. 三连胜额外奖励 10 智核
    6. 加 debug 轴经验、写活动、写动态
    7. 评估徽章（传 ctx 保证连胜徽章能在提交后立即触发）
    """
    challenge = await db.get(DeckArenaChallenge, body.challenge_id)
    if challenge is None:
        raise HTTPException(status_code=404, detail="挑战不存在")

    # 判定用户代码
    result = service.judge_arena_code(body.code, challenge.failing_output)
    # 记录本次尝试（无论成败）
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
        # 攻克成功：加积分、连胜 +1、加 debug 轴经验
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
            # 三连胜额外奖励
            await service.change_cores(db, user, 10, "竞技场三连胜奖励")
    else:
        # 未攻克：连胜归零
        rating.win_streak = 0
    # 记录今日活动
    await service.touch_activity(
        db, user.id, minutes=max(1, challenge.time_limit_sec // 60), correct=result["passed"]
    )
    # 传 ctx 确保「连战连捷」徽章能基于刚更新的连胜数触发
    result["new_badges"] = await badges.evaluate_and_award(
        db, user.id, ctx={"arena_win_streak": rating.win_streak}
    )
    await db.commit()
    return result


# ── 苏格拉底导师 /api/tutor ──────────────────────────────
# 苏格拉底导师（Tutor）：AI 对话式编程教学，两种模式：
# 1. socratic（苏格拉底追问）：用户问问题，导师用层层追问引导思考
# 2. feynman（费曼检验）：用户讲解知识点，导师评估理解程度并点评
# 每次追问/点评消耗 2 智核（TUTOR_COST）。


def _message_out(m: DeckTutorMessage) -> dict:
    """将数据库消息行转换为前端消息格式。

    Args:
        m: 导师消息 ORM 对象

    Returns:
        前端渲染所需的消息格式（id/role/mode/text）
    """
    return {"id": m.id, "role": m.role, "mode": m.mode, "text": m.text}


@router.get("/tutor/state")
async def get_tutor_state(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> dict:
    """获取导师对话状态：最近 20 条历史消息、余额、建议话题。

    前端在进入导师页时调用，恢复上次的对话历史。
    """
    # 取最近 20 条消息（倒序取，再反转为正序返回给前端）
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
        "messages": [_message_out(m) for m in reversed(messages)],  # 反转为正序
        "suggested_topics": await _weakest_kp_names(db, user.id, 3),
    }


@router.post("/tutor/message")
async def send_tutor_message(
    body: TutorMessageIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> dict:
    """发送消息给苏格拉底导师，返回 AI 回复。

    业务规则：
    - 余额不足时返回提示消息，不扣费（200 而非 4xx，用户体验更好）
    - 余额充足时调用 socratic_reply 生成回复并扣费
    - 每条用户消息都会写入数据库（保留对话历史）
    """
    # 1. 写入用户消息
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


# ── 费曼检验会话 ─────────────────────────────────────
# 费曼检验的会话存储在内存中（FEYNMAN_SESSIONS 字典），
# 这是因为开发阶段不需要跨进程/跨重启持久化。
# 生产环境应换为 Redis 或其他共享存储。

# 费曼会话（内存态，dev 后端够用）：session_id → {user_id, kp_id, created_at}
FEYNMAN_SESSIONS: dict[str, dict] = {}


@router.post("/tutor/feynman")
async def start_feynman(
    body: FeynmanStartIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> dict:
    """开始费曼检验：创建会话，返回开场白。

    流程：
    1. 验证知识点存在
    2. 创建内存会话（session_id = uuid4）
    3. 生成费曼检验开场白（要求用户像教新手一样讲解）
    4. 返回 session_id 供前端 check 时使用
    """
    # 验证知识点
    kp = (
        await db.execute(
            select(DeckKnowledgePoint).where(DeckKnowledgePoint.name == body.topic)
        )
    ).scalar_one_or_none()
    if kp is None:
        raise HTTPException(status_code=404, detail="知识点不存在")

    # 创建内存会话（不落库，dev 后端够用）
    session_id = str(uuid4())
    FEYNMAN_SESSIONS[session_id] = {
        "user_id": user.id,
        "kp_id": kp.id,
        "created_at": datetime.now(),
    }
    # 生成开场白
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
    """提交费曼讲解，返回评分和点评。

    业务流程：
    1. 验证会话有效性（session + user_id 匹配）
    2. 调用 mastery.feynman_grade 评分（比对该知识点的 key_points）
    3. 记录掌握度事件（correct = grade != "待加强"）
    4. 扣智核、写活动、生成点评
    5. 评估徽章

    返回 mastery_update 让前端展示 p_l 变化动画。
    """
    # 验证会话（防止跨用户访问）
    session = FEYNMAN_SESSIONS.get(body.session_id)
    if session is None or session["user_id"] != user.id:
        raise HTTPException(status_code=404, detail="费曼会话不存在或已过期")
    kp = await db.get(DeckKnowledgePoint, session["kp_id"])
    if kp is None:
        raise HTTPException(status_code=404, detail="知识点不存在")

    # 调用 mastery 模块评分（比对 key_points 覆盖情况）
    result = mastery.feynman_grade(body.text, kp.key_points)
    grade = result["grade"]
    verdict = service.feynman_feedback(grade, result["covered"], result["missed"])

    # 记录掌握度事件（合格 = 优秀/良好，correct=True）
    p_l_before, p_l_after, level = await service.record_mastery_event(
        db, user.id, kp.id, "feynman", correct=grade != "待加强", grade=grade
    )

    # 扣费 + 写活动
    await service.change_cores(db, user, -service.TUTOR_COST, "费曼检验 · 点评")
    await service.touch_activity(db, user.id, minutes=3)
    reply = DeckTutorMessage(
        user_id=user.id, role="tutor", mode="feynman", text=verdict, grade=grade
    )
    db.add(reply)
    # 评估徽章（费曼检验可能解锁 "以教为学" "讲明白了" 等）
    new_badges = await badges.evaluate_and_award(db, user.id)
    await db.commit()
    await db.refresh(reply)
    return {
        "message": _message_out(reply),
        "cores_balance": user.cores,
        "grade": grade,
        "mastery_update": {  # 前端用此数据播放 p_l 变化动画
            "kp_name": kp.name,
            "p_l_before": p_l_before,
            "p_l_after": p_l_after,
            "level": level,
        },
        "new_badges": new_badges,
    }


# ── 基本功认证 /api/certification ───────────────────────
# 基本功认证（Certification）：限时考试，无 AI 辅助，通过后获得可分享的证书。
# 考试分两类：placement（定级测试，初始化能力图谱）和普通试卷（获得认证）。


def _cert_record(c: DeckCertification) -> dict:
    """将认证 ORM 记录转为前端格式。

    Args:
        c: 认证记录 ORM 对象

    Returns:
        前端证书展示所需字段
    """
    return {
        "topic": c.topic,
        "level": c.level,
        "date": c.created_at.date().isoformat(),
        "score": c.score,
        "verify_code": c.verify_code,
    }


async def _exam_info(db: AsyncSession, exam: DeckCertExam) -> dict:
    """获取试卷的基本信息（不含题目和答案）。

    Args:
        db: 异步数据库会话
        exam: 试卷 ORM 对象

    Returns:
        试卷摘要信息
    """
    # 统计该试卷的题目总数
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
    """认证首页：已获证书列表 + 可用试卷 + 冷却时间 + 徽章墙。

    返回四部分：
    - has_placement: 是否已定级
    - certified: 已获证书列表（按时间倒序）
    - available_exams: 可用试卷列表（排除 placement，定级测试只在未定级时显示）
    - next_available_days: 距下次可考天数（None=从未考过，0=可以考）
    - badges: 全量 17 枚徽章状态
    """
    certs = (
        await db.execute(
            select(DeckCertification)
            .where(DeckCertification.user_id == user.id)
            .order_by(DeckCertification.created_at.desc())
        )
    ).scalars().all()
    # 排除 placement（定级测试不是正式认证）
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
        "badges": await badges.list_badges(db, user.id),
    }


@router.get("/certification/exam")
async def get_certification_exam(
    id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> dict:
    """获取试卷详情（题目列表，绝不含答案）。

    安全设计：返回的题目只包含 prompt/options/starter_code，
    绝不包含 answer_correct 或 answer_includes 字段。
    判分在后端完成，前端只负责收集用户答案。
    """
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
            {  # 绝不下发答案字段 —— 安全边界
                "id": q.qid,
                "kind": q.kind,
                "prompt": q.prompt,
                # 仅当字段非空时才包含（避免下发 None）
                **({"options": q.options} if q.options else {}),
                **({"starter_code": q.starter_code} if q.starter_code else {}),
            }
            for q in questions
        ],
    }


# 定级测试及格线：≥60 分视为「已掌握起点」，所有知识点的定级事件记为 correct=True
PLACEMENT_PASS_SCORE = 60  # 定级测试达到该分数，定级事件记为「已掌握起点」


def _cert_level(score: int) -> str:
    """根据得分返回认证等级。

    等级划分：
    - ≥90：精通
    - ≥75：熟练
    - <75：合格

    Args:
        score: 0~100 的考试得分

    Returns:
        等级名称
    """
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
    """提交认证考试答案，返回分数和证书。

    这是训练舱最复杂的提交端点，处理两种考试类型：
    - placement（定级测试）：初始化能力图谱，不颁发证书
    - 普通试卷：通过后颁发证书 + 20 智核奖励

    业务流程：
    1. 逐题判分（mcq/编程题分别处理）
    2. 计算总分
    3. 定级测试：为所有知识点写定级事件 + 初始化三轴经验
    4. 普通试卷：通过后创建证书 + 奖励智核 + 加 implement 轴经验
    5. 写活动 + 评估徽章
    """
    exam = await db.get(DeckCertExam, body.exam_id)
    if exam is None:
        raise HTTPException(status_code=404, detail="试卷不存在")
    questions = (
        await db.execute(
            select(DeckCertQuestion).where(DeckCertQuestion.exam_id == exam.id)
        )
    ).scalars().all()
    # 构建 qid -> 题目 的快速查找映射
    q_map = {q.qid: q for q in questions}

    # 逐题判分
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
    # 计算总分（百分比，四舍五入）
    total = len(questions) or 1
    score = round(sum(1 for p in per_question if p["correct"]) / total * 100)

    certificate = None
    if exam.id == "placement":
        # ── 定级测试分支 ──
        # 每道知识点写一条定级事件（事件是事实源，p_l/level 由重放推导）
        # correct 沿用原 score 语义：60 分及以上视为掌握起点
        placement_correct = score >= PLACEMENT_PASS_SCORE
        kps = (await db.execute(select(DeckKnowledgePoint))).scalars().all()
        for kp in kps:
            # 所有知识点统一标记（placement_correct 决定初始 p_l 的高低）
            await service.record_mastery_event(
                db, user.id, kp.id, "placement", placement_correct
            )
        # 根据得分计算三轴初始等级和经验
        base_level = 1 + min(4, score // 25)  # 等级范围 1~5
        for axis, level in (
            ("review", base_level),
            ("implement", base_level),
            ("debug", max(1, base_level - 1)),  # debug 轴低一级（调试更难）
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
        passed = False  # 定级测试不算「通过」
    else:
        # ── 普通试卷分支 ──
        passed = score >= exam.pass_score
        if passed:
            # 创建认证记录
            record = DeckCertification(
                user_id=user.id,
                topic=exam.topic,
                level=_cert_level(score),
                score=score,
                verify_code=service.new_verify_code("WP-PTR"),  # 生成防伪校验码
            )
            db.add(record)
            await db.flush()  # 让 created_at 等默认值生效后再读
            # 通过奖励：20 智核 + 40 implement 轴经验
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

    # 记录今日活动
    await service.touch_activity(db, user.id, minutes=exam.time_limit_min,
                                 correct=sum(1 for p in per_question if p["correct"]))
    # 评估徽章：placement 不传 cert_score（保持端点判定与 backfill ctx=None 一致）
    badge_ctx = None if exam.id == "placement" else {"cert_score": score}
    new_badges = await badges.evaluate_and_award(db, user.id, ctx=badge_ctx)
    await db.commit()
    return {
        "score": score,
        "passed": passed,
        "certificate": certificate,
        "per_question": per_question,  # 每题的正误详情
        "new_badges": new_badges,
    }
