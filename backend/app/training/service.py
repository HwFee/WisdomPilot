"""训练舱领域服务：判定逻辑、主任务分发、能力轴、智核经济。

判定规则与 frontend/lib/api/deck/mock/ 下的纯函数一一对应
（mock 即本服务的参考实现；cert code 题后续应换 Judge0 真判分）。

模块职责
========
本文件是训练舱（Deck）后端的**领域服务层**，承载了所有核心业务逻辑：
1. **能力轴系统**：审阅 / 调试 / 实现三大维度，每轴有等级和经验值（XP）。
2. **掌握度事件读写**：基于事件源模型（Event Sourcing），写入事件后重算 p_l/level 缓存。
3. **智核经济**：唯一的虚拟货币变动途径，每次收支都记账（DeckCoreTransaction）。
4. **每日活动与动态**：记录每日练习时长/题数，生成用户动态 Feed。
5. **段位系统**：竞技场 ELO 积分到段位名称的映射。
6. **各模块判定函数**：代码审查、竞技场代码、导师回复、费曼检验、认证判分——
   这些纯函数与前端 mock 一一对应，确保前后端判定逻辑一致。
7. **连续天数与冷却**：计算连续学习天数、认证冷却天数、审查室今日完成数。

设计要点
========
- 判定函数（judge_marks / judge_arena_code / judge_cert_answer 等）都是**纯函数**，
  无副作用、无 IO，方便单元测试，且前端 mock 可以直接复制。
- 掌握度写操作一律走 ``record_mastery_event``：先写事件（事实源），再重算缓存。
- 智核变动一律走 ``change_cores``：保证余额不为负、同时写交易流水。
"""

import random
import re
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.training import mastery
from app.training.models import (
    DeckAbilityAxis,
    DeckArenaRating,
    DeckCertification,
    DeckCoreTransaction,
    DeckDailyActivity,
    DeckFeedEvent,
    DeckKnowledgePoint,
    DeckMasteryEvent,
    DeckReviewAttempt,
    DeckUserMastery,
)
from app.auth.models import User

# 北京时区（UTC+8）：训练舱的「自然日」以北京时间为准，
# 例如连续学习天数、今日已用智核等都按 BJT 的日期来切分。
BJT = timezone(timedelta(hours=8))  # 自然日按北京时间

# 三大能力轴的 key 列表，顺序固定（review → debug → implement）
AXES = ("review", "debug", "implement")
# 能力轴中文标签，用于前端展示
AXIS_LABELS = {"review": "审阅", "debug": "调试", "implement": "实现"}
# 导师每问一次消耗的智核数（苏格拉底导师 & 费曼检验共用）
TUTOR_COST = 2
# 认证考试冷却天数：通过/参加一次后需等待 N 天才能再考
CERT_COOLDOWN_DAYS = 3


def today_bjt() -> date:
    """返回北京时间（BJT）的当天日期。

    用于按自然日聚合统计数据（今日完成数、今日已用智核等）。
    所有「今日」相关的判定都应调用此函数而非 ``datetime.now().date()``，
    保证时区一致。
    """
    return datetime.now(BJT).date()


# ── 能力轴 ──────────────────────────────────────────────
# 能力轴是训练舱对用户编程能力的三维评估体系：
# - review（审阅）：代码审查能力，在复习舱中练习
# - debug（调试）：调试排错能力，在竞技场中练习
# - implement（实现）：实现/讲解能力，在苏格拉底导师和认证中练习
# 每轴有等级（level）和经验值（xp），400 xp 升一级。


def axis_level(xp: int) -> int:
    """根据经验值计算能力轴等级。

    每 400 经验值升一级，等级从 1 开始（0 xp = LV.1）。

    Args:
        xp: 该轴的累计经验值

    Returns:
        能力轴等级（≥1 的整数）
    """
    return 1 + xp // 400


