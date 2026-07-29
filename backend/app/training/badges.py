"""徽章系统：定义清单（常量，不入库）+ 事实聚合 + 幂等评估引擎。

判定风格参照 mastery.py：规则是纯函数 `check(facts, ctx) -> bool`，不各自查库；
`collect_facts` 一次性聚合全部事实表，`evaluate_and_award` 在提交端点事务内
commit 前调用，已解锁的跳过（deck_user_badges 复合唯一约束兜底）。

`ctx` 是本次提交的瞬时上下文（dict，回填时为 None），目前支持：
- arena_win_streak: 本次竞技场提交后的当前连胜（历史峰值不落库，只能靠当前值触发）
- cert_score: 本次认证考试得分

模块职责
========
徽章系统是训练舱的游戏化激励层，共 17 枚徽章分三级（铜/银/金），
总奖励 165 智核。核心设计原则：

1. **定义在代码中，不入库**：``BADGES`` 列表直接定义所有徽章和规则，
   不需要建 badge 表，新增徽章就是新增一行 BadgeDef。
2. **事实聚合 + 纯函数规则**：``collect_facts`` 一次性查询所有相关表，
   组装成 ``BadgeFacts`` 数据类；每个徽章的 ``check`` 是纯函数，
   只读 facts + ctx，不做 IO。
3. **幂等评估**：``evaluate_and_award`` 先查已解锁的，再跑规则，
   只写入新达成的。复合唯一约束 (user_id, badge_id) 兜底。
4. **分层奖励**：铜 +5、银 +10、金 +20 智核。
5. **隐藏徽章**：hidden=True 的徽章，未解锁时在前端徽章墙脱敏为 "???"，
   解锁后才显示真名和条件。这是一种「惊喜」设计。
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
# 三级徽章的 tier 标识和对应的智核奖励额
TIER_BRONZE = "bronze"
TIER_SILVER = "silver"
TIER_GOLD = "gold"

BRONZE_REWARD = 5
SILVER_REWARD = 10
GOLD_REWARD = 20

# ── 判定阈值：徽章 check 函数使用的业务常量 ──
NIGHT_OWL_END_HOUR = 5          # 夜猫子：北京时间 00:00–05:00（不含 5 点）
PERFECT_ACCURACY = 1.0          # 复习舱单次判定全命中（accuracy = 1.0）
PERFECT_SCORE = 100             # 认证满分
ARENA_STREAK_TARGET = 3         # 竞技场三连胜
STREAK_3_DAYS = 3
STREAK_7_DAYS = 7
MULTI_TOPIC_TARGET = 2          # 博览：认证覆盖主题数
FEYNMAN_TOP_GRADE = "优秀"
FEYNMAN_PASS_GRADES = frozenset({"良好", "优秀"})  # 费曼检验「合格」的两档评级
CERT_LEVEL_ADEPT = "熟练"
CERT_LEVEL_MASTER = "精通"

HIDDEN_PLACEHOLDER = "???"      # 隐藏徽章未解锁时的脱敏文案


# ── 事实与规则 ──────────────────────────────────────────
# 徽章系统的两层核心数据结构：
# 1. BadgeFacts：聚合后的全部事实（只读，规则函数入参）
# 2. BadgeDef：徽章定义（id/等级/名称/条件/奖励/判定规则）


@dataclass(frozen=True)
class BadgeFacts:
    """一次评估所需的全部事实（collect_facts 聚合，规则只读它）。

    这是一个不可变数据类（frozen=True），确保在评估过程中不会被意外修改。
    所有字段都是「已发生的累计事实」——统计值或布尔标记，
    不包含瞬时上下文（瞬时上下文走 ctx 参数）。

    Attributes:
        has_placement: 是否已完成定级测试
        cert_count: 已通过的认证次数
        cert_levels: 已获得的所有认证等级集合（如 {"合格", "熟练"}）
        cert_topic_count: 已认证的不同主题数量
        cert_max_score: 历史最高认证得分
        review_attempt_count: 审查室提交总次数
        review_has_perfect: 是否曾有全命中的审查（accuracy = 1.0）
        arena_win_count: 竞技场攻克（solved=true）总次数
        arena_win_streak: 当前连胜数（落库值，不含未提交的当前局）
        feynman_pass_count: 费曼检验合格次数（良好/优秀）
        feynman_best_grade: 费曼检验最高评级（None 表示从未参与）
        streak_days: 连续学习天数（含当日）
        night_event_count: 凌晨（0-5点）活动事件数
        topic_all_mastered: 是否有一个主题的所有知识点都达「精通」
        has_comeback: 是否有「先错后对」的 comeback 事件
    """

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
    """单枚徽章的完整定义（代码级常量，不入数据库）。

    check 是判定规则的纯函数，签名为 (BadgeFacts, dict|None) -> bool。
    - 第一个参数是聚合事实（由 collect_facts 提供）
    - 第二个参数是瞬时上下文（ctx），用于「本次达到」类条件
      （如竞技场连胜需 ctx["arena_win_streak"]，因为提交前的 rating 尚未更新）

    Attributes:
        id: 徽章唯一标识（如 "placement-done"）
        tier: 等级（bronze/silver/gold），决定奖励金额（5/10/20）
        title: 徽章中文名称（如 "知己知彼"）
        hidden: 是否为隐藏徽章（未解锁时脱敏为 "???"）
        condition_desc: 解锁条件中文描述
        reward_cores: 解锁时奖励的智核数
        check: 判定函数，纯函数，无副作用
    """
    id: str
    tier: str
    title: str
    hidden: bool
    condition_desc: str
    reward_cores: int
    # 判定函数：(facts, ctx) -> bool
    # ctx 是本次提交的瞬时上下文，回填脚本使用时为 None
    check: Callable[[BadgeFacts, dict | None], bool]


def _ctx_int(ctx: dict | None, key: str) -> int:
    """读瞬时上下文里的整数，缺失/回填时按 0 处理。

    瞬时上下文（ctx）是本次提交带来的实时数据，不落库。
    - arena_win_streak：提交后 rating 更新了但事务未提交，需从 ctx 读取
    - cert_score：本次认证考试得分

    Args:
        ctx: 瞬时上下文字典，回填脚本传 None
        key: 要读取的键名

    Returns:
        对应的整数值，缺失时返回 0
    """
    if not ctx:
        return 0
    return int(ctx.get(key) or 0)


# ── 徽章清单（17 枚，全量定义在代码中，不入库）────────────
# 每个 BadgeDef 是一枚徽章，按等级分组（铜 → 银 → 金）。
# check 是 lambda 纯函数：(facts, ctx) -> bool
# 实测时注意：arena-streak-3 和 perfect-score 还依赖 ctx 参数，
# 因为它们需要在"本次提交"的瞬时状态下判定。
BADGES: list[BadgeDef] = [
    # ── 铜（+5）── 入门激励，条件宽松 ──
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
    # ── 银（+10）── 进阶成就，需要一定的投入 ──
    BadgeDef("cert-adept", TIER_SILVER, "游刃有余", False,
             "获得首个「熟练」级认证", SILVER_REWARD,
             lambda facts, ctx: CERT_LEVEL_ADEPT in facts.cert_levels
             or CERT_LEVEL_MASTER in facts.cert_levels),  # 精通自动满足熟练
    BadgeDef("cert-multi-topic", TIER_SILVER, "博览", False,
             "认证覆盖 2 个不同主题", SILVER_REWARD,
             lambda facts, ctx: facts.cert_topic_count >= MULTI_TOPIC_TARGET),
    BadgeDef("review-perfect", TIER_SILVER, "弹无虚发", False,
             "复习舱单次判定全命中", SILVER_REWARD,
             lambda facts, ctx: facts.review_has_perfect),
    BadgeDef("arena-streak-3", TIER_SILVER, "连战连捷", False,
             "竞技场三连胜", SILVER_REWARD,
             # 连胜从两个来源读取：facts 里是数据库中的历史值，ctx 里是本次提交的当前值
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
             # 满分从两个来源读取：历史最高分（facts）或本次得分（ctx）
             lambda facts, ctx: facts.cert_max_score >= PERFECT_SCORE
             or _ctx_int(ctx, "cert_score") >= PERFECT_SCORE),
    # ── 金（+20）── 顶尖荣誉，需要深度投入 ──
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

# 快速索引：badge_id -> BadgeDef，O(1) 查找
BADGE_BY_ID: dict[str, BadgeDef] = {b.id: b for b in BADGES}


# ── 事实聚合 ────────────────────────────────────────────
# 各 _xxx_facts 函数从不同事实表中聚合数据，最终由 collect_facts 汇总。
# 设计原则：每个函数只查询自己需要的事实表，规则函数不各自查库。
# 在事务内调用时，SQLAlchemy 的 autoflush 会自动包含本次新写入的行。


async def _cert_facts(db: AsyncSession, user_id: str) -> tuple[int, frozenset, int, int]:
    """查询认证（Certification）相关事实。

    Returns:
        元组 (认证次数, 已获等级集合, 覆盖主题数, 历史最高分)
    """
    rows = (
        await db.execute(
            select(DeckCertification).where(DeckCertification.user_id == user_id)
        )
    ).scalars().all()
    # 从所有认证记录中提取去重的等级集合
    levels = frozenset(r.level for r in rows)
    # 统计不同主题数（用 set 去重 topic）
    topic_count = len({r.topic for r in rows})
    # 取最高分，无记录时 default=0
    max_score = max((r.score for r in rows), default=0)
    return len(rows), levels, topic_count, max_score


async def _review_facts(db: AsyncSession, user_id: str) -> tuple[int, bool]:
    """查询审查室（Review Gym）相关事实。

    Returns:
        元组 (审查提交总次数, 是否曾有全命中)
    """
    verdicts = (
        await db.execute(
            select(DeckReviewAttempt.verdict).where(DeckReviewAttempt.user_id == user_id)
        )
    ).scalars().all()
    # 遍历所有判定结果，检查是否有准确率为 1.0 的
    has_perfect = any(v.get("accuracy") == PERFECT_ACCURACY for v in verdicts)
    return len(verdicts), has_perfect


async def _arena_facts(db: AsyncSession, user_id: str) -> tuple[int, int]:
    """查询竞技场（Arena）相关事实。

    Returns:
        元组 (攻克总次数, 当前连胜数)
    """
    attempts = (
        await db.execute(
            select(DeckArenaAttempt.solved).where(DeckArenaAttempt.user_id == user_id)
        )
    ).scalars().all()
    # 连胜数从 DeckArenaRating 读取（落库的当前值）
    rating = await db.get(DeckArenaRating, user_id)
    win_streak = rating.win_streak if rating else 0
    # 统计 solved=1（成功攻克）的次数
    return sum(1 for s in attempts if s), win_streak


async def _feynman_facts(db: AsyncSession, user_id: str) -> tuple[int, str | None]:
    """查询费曼检验（Feynman）相关事实。

    从导师消息表中筛选 mode="feynman" 且有 grade 的记录。

    Returns:
        元组 (合格次数, 最高评级)
    """
    grades = (
        await db.execute(
            select(DeckTutorMessage.grade).where(
                DeckTutorMessage.user_id == user_id,
                DeckTutorMessage.mode == "feynman",
                DeckTutorMessage.grade.is_not(None),  # 排除无评级的记录（如开场白）
            )
        )
    ).scalars().all()
    # 统计「良好」或「优秀」的次数
    pass_count = sum(1 for g in grades if g in FEYNMAN_PASS_GRADES)
    # 最佳评级按优先级：优秀 > 良好 > 其他
    best = FEYNMAN_TOP_GRADE if FEYNMAN_TOP_GRADE in grades else (
        "良好" if "良好" in grades else (grades[0] if grades else None)
    )
    return pass_count, best


def _scan_events(events: list[DeckMasteryEvent]) -> tuple[int, bool]:
    """扫一遍掌握度事件：夜间（北京时间 0–5 点）事件数 + comeback 序列判定。

    - 夜间事件：事件发生时间在 00:00-04:59（BJT）之间的计数
    - comeback 序列：先答错（非 review_gym 来源），后在 review_gym 中答对同一知识点

    注意：events 必须按 created_at 排序后才能正确检测 comeback 序列。

    Args:
        events: 按时间升序排列的掌握度事件列表

    Returns:
        元组 (夜间事件数, 是否有 comeback)
    """
    night_count = 0
    wrong_seen: set[str] = set()  # 记录曾答错的知识点 ID
    has_comeback = False
    # 按时间排序后顺序扫描
    for e in sorted(events, key=lambda x: x.created_at):
        # 将 UTC 时间转为 BJT，提取小时数判断是否夜间
        hour = e.created_at.replace(tzinfo=timezone.utc).astimezone(service.BJT).hour
        if hour < NIGHT_OWL_END_HOUR:
            night_count += 1
        if not e.correct:
            # 答错了：记录知识点 ID
            wrong_seen.add(e.kp_id)
        elif e.source == "review_gym" and e.kp_id in wrong_seen:
            # review_gym 中答对 + 之前曾答错 = comeback
            has_comeback = True
    return night_count, has_comeback


async def _topic_all_mastered(db: AsyncSession, user_id: str) -> bool:
    """是否存在某个主题（知识点 category）其全部知识点都达「精通」。

    按知识点的 category 字段分组，检查是否有任意一组的所有知识点 level 都是「精通」。

    Args:
        db: 异步数据库会话
        user_id: 用户 ID

    Returns:
        True 表示至少有一个主题全部精通
    """
    # 取所有知识点定义
    kps = (await db.execute(select(DeckKnowledgePoint))).scalars().all()
    # 取该用户的掌握度缓存（level 字段）
    mastery_rows = (
        await db.execute(
            select(DeckUserMastery).where(DeckUserMastery.user_id == user_id)
        )
    ).scalars().all()
    # 构建 kp_id -> level 的快速查找映射
    level_by_kp = {m.kp_id: m.level for m in mastery_rows}
    # 按 category 分组知识点
    by_topic: dict[str, list[str]] = {}
    for kp in kps:
        by_topic.setdefault(kp.category, []).append(kp.id)
    # 检查任意一组是否全部精通
    return any(
        all(level_by_kp.get(kp_id) == CERT_LEVEL_MASTER for kp_id in kp_ids)
        for kp_ids in by_topic.values()
    )


async def collect_facts(db: AsyncSession, user_id: str) -> BadgeFacts:
    """集中聚合各事实表（规则不各自查库）。在提交事务内调用时靠 autoflush 看到本次写入。

    这是所有徽章评估的**唯一数据入口**。一次查询，所有规则共享。
    在提交端点的事务中、commit 之前调用时，SQLAlchemy autoflush 会
    自动把本次新写入的行包含进查询结果。

    Args:
        db: 异步数据库会话
        user_id: 用户 ID

    Returns:
        聚合后的 BadgeFacts 数据类实例
    """
    # 分别从各事实表聚合数据
    cert_count, cert_levels, cert_topic_count, cert_max_score = await _cert_facts(db, user_id)
    review_count, review_has_perfect = await _review_facts(db, user_id)
    arena_wins, arena_win_streak = await _arena_facts(db, user_id)
    feynman_pass, feynman_best = await _feynman_facts(db, user_id)
    # 掌握度事件：全量拉取后扫描夜间事件和 comeback
    events = (
        await db.execute(
            select(DeckMasteryEvent).where(DeckMasteryEvent.user_id == user_id)
        )
    ).scalars().all()
    night_count, has_comeback = _scan_events(list(events))
    # 组装不可变的 BadgeFacts 实例
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
# evaluate_and_award 是徽章系统的核心入口，在每次提交端点事务内 commit 前调用。
# list_badges 用于认证页徽章墙展示。


def _unlock_out(badge: BadgeDef) -> dict:
    """将徽章定义转换为前端所需的解锁响应格式。

    只包含前端需要展示的字段（id/tier/title/reward_cores），
    不暴露 check 函数等内部细节。

    Args:
        badge: 徽章定义

    Returns:
        前端 new_badges 数组中的单个元素
    """
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

    执行流程：
    1. 获取用户对象（不存在则直接返回空列表）
    2. 收集事实（collect_facts）
    3. 查询已解锁徽章 ID（幂等关键）
    4. 遍历全部 17 枚徽章，跳过已解锁或不满足条件的
    5. 新达成：写入 DeckUserBadge 行 → 奖励智核 → 写动态
    6. 返回本次新解锁的列表

    Args:
        db: 异步数据库会话
        user_id: 用户 ID
        ctx: 瞬时上下文，本次提交带来的实时数据（None 用于回填脚本）

    Returns:
        本次新解锁的徽章列表（每个元素含 id/tier/title/reward_cores）
    """
    # 1. 用户存在性检查
    user = await db.get(User, user_id)
    if user is None:
        return []
    # 2. 一次性聚合所有事实
    facts = await collect_facts(db, user_id)
    # 3. 查询已解锁的徽章 ID 集合（幂等关键：已解锁的跳过）
    unlocked_ids = set(
        (
            await db.execute(
                select(DeckUserBadge.badge_id).where(DeckUserBadge.user_id == user_id)
            )
        ).scalars().all()
    )

    # 4. 遍历全部 17 枚徽章，检查条件
    new_badges: list[dict] = []
    for badge in BADGES:
        # 已解锁 或 不满足条件 → 跳过
        if badge.id in unlocked_ids or not badge.check(facts, ctx):
            continue
        # 5. 新达成：写入解锁记录
        db.add(DeckUserBadge(user_id=user_id, badge_id=badge.id))
        # 发放智核奖励（统一的变动途径，保证记账）
        await service.change_cores(
            db, user, badge.reward_cores, f"解锁徽章 · {badge.title}"
        )
        # 写入动态 Feed
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
        # 收集本次新解锁的徽章（用于前端播动画）
        new_badges.append(_unlock_out(badge))
    return new_badges