async def get_axes(db: AsyncSession, user_id: str) -> list[dict]:
    """获取用户三大能力轴的完整状态（等级、经验、短板知识点）。

    该函数聚合两份数据：
    1. ``DeckAbilityAxis`` 表：每轴的累计经验值
    2. ``DeckUserMastery`` + ``DeckKnowledgePoint`` 联查：找到每轴下掌握度最低的知识点

    返回的数据结构直接用于前端能力图谱（ability-map）和 Dashboard 展示。

    Args:
        db: 异步数据库会话
        user_id: 用户 ID

    Returns:
        能力轴列表，每轴包含 key/label/level/xp_current/xp_next/weakest_focus。
        weakest_focus 是该轴下 p_l 最低的知识点名称，用于引导用户补短板。
    """
    # 查询用户三条能力轴记录（review/debug/implement）
    rows = (
        await db.execute(select(DeckAbilityAxis).where(DeckAbilityAxis.user_id == user_id))
    ).scalars().all()
    # 构建 axis -> xp 的映射，方便后续按轴取值
    xp_map = {r.axis: r.xp for r in rows}

    # 每轴短板：p_l 最低的知识点
    # 联查掌握度缓存表和知识点表，找到每个知识点属于哪个轴及其 p_l
    mastery_rows = (
        await db.execute(
            select(DeckUserMastery, DeckKnowledgePoint)
            .join(DeckKnowledgePoint, DeckUserMastery.kp_id == DeckKnowledgePoint.id)
            .where(DeckUserMastery.user_id == user_id)
        )
    ).all()
    # 按轴分组，找出每轴 p_l 最低的知识点名称
    weakest: dict[str, str] = {}
    for axis in AXES:
        axis_rows = [(m.p_l, kp.name) for m, kp in mastery_rows if kp.axis == axis]
        if axis_rows:
            # min 取 p_l 最小的元组，[1] 取知识点名称
            weakest[axis] = min(axis_rows)[1]

    # 组装三轴的完整返回结构
    axes = []
    for axis in AXES:
        xp = xp_map.get(axis, 0)
        level = axis_level(xp)
        axes.append(
            {
                "key": axis,
                "label": AXIS_LABELS[axis],
                "level": level,
                "xp_current": xp,
                "xp_next": level * 400,  # 升到下一级所需的总 xp
                "weakest_focus": weakest.get(axis),
            }
        )
    return axes


async def add_axis_xp(db: AsyncSession, user_id: str, axis: str, amount: int) -> None:
    """给用户某个能力轴增加经验值（不存在则自动创建）。

    在提交判定后调用：审查命中、竞技场攻克、认证通过等场景都会给对应轴加经验。

    Args:
        db: 异步数据库会话
        user_id: 用户 ID
        axis: 能力轴 key（review/debug/implement）
        amount: 增加的经验值（正整数）
    """
    # 尝试按复合主键获取已有记录
    row = await db.get(DeckAbilityAxis, {"user_id": user_id, "axis": axis})
    if row is None:
        # 首次获得该轴经验：创建记录并加入 session
        row = DeckAbilityAxis(user_id=user_id, axis=axis, xp=0)
        db.add(row)
    row.xp += amount


async def has_placement(db: AsyncSession, user_id: str) -> bool:
    """判断用户是否已完成定级测试。

    定级测试是用户进入训练舱后的第一步：通过一场考试来初始化各知识点的掌握度。
    判定依据是 ``DeckUserMastery`` 表中是否有记录（定级时会为所有知识点写入初始事件）。

    Args:
        db: 异步数据库会话
        user_id: 用户 ID

    Returns:
        True 表示已定级，False 表示未定级（Dashboard 主任务会返回 null）
    """
    # 统计该用户的掌握度缓存记录数，>0 即已定级
    count = await db.scalar(
        select(func.count()).select_from(DeckUserMastery).where(
            DeckUserMastery.user_id == user_id
        )
    )
    return bool(count and count > 0)


async def _mastery_events_of(
    db: AsyncSession, user_id: str, kp_id: str
) -> list[mastery.MasteryEvent]:
    """读出某用户某知识点的全部事件（事实源），转成引擎输入。

    掌握度采用事件源模型：``DeckMasteryEvent`` 是不可变的事实表，
    每次答题/练习都会追加一条事件。本函数把数据库行转换为
    ``mastery.MasteryEvent`` 数据类，供 HLR 重算引擎使用。

    Args:
        db: 异步数据库会话
        user_id: 用户 ID
        kp_id: 知识点 ID

    Returns:
        按时间排序的掌握度事件列表（MasteryEvent 数据类）
    """
    rows = (
        await db.execute(
            select(DeckMasteryEvent)
            .where(DeckMasteryEvent.user_id == user_id, DeckMasteryEvent.kp_id == kp_id)
            .order_by(DeckMasteryEvent.created_at)
        )
    ).scalars().all()
    return [
        mastery.MasteryEvent(created_at=r.created_at, correct=bool(r.correct), source=r.source)
        for r in rows
    ]


async def record_mastery_event(
    db: AsyncSession,
    user_id: str,
    kp_id: str,
    source: str,
    correct: bool,
    grade: str | None = None,
    hints_used: int = 0,
    latency_ms: int | None = None,
) -> tuple[float | None, float, str]:
    """写入一条掌握度事件并重算 p_l/level 缓存。返回 (重算前 p_l, 重算后 p_l, 等级)

    这是掌握度系统的**唯一写入口**。流程：
    1. 读取重算前的缓存 p_l（可能为 None，表示首次记录）
    2. 追加一条事件到 ``DeckMasteryEvent`` 事实表
    3. flush 让新事件进入后续查询可见
    4. 重放该知识点全部事件，用 HLR 模型重算 p_l 和等级
    5. 更新（或创建）``DeckUserMastery`` 缓存行

    Args:
        db: 异步数据库会话
        user_id: 用户 ID
        kp_id: 知识点 ID
        source: 事件来源（placement/review_gym/arena/feynman）
        correct: 本次是否答对
        grade: 评级（仅费曼检验使用：优秀/良好/待加强）
        hints_used: 使用提示次数（预留字段）
        latency_ms: 答题耗时毫秒（预留字段）

    Returns:
        元组 (p_l_before, p_l_after, level)：
        - p_l_before: 重算前的 p_l（首次为 None）
        - p_l_after: 重算后的 p_l（0~1 之间的浮点数）
        - level: 重算后的等级名称（初识/熟悉/熟练/精通）
    """
    # 1. 读取重算前的缓存值（用于前端展示 p_l 变化动画）
    row = await db.get(DeckUserMastery, {"user_id": user_id, "kp_id": kp_id})
    p_l_before = row.p_l if row is not None else None
    # 2. 追加事件到事实表（不可变，只增不改）
    db.add(
        DeckMasteryEvent(
            user_id=user_id,
            kp_id=kp_id,
            source=source,
            correct=correct,
            grade=grade,
            hints_used=hints_used,
            latency_ms=latency_ms,
        )
    )
    # 3. flush 让新事件对后续查询可见（不 commit，保持事务原子性）
    await db.flush()  # 让新事件进入后续查询

    # 4. 重放全部事件，用 HLR 模型重算
    events = await _mastery_events_of(db, user_id, kp_id)
    now = datetime.now(timezone.utc)
    p_l_after = mastery.recall_probability(events, now)
    level = mastery.mastery_level(events, now)
    # 5. 更新缓存读模型
    if row is None:
        row = DeckUserMastery(user_id=user_id, kp_id=kp_id, p_l=p_l_after, level=level)
        db.add(row)
    else:
        row.p_l = p_l_after
        row.level = level
    return p_l_before, p_l_after, level


async def mastery_trends(db: AsyncSession, user_id: str) -> dict[str, str]:
    """各知识点 7 天趋势（无事件的 kp 不出现，调用方按 flat 兜底）

    趋势判定逻辑在 ``mastery.compute_trend`` 中实现，基于最近 7 天的事件
    计算「上升 / 持平 / 下降」。

    Args:
        db: 异步数据库会话
        user_id: 用户 ID

    Returns:
        kp_id -> 趋势字符串（"up" / "flat" / "down"）的映射。
        只包含有事件的知识点，无事件的不会出现在 dict 中。
    """
    # 一次性查出用户所有掌握度事件
    rows = (
        await db.execute(
            select(DeckMasteryEvent).where(DeckMasteryEvent.user_id == user_id)
        )
    ).scalars().all()
    # 按知识点分组，转换为 MasteryEvent 列表
    by_kp: dict[str, list[mastery.MasteryEvent]] = {}
    for r in rows:
        by_kp.setdefault(r.kp_id, []).append(
            mastery.MasteryEvent(created_at=r.created_at, correct=bool(r.correct), source=r.source)
        )
    now = datetime.now(timezone.utc)
    # 对每个知识点的事件列表计算趋势
    return {kp_id: mastery.compute_trend(events, now) for kp_id, events in by_kp.items()}


# ── 智核经济（唯一变动途径）──────────────────────────────
# 智核（Cores）是训练舱的虚拟货币，用于：
# - 苏格拉底导师追问（每次 -2）
# - 费曼检验点评（每次 -2）
# 通过认证、解锁徽章、竞技场连胜等可获得智核。
# 所有智核变动必须走 change_cores，保证余额不为负且留有交易流水。