async def list_badges(db: AsyncSession, user_id: str) -> list[dict]:
    """徽章墙：全量 17 枚 + 解锁状态。hidden 且未解锁时 title/desc 脱敏为 ???

    用于认证页的徽章墙展示。设计要点：
    - 全量返回 17 枚徽章，每枚标注 unlocked 状态和 unlocked_at 时间
    - hidden 徽章未解锁时：title 和 condition_desc 显示为 "???"，制造惊喜感
    - hidden 徽章已解锁后：正常显示名称和条件

    Args:
        db: 异步数据库会话
        user_id: 用户 ID

    Returns:
        徽章列表，每项包含 id/tier/title/condition_desc/hidden/unlocked/reward_cores/unlocked_at
    """
    # 查询该用户已解锁的徽章记录
    rows = (
        await db.execute(
            select(DeckUserBadge).where(DeckUserBadge.user_id == user_id)
        )
    ).scalars().all()
    # 构建 badge_id -> unlocked_at 的映射
    unlocked_at_by_id = {r.badge_id: r.unlocked_at for r in rows}

    infos: list[dict] = []
    for badge in BADGES:
        unlocked_at = unlocked_at_by_id.get(badge.id)
        unlocked = unlocked_at is not None
        # mask 条件：隐藏徽章 且 未解锁 → 脱敏
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
                # unlocked_at 从数据库读取的是 UTC naive datetime，
                # 用 isoformat() 序列化为 ISO 8601 字符串
                "unlocked_at": unlocked_at.isoformat() if unlocked else None,
            }
        )
    return infos