async def change_cores(
    db: AsyncSession, user: User, delta: int, reason: str
) -> int:
    """增减智核并记账，返回新余额。余额不会变负。

    智核经济的核心约束：
    1. 余额下限为 0（不会出现负数）
    2. 每次变动都写一条 ``DeckCoreTransaction`` 流水记录
    3. 流水记录变动后的余额快照，方便审计

    Args:
        db: 异步数据库会话
        user: 用户 ORM 对象（直接修改其 cores 属性）
        delta: 变动量（正数=获得，负数=消耗）
        reason: 变动原因（如"通过认证 · 指针"）

    Returns:
        变动后的新余额（≥0）
    """
    # max(0, ...) 确保余额不为负：即使 delta 是大负数也只扣到 0
    new_balance = max(0, user.cores + delta)
    user.cores = new_balance
    # 写交易流水，balance_after 是快照，用于历史审计和前端账单展示
    db.add(
        DeckCoreTransaction(
            user_id=user.id, delta=delta, reason=reason, balance_after=new_balance
        )
    )
    return new_balance


async def today_cores_used(db: AsyncSession, user_id: str) -> int:
    """统计用户今日（BJT 自然日）已消耗的智核总数。

    只统计 delta < 0 的记录（消耗），返回其绝对值之和。
    用于 Dashboard 展示「今日已用 X 次」和导师页面的余额提示。

    Args:
        db: 异步数据库会话
        user_id: 用户 ID

    Returns:
        今日已消耗智核数（非负整数）
    """
    # coalesce 确保无记录时返回 0 而非 None
    # func.date() 取日期部分与今天 BJT 日期比较
    total = await db.scalar(
        select(func.coalesce(func.sum(DeckCoreTransaction.delta), 0)).where(
            DeckCoreTransaction.user_id == user_id,
            DeckCoreTransaction.delta < 0,
            func.date(DeckCoreTransaction.created_at) == today_bjt().isoformat(),
        )
    )
    # abs 因为 delta 是负数，返回正数给前端展示
    return abs(int(total or 0))


# ── 活动 / 动态 ─────────────────────────────────────────
# 每日活动（DeckDailyActivity）：按天聚合用户的练习时长和题数，
# 用于 Dashboard 的 7 天节奏图和连续学习天数计算。
# 动态 Feed（DeckFeedEvent）：记录用户的关键操作日志（完成审查、通过认证等），
# 以 segments 结构化文案形式存储，前端直接渲染。


async def touch_activity(
    db: AsyncSession, user_id: str, *, minutes: int = 0, correct: int = 0
) -> None:
    """更新用户今日活动记录（不存在则创建）。

    每次提交判定后调用，累加今日练习时长和题数。
    用「upsert」模式：先查今日记录，没有就创建，有就累加。

    Args:
        db: 异步数据库会话
        user_id: 用户 ID
        minutes: 本次练习耗时分钟数（累加到今日总时长）
        correct: 本次答对题数（累加到今日正确数）
    """
    # 按复合主键 (user_id, day) 查今日记录
    row = await db.get(DeckDailyActivity, {"user_id": user_id, "day": today_bjt()})
    if row is None:
        # 今日首条活动：创建记录
        row = DeckDailyActivity(user_id=user_id, day=today_bjt(), minutes=0, exercises=0, correct=0)
        db.add(row)
    # 累加今日数据
    row.minutes += minutes
    row.exercises += 1
    row.correct += correct


async def add_feed(db: AsyncSession, user_id: str, kind: str, segments: list[dict]) -> None:
    """写入一条用户动态（Feed 事件）。

    动态采用 segments 结构化文案：每个 segment 是 {"t": "文本", "tone": "语气"}，
    前端按 tone 渲染不同颜色/样式（strong=高亮, ok=绿色, bad=红色）。

    Args:
        db: 异步数据库会话
        user_id: 用户 ID
        kind: 动态类型（review/arena/cert/badge/tutor）
        segments: 结构化文案片段列表
    """
    db.add(DeckFeedEvent(user_id=user_id, kind=kind, payload={"segments": segments}))


def feed_time_label(created_at: datetime) -> str:
    """将动态时间戳转换为人类友好的时间标签。

    规则：
    - 今天：显示 HH:MM（如 "14:30"）
    - 昨天：显示 "昨天"
    - 更早：显示 "N天前"

    注意：created_at 在数据库中以 UTC 存储，这里转换为 BJT 后计算天数差。

    Args:
        created_at: UTC 时间戳

    Returns:
        友好的时间标签字符串
    """
    now = datetime.now(BJT)
    # 数据库存储的是 UTC naive datetime，需要加上 UTC tzinfo 再转 BJT
    created = created_at.replace(tzinfo=timezone.utc).astimezone(BJT)
    days = (now.date() - created.date()).days
    if days == 0:
        return created.strftime("%H:%M")
    if days == 1:
        return "昨天"
    return f"{days}天前"


# ── 段位 ────────────────────────────────────────────────
# 竞技场段位系统：基于 ELO 积分的段位映射。
# 初始积分 1200（白银），通过攻克挑战获得 score_delta 提升积分。

# 段位表：按积分阈值从高到低排列，匹配第一个 >= threshold 的即返回对应段位名。
TIER_TABLE = [
    (2400, "王者"),
    (2100, "钻石"),
    (1800, "铂金 II"),
    (1500, "黄金"),
    (1200, "白银"),
    (0, "青铜"),
]


def tier_of(rating: int) -> str:
    """根据竞技场积分返回段位名称。

    遍历段位表，返回第一个阈值 ≤ rating 的段位名。

    Args:
        rating: 竞技场 ELO 积分

    Returns:
        段位名称（青铜/白银/黄金/铂金 II/钻石/王者）
    """
    for threshold, name in TIER_TABLE:
        if rating >= threshold:
            return name
    return "青铜"


async def get_or_create_rating(db: AsyncSession, user_id: str) -> DeckArenaRating:
    """获取或创建用户的竞技场积分记录。

    新用户初始积分 1200（白银段位），连胜数 0。

    Args:
        db: 异步数据库会话
        user_id: 用户 ID

    Returns:
        用户的竞技场积分记录 ORM 对象
    """
    row = await db.get(DeckArenaRating, user_id)
    if row is None:
        # 首次进入竞技场：创建初始积分记录（1200 = 白银起点）
        row = DeckArenaRating(user_id=user_id, rating=1200, win_streak=0)
        db.add(row)
        await db.flush()
    return row


async def week_rank(db: AsyncSession, rating: int) -> int:
    """计算用户本周排名（基于积分高于自己的人数 + 1）。

    排名 = 积分比你高的人数 + 1。

    Args:
        db: 异步数据库会话
        rating: 用户的当前竞技场积分

    Returns:
        排名（≥1 的整数，1 表示第一名）
    """
    # 统计积分高于当前用户的人数
    higher = await db.scalar(
        select(func.count()).select_from(DeckArenaRating).where(DeckArenaRating.rating > rating)
    )
    return int(higher or 0) + 1


# ── 审查判定（对齐 mock judgeMarks）──────────────────────
# 代码审查室的核心判定逻辑：用户标记的缺陷 vs 实际注入的缺陷。
# 判定规则与前端 mock（frontend/lib/api/deck/mock/）完全一致，
# 确保前端预览和后端提交结果一致。


def judge_marks(defects: list[dict], marks: list[dict]) -> dict:
    """代码审查判定：比对用户标记与实际缺陷。

    判定规则：
    1. 逐个缺陷寻找匹配的用户标记（行号差 ≤1 且类型相同）
    2. 匹配的缺陷 = hits（命中）
    3. 未匹配的缺陷 = missed（漏报）
    4. 未匹配的标记 = false_alarms（误报）
    5. 每个标记只能匹配一个缺陷（用 used 集合去重）

    评分公式：score = 命中率 × 70 + 精确率 × 30（满分 100）

    Args:
        defects: 实际注入的缺陷列表，每项含 line/type/explanation
        marks: 用户标记列表，每项含 line/type

    Returns:
        判定结果 dict，包含：
        - hits: 命中的缺陷列表
        - missed: 漏报的缺陷列表
        - false_alarms: 误报的标记列表
        - score: 0~100 的整数评分
        - accuracy: 命中率（0~1，命中数/标记数）
    """
    hits, missed, false_alarms = [], [], []
    # used 记录已匹配的标记索引，防止一个标记匹配多个缺陷
    used: set[int] = set()
    for defect in defects:
        # 寻找第一个未使用且行号差 ≤1、类型相同的标记
        hit_index = next(
            (
                i
                for i, m in enumerate(marks)
                if i not in used
                and abs(m["line"] - defect["line"]) <= 1
                and m["type"] == defect["type"]
            ),
            None,
        )
        if hit_index is not None:
            hits.append(defect)
            used.add(hit_index)
        else:
            missed.append(defect)
    # 未被使用的标记都是误报
    false_alarms = [m for i, m in enumerate(marks) if i not in used]

    # 精确率 = 1 - 误报率（无标记时精确率为 1.0）
    precision = 1.0 if not marks else 1 - len(false_alarms) / len(marks)
    # 总分 = 命中率 × 70 + 精确率 × 30
    score = round(len(hits) / len(defects) * 70 + precision * 30)
    # 准确率 = 命中数 / 标记数（无标记时为 0）
    accuracy = 0.0 if not marks else len(hits) / len(marks)
    return {"hits": hits, "missed": missed, "false_alarms": false_alarms,
            "score": score, "accuracy": accuracy}


# ── 竞技场判定（对齐 mock judgeArenaCode；后续换 Judge0）──
# 竞技场代码判定：目前用规则匹配（字符串检测），后续应替换为 Judge0 真实判分。
# 规则与前端 mock 完全一致，保证开发阶段前后端体验统一。


# 全部通过的模拟测试输出（5/5 passed）
ARENA_SOLVED_OUTPUT = """$ pytest test_median.py -v
test_median.py::test_odd            PASSED   [ 20%]
test_median.py::test_single         PASSED   [ 40%]
test_median.py::test_even           PASSED   [ 60%]
test_median.py::test_even_negative  PASSED   [ 80%]
test_median.py::test_even_unsorted  PASSED   [100%]

======================== 5 passed in 0.08s ========================"""

# 部分通过的模拟测试输出（3/5 passed，偶数中位数索引有问题）
ARENA_PARTIAL_OUTPUT = """$ pytest test_median.py -v
test_median.py::test_even           FAILED   assert 5.0 == 4.5
test_median.py::test_even_negative  FAILED   assert -4.0 == -4.5

=================== 3 passed, 2 failed in 0.11s ===================
右中位索引还有问题：偶数个时中间两个是 nums[mid-1] 和 nums[mid]。"""


def judge_arena_code(code: str, failing_output: str) -> dict:
    """竞技场代码判定（规则匹配版，后续换 Judge0）。

    当前实现用字符串匹配检测用户代码是否修正了关键错误：
    1. 检测是否包含 ``lo=mid-1``（正确的循环边界修正）
    2. 检测是否包含 ``nums[lo]+nums[mid])``（正确的中位数计算）
    两个规则都满足 = 全通过；只满足循环 = 部分通过；都不满足 = 失败。

    Args:
        code: 用户提交的代码
        failing_output: 原始失败输出（全失败时返回给用户）

    Returns:
        判定结果 dict，包含：
        - passed: 通过的测试数
        - total: 总测试数
        - output: 模拟的测试输出文本
        - solved: 是否全部通过
        - score_delta: 积分变动（全通过 +23，否则 0）
    """
    # 去除所有空白字符，使规则匹配不受格式影响
    normalized = re.sub(r"\s+", "", code)
    # 规则1：循环边界修正（lo = mid - 1 而非 lo = mid）
    rule_loop = "lo=mid-1" in normalized
    # 规则2：中位数计算修正（偶数个时取中间两个的平均值）
    rule_index = "nums[lo]+nums[mid])" in normalized
    if rule_loop and rule_index:
        # 两条规则都满足：全部通过
        return {"passed": 5, "total": 5, "output": ARENA_SOLVED_OUTPUT,
                "solved": True, "score_delta": 23}
    if rule_loop:
        # 只修正了循环边界：部分通过（3/5）
        return {"passed": 3, "total": 5, "output": ARENA_PARTIAL_OUTPUT,
                "solved": False, "score_delta": 0}
    # 都没修正：返回原始失败输出
    return {"passed": 2, "total": 5, "output": failing_output,
            "solved": False, "score_delta": 0}


# ── 导师脚本（后续换 LLM 追问）───────────────────────────
# 苏格拉底导师目前的回复是脚本式的（关键词匹配 + 通用追问轮替），
# 后续会替换为 LLM 追问。脚本式回复保证开发阶段无需 AI 调用即可测试交互流程。

# 关键词触发的定向追问：当用户消息包含特定关键词时，返回针对性的苏格拉底式追问。
KEYWORD_PROBES = [
    (["指针", "pointer", "内存"],
     "先别急着写代码。你觉得 p 指向的内存被 free 之后，p 这个变量本身变成了什么？它还「认识」原来那块地址吗？"),
    (["递归"],
     "如果递归没有出口，调用栈一层层压下去会发生什么？你能描述第 1000 层时栈里的状态吗？"),
    (["边界", "空", "0"],
     "好，那我们把输入推到极限：空列表、单个元素、全部相同——你的代码在这三种情况下分别会走到哪一行？"),
    (["排序"],
     "你说它排对了。那我问你：当数组里有两个相同的元素时，它们各自会落在哪个位置？一个都不多、一个都不少吗？"),
    (["循环", "死循环"],
     "循环退出靠的是哪个条件？你能找到一个输入，让这个条件永远不满足吗？"),
]

# 通用追问列表：无关键词匹配时按对话轮次轮替使用，引导用户深入思考。
GENERIC_PROBES = [
    "在你给出答案之前——你觉得这段代码最可能在哪一类输入上出错？",
    "你说的「正确」具体指什么？我们怎么验证它？",
    "如果输入规模放大 1000 倍，你的方案还成立吗？哪一步先撑不住？",
    "试着构造一个让自己代码出错的反例。最小的那个是什么？",
    "如果让你给这段代码写三条测试用例，你会先写哪三条？为什么？",
]


def socratic_reply(text: str, history_len: int) -> str:
    """苏格拉底导师脚本式回复。

    回复策略：
    1. 优先匹配关键词：用户消息包含特定关键词时返回定向追问
    2. 无匹配时按对话历史长度轮替使用通用追问

    Args:
        text: 用户发送的消息文本
        history_len: 用户的历史消息总数（用于轮替通用追问）

    Returns:
        导师的回复文本
    """
    # 优先：关键词匹配
    for keys, reply in KEYWORD_PROBES:
        if any(k in text for k in keys):
            return reply
    # 兜底：按历史长度取模轮替通用追问
    return GENERIC_PROBES[history_len % len(GENERIC_PROBES)]


def feynman_opening(topic: str) -> str:
    """费曼检验开场白：引导用户用自己的话讲解知识点。

    费曼检验核心理念：如果你不能用简单的话把一个概念讲清楚，
    说明你还没有真正理解它。

    Args:
        topic: 知识点名称

    Returns:
        开场白文本，要求用户像教新手一样讲解
    """
    return f"好，「{topic}」。用你自己的话讲给我听——假装你在教一个完全不懂编程的人。不许用术语搪塞，讲到他能复述为止。"


def feynman_feedback(grade: str, covered: list[str], missed: list[str]) -> str:
    """按评分结果生成点评：点明已覆盖/缺失的要点

    根据费曼检验的评级结果生成不同深度的点评：
    - 优秀：肯定理解深度，追问更深层的证明能力
    - 良好：指出主干清晰但有关键要点遗漏，要求补全
    - 待加强：指出讲解离「教会别人」还有差距，引导回到最基本的问题

    Args:
        grade: 评级（优秀/良好/待加强）
        covered: 用户讲解中已覆盖的要点列表
        missed: 用户讲解中遗漏的要点列表

    Returns:
        点评文本，包含具体的改进方向
    """
    # 拼接遗漏要点提示（有遗漏时才显示）
    missed_hint = f"没讲到的要点：{'、'.join(missed)}。" if missed else ""
    if grade == "优秀":
        return (
            f"讲得有因有果，要点也都覆盖了——这说明你真的内化了。"
            f"只追一个盲区：如果让你向「会编程但不信你的人」证明它，你会用什么证据？"
        )
    if grade == "良好":
        return (
            f"主干讲清楚了。{missed_hint}"
            f"补上这些再讲一遍？记住：说「是什么」不算懂，说清「为什么必须这样」才算。"
        )
    return (
        f"停——这段讲述离「教会别人」还有距离。{missed_hint}"
        f"回到最小的一步：这个知识点要解决什么问题？不解决会怎样？"
        f"讲的时候带上因果（因为/所以）和一个具体例子（比如/当）。"
    )


# ── 认证判分（对齐 mock judgeExam）───────────────────────
# 认证考试（Certification）的题目判分逻辑，支持两种题型：
# 1. mcq（选择题）：答案完全匹配
# 2. 编程题：去除空白后判断是否包含所有关键片段（includes）


def judge_cert_answer(kind: str, answer: str, correct: str | None, includes: list | None) -> bool:
    """认证题目判分：判断用户答案是否正确。

    判分规则因题型而异：
    - mcq（单选题）：答案字符串与正确选项完全相等
    - 编程题：去除所有空白后，判断是否包含所有 key includes 片段

    Args:
        kind: 题型（mcq 或编程题）
        answer: 用户提交的答案
        correct: 正确答案（仅 mcq 使用）
        includes: 关键代码片段列表（仅编程题使用，答案需全部包含才算对）

    Returns:
        True 表示答案正确，False 表示错误
    """
    if kind == "mcq":
        # 选择题：直接字符串匹配（correct or "" 防止 None）
        return answer == (correct or "")
    # 编程题：去除空白后，逐一检查每个关键片段是否被包含
    normalized = re.sub(r"\s+", "", answer)
    return all(re.sub(r"\s+", "", frag) in normalized for frag in (includes or []))


def new_verify_code(topic_prefix: str) -> str:
    """生成认证凭证校验码。

    校验码格式：{前缀}-{4位随机十六进制}，例如 "WP-PTR-A3F2"。
    用于认证证书的防伪和分享验证。

    Args:
        topic_prefix: 主题前缀（如 "WP-PTR" 表示指针主题）

    Returns:
        校验码字符串
    """
    # 从十六进制字符集中随机选取 4 位，生成唯一校验码
    return f"{topic_prefix}-{''.join(random.choices('0123456789ABCDEF', k=4))}"


# ── 连续训练天数 ─────────────────────────────────────────
# 连续训练天数计算，用于 Dashboard 展示和徽章条件判定。
# 基于 DeckDailyActivity 表的 day 字段（BJT 日期），从今天往前回溯。


async def streak_days(db: AsyncSession, user_id: str) -> int:
    """计算用户连续学习天数（当日计入）。

    算法：从用户最近活动日期列表（最多取 60 天）中，从今天（BJT）开始
    逐日回溯，找到最长的连续天数。有间隔（day < expected）时立即终止。

    Args:
        db: 异步数据库会话
        user_id: 用户 ID

    Returns:
        连续天数（≥0 的整数，0 表示今天还没有活动）
    """
    # 按日期倒序取最近 60 天内的所有活动日
    rows = (
        await db.execute(
            select(DeckDailyActivity.day)
            .where(DeckDailyActivity.user_id == user_id)
            .order_by(DeckDailyActivity.day.desc())
            .limit(60)
        )
    ).scalars().all()
    if not rows:
        return 0
    streak = 0
    expected = today_bjt()  # 从今天开始回溯
    for day in rows:
        if day == expected:
            # 连续无间断：计数 +1，预期日期往前推一天
            streak += 1
            expected -= timedelta(days=1)
        elif day < expected:
            # 发生间断（day 比 expected 更早），停止计数
            break
    return streak


async def next_cert_available_days(db: AsyncSession, user_id: str) -> int | None:
    """计算距离下次可参加认证考试的剩余天数。

    规则：上次认证后有 3 天冷却期（CERT_COOLDOWN_DAYS）。
    返回 None 表示从未考过（无冷却限制），0 表示今天就可以考。

    Args:
        db: 异步数据库会话
        user_id: 用户 ID

    Returns:
        剩余冷却天数（None 表示无限制，0 表示冷却已过）
    """
    # 查找最近一次认证记录的时间
    last = (
        await db.execute(
            select(DeckCertification.created_at)
            .where(DeckCertification.user_id == user_id)
            .order_by(DeckCertification.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if last is None:
        return None  # 从未考过，无冷却
    # 计算距上次认证已过天数
    elapsed = (today_bjt() - last.replace(tzinfo=timezone.utc).astimezone(BJT).date()).days
    # 冷却期 - 已过天数 = 还需等待的天数（最低 0）
    return max(0, CERT_COOLDOWN_DAYS - elapsed)


async def attempts_today(db: AsyncSession, user_id: str) -> tuple[int, float]:
    """审查室今日完成数与平均准确率

    用于 Dashboard 展示的模块 stat-line 数据。

    Args:
        db: 异步数据库会话
        user_id: 用户 ID

    Returns:
        元组 (今日完成数, 今日平均准确率)：
        - 今日完成数：整数，今日提交的审查次数
        - 平均准确率：0~1 的浮点数
    """
    rows = (
        await db.execute(
            select(DeckReviewAttempt.verdict).where(
                DeckReviewAttempt.user_id == user_id,
                # 按 BJT 日期筛选今日记录
                func.date(DeckReviewAttempt.created_at) == today_bjt().isoformat(),
            )
        )
    ).scalars().all()
    if not rows:
        return 0, 0.0
    # 统计今日所有审查的平均准确率
    avg = sum(v.get("accuracy", 0) for v in rows) / len(rows)
    return len(rows), avg
