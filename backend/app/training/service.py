"""训练舱领域服务：判定逻辑、主任务分发、能力轴、智核经济。

判定规则与 frontend/lib/api/deck/mock/ 下的纯函数一一对应
（mock 即本服务的参考实现；竞技场与认证 code 题已接入 Judge0 真判分，
Judge0 不可用时降级回关键字匹配，见 judge_arena_code_submit /
judge_cert_code_answer）。

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

import json
import logging
import random
import re
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.service import AIService, ai_service
# Judge0 判题基础设施：业务服务层 + HTTP 客户端 + 语言 ID 常量
from app.services.judge0 import (
    Judge0Client,
    Judge0Service,
    LANGUAGE_C,
    LANGUAGE_PYTHON,
)
from app.training import mastery
from app.training.models import (
    DeckAbilityAxis,
    DeckArenaAttempt,
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

logger = logging.getLogger(__name__)

# 北京时区（UTC+8）：训练舱的「自然日」以北京时间为准，
# 例如连续学习天数、今日已用智核等都按 BJT 的日期来切分。
BJT = timezone(timedelta(hours=8))  # 自然日按北京时间

# 三大能力轴的 key 列表，顺序固定（review → debug → implement）
AXES = ("review", "debug", "implement")
# 能力轴中文标签，用于前端展示
AXIS_LABELS = {"review": "审阅", "debug": "调试", "implement": "实现"}
# 训练指纹轴代码（§3.5 P-11 路径唯一性标识）：审阅→R / 调试→D / 实现→I
FINGERPRINT_AXIS_CODES = {"review": "R", "debug": "D", "implement": "I"}
# 导师每问一次消耗的智核数（苏格拉底导师 & 费曼检验共用）
TUTOR_COST = 2
# 认证考试冷却天数：通过/参加一次后需等待 N 天才能再考
CERT_COOLDOWN_DAYS = 3

# ── P-09 / P-10 训练轨迹（时间线 + 能力演化对比）──────────
# 定级 feed 事件的分段文案标记（旧格式 payload 解析分数用）
PLACEMENT_FEED_MARK = "完成定级测试"
# 定级分数段正则：匹配 "100 分" / "80分"（定级动态的 strong 分段文案）
PLACEMENT_SCORE_RE = re.compile(r"^(\d+)\s*分$")
# 时间线条目类型（与前端 TimelineKind 同源，snake_case 契约）
TIMELINE_PLACEMENT = "placement"       # 定级画像
TIMELINE_AXIS_UPGRADE = "axis_upgrade"  # 能力轴升级
TIMELINE_MASTERY = "mastery"           # 知识点达到熟练/精通
TIMELINE_CERT = "cert"                 # 认证通过
# 时间线只展示达到这两个掌握等级的知识点里程碑（初识/熟悉不构成里程碑）
TIMELINE_MASTERY_LEVELS = ("熟练", "精通")
# 各模块单次活动的轴经验（与各 submit 端点结算一致，用于重放轴升级）：
# review=20×命中缺陷数 / debug=竞技场攻克固定 23 / implement=认证通过 40
XP_REVIEW_PER_HIT = 20
XP_ARENA_SOLVED = 23
XP_CERT_PASS = 40
# 每升一级所需经验（与 axis_level 公式同源，400 xp 升一级）
XP_PER_LEVEL = 400
# 定级初始经验的档内偏移（§8：xp = (level-1)×400 + 200，落点在档内 2/3 处）
PLACEMENT_XP_OFFSET = 200


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

    每 XP_PER_LEVEL（400）经验值升一级，等级从 1 开始（0 xp = LV.1）。

    Args:
        xp: 该轴的累计经验值

    Returns:
        能力轴等级（≥1 的整数）
    """
    return 1 + xp // XP_PER_LEVEL


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


def training_fingerprint(axes: list[dict]) -> str:
    """根据三轴等级生成训练指纹短码（§3.5 P-11），如 R3-D1-I4。

    格式固定为 ``R{审阅等级}-D{调试等级}-I{实现等级}``（例：审阅 LV.3、
    调试 LV.1、实现 LV.4 → "R3-D1-I4"）。只暴露三轴等级的粗粒度信息，
    不含任何具体弱点知识点（隐私约束 4），防止被用于逆向推测用户水平。

    Args:
        axes: get_axes 返回的三轴列表（每项含 key/level）

    Returns:
        形如 "R3-D1-I4" 的指纹短码；缺失的轴按 LV.1（未定级默认）计。
    """
    level_by_axis = {a.get("key"): a.get("level", 1) for a in axes}
    return "-".join(
        f"{FINGERPRINT_AXIS_CODES[axis]}{level_by_axis.get(axis, 1)}"
        for axis in AXES
    )


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


# ── 间隔重复调度 & 难度自适应（§3.5 P-06 / P-08）──────────
# P-06：到期复习调度。掌握度（HLR 回忆概率 p_l）低于阈值的知识点视为
# 「记忆正在消退」，优先生成费曼复习任务。阈值与复盘队列 knowledge 项
# （router.py 的 WEAK_MASTERY_THRESHOLD）共用同一常量，保证口径一致。
# 0.6 的含义（与掌握度等级"熟练"门槛 P_PROFICIENT 同值）：回忆概率跌破
# 六成意味着约 h×log2(5/3) 天没练，再拖就会滑向"初识"档，此时复习性价比最高。
DUE_MASTERY_THRESHOLD = 0.6

# P-08：难度自适应的统计窗口与升降档阈值（审查室/竞技场共用判定骨架）。
# 窗口 3 次：足够小以快速响应表现变化，又足够大以滤除单次偶然
# （与竞技场"三连胜奖励"的口径对齐）。
REVIEW_ADAPT_WINDOW = 3   # 审查室：统计最近 N 次提交
ARENA_ADAPT_WINDOW = 3    # 竞技场：统计最近 N 次提交
# 升档 0.9：窗口内几乎全对（审查 accuracy=命中/标记，≥0.9 意味着基本无误报漏报；
# 竞技场攻克率 ≥0.9 约等于 3 连过），当前难度已无法带来训练增量 → +1 档。
REVIEW_ADAPT_UP = 0.9     # 审查室升档阈值
ARENA_ADAPT_UP = 0.9      # 竞技场升档阈值
# 降档 0.4：窗口内半数以上表现不佳，说明难度超出能力 → -1 档，防止挫败流失。
REVIEW_ADAPT_DOWN = 0.4   # 审查室降档阈值
ARENA_ADAPT_DOWN = 0.4    # 竞技场降档阈值


def difficulty_delta(
    mean_ratio: float | None, up_threshold: float, down_threshold: float
) -> int:
    """近期表现均值 → 难度档位偏移（P-08 纯函数，确定性可测）。

    规则（阈值由调用方传入模块级常量，本函数只做档位判定）：
    - 均值 ≥ up_threshold → +1（升档：当前难度已无挑战）
    - 均值 ≤ down_threshold → -1（降档：当前难度超出能力）
    - 其余 → 0（保持不变）
    - None（无记录）→ 0（冷启动不扰动难度）

    Args:
        mean_ratio: 近期表现均值（0~1），None 表示无记录
        up_threshold: 升档阈值（如 REVIEW_ADAPT_UP / ARENA_ADAPT_UP）
        down_threshold: 降档阈值（如 REVIEW_ADAPT_DOWN / ARENA_ADAPT_DOWN）

    Returns:
        -1 / 0 / 1。
    """
    if mean_ratio is None:
        return 0
    if mean_ratio >= up_threshold:
        return 1
    if mean_ratio <= down_threshold:
        return -1
    return 0


async def recent_review_accuracy(db: AsyncSession, user_id: str) -> float | None:
    """近 REVIEW_ADAPT_WINDOW 次审查提交的平均准确率（取 verdict.accuracy）。

    P-08 审查室难度自适应数据源：deck_review_attempts.verdict["accuracy"]。
    不足窗口时按已有记录求均值（响应更灵敏）；完全无记录时返回 None。

    Args:
        db: 异步数据库会话
        user_id: 用户 ID

    Returns:
        平均准确率（0~1）；无任何提交记录时返回 None。
    """
    rows = (
        await db.execute(
            select(DeckReviewAttempt.verdict)
            .where(DeckReviewAttempt.user_id == user_id)
            .order_by(DeckReviewAttempt.created_at.desc())
            .limit(REVIEW_ADAPT_WINDOW)
        )
    ).scalars().all()
    if not rows:
        return None
    return sum(v.get("accuracy", 0.0) for v in rows) / len(rows)


async def recent_arena_win_rate(db: AsyncSession, user_id: str) -> float | None:
    """近 ARENA_ADAPT_WINDOW 次竞技场提交的攻克率（solved=1 占比）。

    P-08 竞技场难度自适应数据源：deck_arena_attempts.solved。
    不足窗口时按已有记录求均值；完全无记录时返回 None。

    Args:
        db: 异步数据库会话
        user_id: 用户 ID

    Returns:
        攻克率（0~1）；无任何提交记录时返回 None。
    """
    rows = (
        await db.execute(
            select(DeckArenaAttempt.solved)
            .where(DeckArenaAttempt.user_id == user_id)
            .order_by(DeckArenaAttempt.created_at.desc())
            .limit(ARENA_ADAPT_WINDOW)
        )
    ).scalars().all()
    if not rows:
        return None
    return sum(1 for s in rows if s) / len(rows)


async def due_for_review(db: AsyncSession, user_id: str) -> list[dict]:
    """返回到期需复习的知识点（§3.5 P-06 间隔重复调度）。

    判定：掌握度缓存 p_l 低于 DUE_MASTERY_THRESHOLD（0.6）即视为
    「记忆正在消退」，需要复习。按 p_l 升序返回（最危险的在最前），
    只读缓存读模型，不触碰事件表（事件写入仍走 record_mastery_event）。

    Args:
        db: 异步数据库会话
        user_id: 用户 ID

    Returns:
        [{"name": 知识点名称, "p_l": 回忆概率}, ...]；无到期知识点返回空列表。
    """
    rows = (
        await db.execute(
            select(DeckKnowledgePoint.name, DeckUserMastery.p_l)
            .join(DeckUserMastery, DeckUserMastery.kp_id == DeckKnowledgePoint.id)
            .where(
                DeckUserMastery.user_id == user_id,
                DeckUserMastery.p_l < DUE_MASTERY_THRESHOLD,
            )
            .order_by(DeckUserMastery.p_l.asc())
        )
    ).all()
    return [{"name": name, "p_l": p_l} for name, p_l in rows]


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


async def add_feed(
    db: AsyncSession, user_id: str, kind: str, segments: list[dict], *, extra: dict | None = None
) -> None:
    """写入一条用户动态（Feed 事件）。

    动态采用 segments 结构化文案：每个 segment 是 {"t": "文本", "tone": "语气"}，
    前端按 tone 渲染不同颜色/样式（strong=高亮, ok=绿色, bad=红色）。
    extra 为可选的结构化载荷（如定级分数），合并进 payload 供后端复算
    （P-09/P-10 读它重建轨迹），不影响前端渲染（前端只读 segments）。

    Args:
        db: 异步数据库会话
        user_id: 用户 ID
        kind: 动态类型（review/arena/cert/badge/tutor）
        segments: 结构化文案片段列表
        extra: 附加结构化数据（可选，合并进 payload）
    """
    payload: dict = {"segments": segments}
    if extra:
        payload.update(extra)
    db.add(DeckFeedEvent(user_id=user_id, kind=kind, payload=payload))


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


# ── P-09 / P-10 训练轨迹（时间线 + 能力演化对比）────────────
# 数据源全部来自既有事实表（deck_feed_events / deck_mastery_events /
# deck_review_attempts / deck_arena_attempts / deck_certifications），
# 不新增表、不写事件：定级初始状态按 §8 规则复算，其余按事件流重放。


def placement_score_from_feed(payload: dict) -> int | None:
    """从定级 feed 事件 payload 解析定级分数（P-09/P-10 共用）。

    新格式（2026-07-31 起）：payload["placement"]["score"] 为结构化整数；
    旧格式兜底：定级 feed 的 segments 文案含「完成定级测试，100 分」，
    从 strong 分段 "100 分" 解析出分数。非定级 feed 或解析失败返回 None。

    Args:
        payload: DeckFeedEvent.payload（含 segments 与可选的 placement 结构）

    Returns:
        定级分数（0~100）；无法解析时返回 None。
    """
    structured = payload.get("placement")
    if isinstance(structured, dict) and isinstance(structured.get("score"), int):
        return structured["score"]
    # 旧格式：先确认是定级 feed（含标记文案），再逐段匹配 "N 分"
    segments = payload.get("segments", [])
    if not any(PLACEMENT_FEED_MARK in str(seg.get("t", "")) for seg in segments):
        return None
    for seg in segments:
        match = PLACEMENT_SCORE_RE.match(str(seg.get("t", "")).strip())
        if match:
            return int(match.group(1))
    return None


def placement_levels_from_score(score: int) -> dict[str, int]:
    """定级分数 → 三轴初始等级（§8：base = 1 + min(4, score // 25)）。

    规则与 docs/backend-api/01-target-design.md §8 及 certification/submit
    定级分支一致：review/implement 取 base，debug 恒低一档（最低 LV.1）。

    Args:
        score: 定级测试分数（0~100）

    Returns:
        {"review": LV, "debug": LV, "implement": LV} 三轴初始等级
    """
    base = 1 + min(4, score // 25)
    return {"review": base, "debug": max(1, base - 1), "implement": base}


def placement_axis_xp(score: int) -> dict[str, int]:
    """定级分数 → 三轴初始经验（§8：xp = (level-1) × XP_PER_LEVEL + 200）。

    Args:
        score: 定级测试分数（0~100）

    Returns:
        {"review": xp, "debug": xp, "implement": xp} 三轴初始经验值
    """
    return {
        axis: (level - 1) * XP_PER_LEVEL + PLACEMENT_XP_OFFSET
        for axis, level in placement_levels_from_score(score).items()
    }


async def _placement_feed_event(
    db: AsyncSession, user_id: str
) -> tuple[DeckFeedEvent, int] | None:
    """找到用户的定级 feed 事件并解析出分数（P-09/P-10 共用数据源）。

    按时间升序遍历 kind=cert 的 feed 事件，返回第一个能解析出分数的
    （新格式 payload.placement.score / 旧格式 segments 文案）。

    Args:
        db: 异步数据库会话
        user_id: 用户 ID

    Returns:
        (feed 事件行, 定级分数)；未定级返回 None。
    """
    rows = (
        await db.execute(
            select(DeckFeedEvent)
            .where(DeckFeedEvent.user_id == user_id, DeckFeedEvent.kind == "cert")
            .order_by(DeckFeedEvent.created_at.asc())
        )
    ).scalars().all()
    for row in rows:
        score = placement_score_from_feed(row.payload)
        if score is not None:
            return row, score
    return None


async def placement_snapshot(db: AsyncSession, user_id: str) -> dict | None:
    """定级画像快照（P-10 能力演化对比的数据源）。

    从用户最早的定级 feed 事件读取定级分数与日期，初始三轴等级按
    §8 规则复算，并附训练指纹短码。未定级返回 None。

    Args:
        db: 异步数据库会话
        user_id: 用户 ID

    Returns:
        {"score", "date", "levels", "fingerprint"}；未定级返回 None。
    """
    found = await _placement_feed_event(db, user_id)
    if found is None:
        return None
    feed, score = found
    levels = placement_levels_from_score(score)
    return {
        "score": score,
        "date": feed.created_at.date().isoformat(),
        "levels": levels,
        "fingerprint": training_fingerprint(
            [{"key": axis, "level": level} for axis, level in levels.items()]
        ),
    }


async def _axis_upgrade_entries(
    db: AsyncSession, user_id: str, placed_at: datetime, initial_xp: dict[str, int]
) -> list[tuple[datetime, dict]]:
    """重放三轴经验增量，产出轴升级条目（(时间, 条目) 对列表）。

    经验来源（与各 submit 端点结算一致）：
    - review：审查尝试行，每关一行，verdict.hits 为最终命中数（含重做累计），20×命中
    - debug：竞技场攻克记录，solved=1 每场 +23
    - implement：认证通过记录，每场 +40
    从定级初始经验出发按时间累加，累计经验跨过 XP_PER_LEVEL（400）边界即产出一条
    axis_upgrade 条目（from_level → to_level）。

    Args:
        db: 异步数据库会话
        user_id: 用户 ID
        placed_at: 定级时间（早于它的记录不属于该轴，防御跳过）
        initial_xp: 定级初始三轴经验（placement_axis_xp 输出）

    Returns:
        [(时间, 轴升级条目 dict), ...]，未排序。
    """
    review_rows = (
        await db.execute(
            select(DeckReviewAttempt).where(DeckReviewAttempt.user_id == user_id)
        )
    ).scalars().all()
    arena_rows = (
        await db.execute(
            select(DeckArenaAttempt).where(DeckArenaAttempt.user_id == user_id)
        )
    ).scalars().all()
    cert_rows = (
        await db.execute(
            select(DeckCertification).where(DeckCertification.user_id == user_id)
        )
    ).scalars().all()
    contributions: dict[str, list[tuple[datetime, int]]] = {
        "review": [
            (r.created_at, XP_REVIEW_PER_HIT * len(r.verdict.get("hits", [])))
            for r in review_rows
        ],
        "debug": [
            (r.created_at, XP_ARENA_SOLVED) for r in arena_rows if r.solved
        ],
        "implement": [(c.created_at, XP_CERT_PASS) for c in cert_rows],
    }
    entries: list[tuple[datetime, dict]] = []
    for axis, events in contributions.items():
        cumulative = initial_xp[axis]
        level = axis_level(cumulative)
        for ts, amount in sorted(events, key=lambda pair: pair[0]):
            # 防御：定级之前的记录不属于该轴（定级前轴行不存在）
            if ts < placed_at:
                continue
            cumulative += amount
            new_level = axis_level(cumulative)
            if new_level > level:
                entries.append(
                    (
                        ts,
                        {
                            "type": TIMELINE_AXIS_UPGRADE,
                            "date": ts.date().isoformat(),
                            "axis": axis,
                            "label": AXIS_LABELS[axis],
                            "from_level": level,
                            "to_level": new_level,
                        },
                    )
                )
                level = new_level
    return entries


async def _mastery_milestone_entries(
    db: AsyncSession, user_id: str
) -> list[tuple[datetime, dict]]:
    """重放知识点事件流，产出达到「熟练/精通」的里程碑条目（(时间, 条目) 对列表）。

    对每个知识点按时间重放 deck_mastery_events，逐事件用 mastery.mastery_level
    在事件发生时刻快照，首次达到 TIMELINE_MASTERY_LEVELS 中某个等级时产出一条条目
    （同一知识点同一等级只记首次，代表「达到」而非「反复波动」）。

    Args:
        db: 异步数据库会话
        user_id: 用户 ID

    Returns:
        [(时间, 里程碑条目 dict), ...]，未排序。
    """
    rows = (
        await db.execute(
            select(DeckMasteryEvent, DeckKnowledgePoint.name)
            .join(DeckKnowledgePoint, DeckMasteryEvent.kp_id == DeckKnowledgePoint.id)
            .where(DeckMasteryEvent.user_id == user_id)
            .order_by(DeckMasteryEvent.created_at.asc())
        )
    ).all()
    # 按知识点分组（保持事件时间升序）
    by_kp: dict[str, tuple[str, list[mastery.MasteryEvent]]] = {}
    for event, name in rows:
        if event.kp_id not in by_kp:
            by_kp[event.kp_id] = (name, [])
        by_kp[event.kp_id][1].append(
            mastery.MasteryEvent(
                created_at=event.created_at, correct=bool(event.correct), source=event.source
            )
        )
    entries: list[tuple[datetime, dict]] = []
    for kp_id, (kp_name, events) in by_kp.items():
        seen_levels: set[str] = set()
        replay: list[mastery.MasteryEvent] = []
        for event in events:
            replay.append(event)
            level = mastery.mastery_level(replay, event.created_at)
            if level in TIMELINE_MASTERY_LEVELS and level not in seen_levels:
                seen_levels.add(level)
                entries.append(
                    (
                        event.created_at,
                        {
                            "type": TIMELINE_MASTERY,
                            "date": event.created_at.date().isoformat(),
                            "kp_name": kp_name,
                            "level": level,
                        },
                    )
                )
    return entries


async def build_timeline(db: AsyncSession, user_id: str) -> list[dict]:
    """构建个人训练时间线（§3.5 P-09）：定级 → 轴升级 → 知识点里程碑 → 认证。

    只读既有事实表重放，不新增表、不写事件，四类条目按时间升序合并：
    1. 定级画像：定级 feed 事件（分数/日期/初始等级/指纹）。
    2. 轴升级：见 _axis_upgrade_entries（模块事实表重放经验增量）。
    3. 知识点里程碑：见 _mastery_milestone_entries（事件流重放）。
    4. 认证通过：deck_certifications 每条记录一条。
    未定级用户返回空列表。

    Args:
        db: 异步数据库会话
        user_id: 用户 ID

    Returns:
        按时间升序的时间线条目列表（type ∈ placement/axis_upgrade/mastery/cert）。
    """
    found = await _placement_feed_event(db, user_id)
    if found is None:
        return []
    feed, score = found
    placed_at = feed.created_at
    levels = placement_levels_from_score(score)
    # (时间, 条目) 列表，最后统一按时间升序排序
    entries: list[tuple[datetime, dict]] = [
        (
            placed_at,
            {
                "type": TIMELINE_PLACEMENT,
                "date": placed_at.date().isoformat(),
                "score": score,
                "levels": levels,
                "fingerprint": training_fingerprint(
                    [{"key": axis, "level": level} for axis, level in levels.items()]
                ),
            },
        )
    ]
    # 2. 轴升级重放
    entries.extend(
        await _axis_upgrade_entries(db, user_id, placed_at, placement_axis_xp(score))
    )
    # 3. 知识点里程碑重放
    entries.extend(await _mastery_milestone_entries(db, user_id))
    # 4. 认证通过：每条凭证记录
    cert_rows = (
        await db.execute(
            select(DeckCertification).where(DeckCertification.user_id == user_id)
        )
    ).scalars().all()
    for c in cert_rows:
        entries.append(
            (
                c.created_at,
                {
                    "type": TIMELINE_CERT,
                    "date": c.created_at.date().isoformat(),
                    "topic": c.topic,
                    "level": c.level,
                    "score": c.score,
                },
            )
        )

    # 按时间升序合并输出（同时间点按插入顺序稳定排序）
    return [entry for _, entry in sorted(entries, key=lambda pair: pair[0])]


# ── 段位 ────────────────────────────────────────────────
# 竞技场段位系统：基于 ELO 积分的段位映射。
# 初始积分 1200（白银），通过攻克挑战获得 score_delta 提升积分。

# 竞技场初始积分：1200（白银起点，get_or_create_rating 建行时使用）
ARENA_INITIAL_RATING = 1200
# 排名变化统计窗口：rank_delta 定义为「近 N 天的排名变化」
RANK_DELTA_WINDOW_DAYS = 7

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
        row = DeckArenaRating(user_id=user_id, rating=ARENA_INITIAL_RATING, win_streak=0)
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


async def rank_delta_7d(db: AsyncSession, user_id: str, current_rank: int) -> int:
    """近 RANK_DELTA_WINDOW_DAYS 天排名变化（§4 arena/profile 的 rank_delta，正数 = 上升）。

    推导（不新增表，基于现有事实表的诚实重放）：
    - deck_arena_ratings 只存当前积分（每用户一行，无历史），但现行规则里积分
      只在攻克时 +ARENA_SOLVED_SCORE_DELTA（router.run_arena 唯一变更点，初始
      ARENA_INITIAL_RATING），因此任意历史时刻的积分可精确重放：
      rating(T) = ARENA_INITIAL_RATING + ARENA_SOLVED_SCORE_DELTA × (T 前攻克次数)。
    - 7 天前排名 = 1 + 全体有 rating 行的用户中「7 天前积分更高」的人数（无攻克
      记录按初始分计），与 week_rank 同人群口径，保证两个排名可比。
    - 返回 rank_7d − current_rank：正数表示 7 天内排名上升（如 +12 = 上升 12 名）。

    守卫：用户 7 天前无任何竞技场尝试记录（cutoff 前无 deck_arena_attempts 行）时
    直接返回 0——此时「7 天前排名」不可定义（新进竞技场的用户），避免把加入时间
    误算成排名下降。

    局限（文档化）：若未来 score_delta 改为按用时/难度动态折算（spec §4 有此设想），
    本重放将不再精确，需要新增积分历史表；当前实现攻克固定 +23，重放与现行规则一致。

    Args:
        db: 异步数据库会话
        user_id: 用户 ID
        current_rank: 用户当前排名（week_rank 的结果）

    Returns:
        近 7 天排名变化（整数；7 天前无记录或两排名相等时为 0）。
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=RANK_DELTA_WINDOW_DAYS)
    # 守卫：cutoff 前无任何尝试记录 → 「7 天前排名」不可定义，返回 0
    prior_attempts = await db.scalar(
        select(func.count())
        .select_from(DeckArenaAttempt)
        .where(
            DeckArenaAttempt.user_id == user_id,
            DeckArenaAttempt.created_at < cutoff,
        )
    )
    if not prior_attempts:
        return 0
    # 自己的 7 天前积分：初始分 + 7 天前攻克次数 × 单场奖励
    my_solved = await db.scalar(
        select(func.count())
        .select_from(DeckArenaAttempt)
        .where(
            DeckArenaAttempt.user_id == user_id,
            DeckArenaAttempt.solved == 1,
            DeckArenaAttempt.created_at < cutoff,
        )
    )
    my_rating_7d = ARENA_INITIAL_RATING + ARENA_SOLVED_SCORE_DELTA * int(my_solved or 0)
    # 全体用户 7 天前攻克次数（无攻克记录的按 0 计 → 初始分）
    solved_rows = (
        await db.execute(
            select(DeckArenaAttempt.user_id, func.count())
            .where(DeckArenaAttempt.solved == 1, DeckArenaAttempt.created_at < cutoff)
            .group_by(DeckArenaAttempt.user_id)
        )
    ).all()
    solved_map = {uid: cnt for uid, cnt in solved_rows}
    # 7 天前排名：与 week_rank 同人群（现有 rating 行用户），7 天前积分更高者 +1
    rating_user_ids = (
        await db.execute(select(DeckArenaRating.user_id))
    ).scalars().all()
    higher_7d = sum(
        1
        for uid in rating_user_ids
        if ARENA_INITIAL_RATING + ARENA_SOLVED_SCORE_DELTA * solved_map.get(uid, 0)
        > my_rating_7d
    )
    return higher_7d + 1 - current_rank


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


# ── 竞技场判定（对齐 mock judgeArenaCode）───────────────
# 竞技场代码判定：Judge0 真判题优先（见下方「Judge0 判题」区块），
# 本区块的规则匹配（字符串检测）是降级路径——Judge0 未配置/异常时由
# judge_arena_code_submit 回退到这里的函数。每个挑战有独立的判定函数，
# 通过 ARENA_JUDGES 字典按 challenge_id 分发，规则与前端 mock 完全一致。

# 每个判定函数签名：(code, failing_output) -> dict
# 返回 dict 包含: passed / total / output / solved / score_delta


def _judge_debug_0091(code: str, failing_output: str) -> dict:
    """DEBUG-0091 中位数统计：死循环 + 右中位索引错。

    两个修复点：
    1. ``lo = mid - 1``（删掉死循环，直接取左中位）
    2. ``nums[lo] + nums[mid])``（右中位是 nums[mid] 不是 nums[mid+1]）
    """
    normalized = re.sub(r"\s+", "", code)
    rule_loop = "lo=mid-1" in normalized
    rule_index = "nums[lo]+nums[mid])" in normalized
    if rule_loop and rule_index:
        return {"passed": 5, "total": 5, "output": _ARENA_0091_SOLVED,
                "solved": True, "score_delta": 23}
    if rule_loop:
        return {"passed": 3, "total": 5, "output": _ARENA_0091_PARTIAL,
                "solved": False, "score_delta": 0}
    return {"passed": 2, "total": 5, "output": failing_output,
            "solved": False, "score_delta": 0}


def _judge_debug_0092(code: str, failing_output: str) -> dict:
    """DEBUG-0092 二分查找越界：right = len(arr) 应为 len(arr) - 1。

    修复点：``len(arr) - 1`` 出现在代码中（right 初始化修正）。
    """
    normalized = re.sub(r"\s+", "", code)
    fixed = "len(arr)-1" in normalized
    if fixed:
        return {"passed": 5, "total": 5, "output": _ARENA_0092_SOLVED,
                "solved": True, "score_delta": 23}
    return {"passed": 2, "total": 5, "output": failing_output,
            "solved": False, "score_delta": 0}


def _judge_debug_0093(code: str, failing_output: str) -> dict:
    """DEBUG-0093 字符串反转指针丢失：return dest 应为 return result。

    修复点：``return result`` 替代 ``return dest``。
    """
    normalized = re.sub(r"\s+", "", code)
    fixed = "returnresult" in normalized
    if fixed:
        return {"passed": 5, "total": 5, "output": _ARENA_0093_SOLVED,
                "solved": True, "score_delta": 23}
    return {"passed": 2, "total": 5, "output": failing_output,
            "solved": False, "score_delta": 0}


def _judge_debug_0094(code: str, failing_output: str) -> dict:
    """DEBUG-0094 去重计数逻辑错误：缺少 if w not in seen 判断。

    修复点：代码中出现 ``not in seen``（添加去重判断）。
    """
    normalized = re.sub(r"\s+", "", code)
    fixed = "notinseen" in normalized
    if fixed:
        return {"passed": 5, "total": 5, "output": _ARENA_0094_SOLVED,
                "solved": True, "score_delta": 23}
    return {"passed": 2, "total": 5, "output": failing_output,
            "solved": False, "score_delta": 0}


def _judge_debug_0095(code: str, failing_output: str) -> dict:
    """DEBUG-0095 阶乘栈溢出：缺少递归出口。

    修复点：代码中出现 ``return1``（添加基例返回）。
    """
    normalized = re.sub(r"\s+", "", code)
    fixed = "return1" in normalized
    if fixed:
        return {"passed": 5, "total": 5, "output": _ARENA_0095_SOLVED,
                "solved": True, "score_delta": 23}
    return {"passed": 0, "total": 5, "output": failing_output,
            "solved": False, "score_delta": 0}


# 挑战 ID -> 判定函数的分发表
ARENA_JUDGES: dict[str, callable] = {
    "DEBUG-0091": _judge_debug_0091,
    "DEBUG-0092": _judge_debug_0092,
    "DEBUG-0093": _judge_debug_0093,
    "DEBUG-0094": _judge_debug_0094,
    "DEBUG-0095": _judge_debug_0095,
}


def judge_arena_code(code: str, challenge_id: str, failing_output: str) -> dict:
    """竞技场代码判定（关键字匹配降级版）。

    这是 Judge0 不可用时的降级路径：根据 challenge_id 分发到对应的判定函数，
    每个函数检查该题特定的修复模式（与前端 mock 一致）。
    未知挑战 ID 返回全失败。Judge0 判题入口见 judge_arena_code_submit。

    Args:
        code: 用户提交的代码
        challenge_id: 挑战 ID（如 DEBUG-0091）
        failing_output: 原始失败输出（全失败时返回给用户）

    Returns:
        判定结果 dict，包含：
        - passed: 通过的测试数
        - total: 总测试数
        - output: 模拟的测试输出文本
        - solved: 是否全部通过
        - score_delta: 积分变动（全通过 +23，否则 0）
    """
    judge_fn = ARENA_JUDGES.get(challenge_id)
    if judge_fn is None:
        return {"passed": 0, "total": 0, "output": failing_output,
                "solved": False, "score_delta": 0}
    return judge_fn(code, failing_output)


# ── 竞技场 / 认证 code 题 Judge0 判题（真判分 + 关键字降级）──
# 判题统一入口：优先调用 Judge0 在线评测引擎跑测试用例（真实判分），
# 未配置 base_url / 连接失败 / 超时 / 返回异常时，回退到上方关键字匹配
# 判定（judge_arena_code / judge_cert_answer 的 includes 分支），保证
# 没启动 Judge0 的开发环境功能完全可用。降级判断集中在
# judge_arena_code_submit / judge_cert_code_answer 两个入口内。

# 全局 Judge0 判题服务单例：由 lifespan 在启动时配置（base_url 为空则不启用）
_judge0: Judge0Service | None = None

# 竞技场挑战语言 -> Judge0 language_id 映射（只覆盖种子里出现的语言）
ARENA_LANGUAGE_IDS: dict[str, int] = {
    "python": LANGUAGE_PYTHON,  # Python 3 (71)
    "c": LANGUAGE_C,            # C (GCC 9.2, 50)
}

# 竞技场攻克奖励积分：与 mock（judgeArenaCode）一致，全过 +23
ARENA_SOLVED_SCORE_DELTA = 23

# 竞技场判题驱动：追加在用户提交代码之后，把「函数实现」变成可运行的完整
# 程序——从 stdin 读取输入、向 stdout 打印结果，供 Judge0 批量执行判定。
ARENA_DRIVERS: dict[str, str] = {
    "DEBUG-0091": "\nimport sys, json\nprint(median(json.loads(sys.stdin.read())))\n",
    "DEBUG-0092": (
        "\nimport sys, json\n"
        "lines = sys.stdin.read().splitlines()\n"
        "arr = json.loads(lines[0])\n"
        "target = json.loads(lines[1])\n"
        "print(binary_search(arr, target))\n"
    ),
    "DEBUG-0093": (
        "\n#include <stdio.h>\n"
        "int main() {\n"
        "    char buf[1024];\n"
        "    size_t n = fread(buf, 1, sizeof(buf) - 1, stdin);\n"
        "    while (n > 0 && (buf[n - 1] == '\\n' || buf[n - 1] == '\\r')) n--;\n"
        "    buf[n] = '\\0';\n"
        "    char *r = reverse_str(buf);\n"
        "    printf(\"%s\\n\", r);\n"
        "    free(r);\n"
        "    return 0;\n"
        "}\n"
    ),
    "DEBUG-0094": "\nimport sys, json\nprint(count_unique(json.loads(sys.stdin.read())))\n",
    "DEBUG-0095": "\nimport sys\nprint(factorial(int(sys.stdin.read().strip())))\n",
}

# 认证考试语言 -> Judge0 language_id 映射（cert-pointer 为 C，其余为 Python）
CERT_EXAM_LANGUAGE_IDS: dict[str, int] = {
    "cert-pointer": LANGUAGE_C,
    "cert-recursion": LANGUAGE_PYTHON,
    "placement": LANGUAGE_PYTHON,
}

# 认证 code 题判题驱动：key 为 "{exam_id}:{qid}"，追加在用户代码之后
CERT_CODE_DRIVERS: dict[str, str] = {
    "cert-pointer:q5": (
        "\n#include <stdio.h>\n"
        "int main() {\n"
        "    int x, y;\n"
        "    if (scanf(\"%d %d\", &x, &y) != 2) return 1;\n"
        "    swap(&x, &y);\n"
        "    printf(\"%d %d\\n\", x, y);\n"
        "    return 0;\n"
        "}\n"
    ),
    "cert-pointer:q6": (
        "\n#include <stdio.h>\n"
        "int main() {\n"
        "    int n;\n"
        "    if (scanf(\"%d\", &n) != 1) return 1;\n"
        "    if (n == 0) {\n"
        "        int *p = find(NULL, 0);\n"
        "        printf(\"%s\\n\", p == NULL ? \"NULL\" : \"NOT_NULL\");\n"
        "        return 0;\n"
        "    }\n"
        "    int arr[1000];\n"
        "    for (int i = 0; i < n; i++) scanf(\"%d\", &arr[i]);\n"
        "    int *p = find(arr, n);\n"
        "    if (p == NULL) { printf(\"NULL\\n\"); return 0; }\n"
        "    printf(\"%d %d\\n\", *p, (int)(p - arr));\n"
        "    return 0;\n"
        "}\n"
    ),
    "placement:p4": (
        "\nimport sys\n"
        "s = sys.stdin.read()\n"
        "if s.endswith(\"\\n\"):\n"
        "    s = s[:-1]\n"
        "print(first_unique(s))\n"
    ),
    "placement:p5": "\nimport sys\nprint(is_power_of_two(int(sys.stdin.read().strip())))\n",
    "cert-recursion:q5": (
        "\nimport sys\n"
        "s = sys.stdin.read()\n"
        "if s.endswith(\"\\n\"):\n"
        "    s = s[:-1]\n"
        "print(reverse_str(s))\n"
    ),
    "cert-recursion:q6": (
        "\nimport sys\n"
        "base, exp = map(int, sys.stdin.read().split())\n"
        "print(power(base, exp))\n"
    ),
}


def configure_judge0(base_url: str | None) -> None:
    """配置全局 Judge0 判题服务（应用启动时由 lifespan 调用）。

    Args:
        base_url: Judge0 API 基地址；为空/None 表示未接入 Judge0，
                  竞技场与认证 code 题判分自动降级为关键字匹配。
    """
    global _judge0
    # base_url 为空时不创建客户端（避免误连公共实例），判题走降级
    _judge0 = Judge0Service(Judge0Client(base_url)) if base_url else None


async def aclose_judge0() -> None:
    """关闭全局 Judge0 服务的底层 HTTP 连接（应用关闭时由 lifespan 调用）。"""
    if _judge0 is not None:
        await _judge0.close()


def _format_arena_output(batch: dict) -> str:
    """把 Judge0 批量判题结果格式化为前端可读的测试输出文本。

    Args:
        batch: Judge0Service.execute_batch 的返回结构（含 results 列表）

    Returns:
        多行文本：每个用例的通过/失败 + 输入/期望/实际输出或错误消息。
    """
    lines = [f"$ 运行 {batch['total_count']} 个测试用例，通过 {batch['passed_count']} 个"]
    for r in batch["results"]:
        if r["passed"]:
            lines.append(f"用例: PASSED   输入 {r['input']!r} → 输出 {r['actual']!r}")
        elif r["actual"]:
            lines.append(
                f"用例: FAILED   输入 {r['input']!r} → 期望 {r['expected']!r}，"
                f"实际 {r['actual']!r}"
            )
        else:
            lines.append(f"用例: FAILED   {r['message']}")
    return "\n".join(lines)


async def judge_arena_code_submit(
    code: str,
    challenge_id: str,
    failing_output: str,
    test_cases: list | None,
    language: str,
    judge: Judge0Service | None = None,
) -> dict:
    """竞技场判题统一入口：Judge0 真判题优先，未配置/异常回退关键字匹配。

    降级策略（集中在本函数内，调用方无需感知）：
    1. Judge0 未配置（_judge0 为 None）、挑战无测试用例、语言不支持或
       无驱动 → 直接用 judge_arena_code 关键字判定
    2. Judge0 调用抛异常（网络/超时等）→ 记录日志后回退关键字判定

    Args:
        code: 用户提交的修正代码
        challenge_id: 挑战 ID（如 DEBUG-0091）
        failing_output: 挑战的失败输出（降级时全失败场景返回给用户）
        test_cases: 挑战的测试用例列表（无则降级）
        language: 挑战的编程语言（python/c）
        judge: 可注入的 Judge0 服务（测试用），默认全局 _judge0

    Returns:
        与 judge_arena_code 相同的契约：passed / total / output / solved / score_delta
    """
    judge = judge if judge is not None else _judge0
    driver = ARENA_DRIVERS.get(challenge_id)
    lang_id = ARENA_LANGUAGE_IDS.get(language)
    if judge is not None and driver is not None and lang_id is not None and test_cases:
        try:
            # 用户代码 + 判题驱动 = 可运行的完整程序，批量跑全部测试用例
            batch = await judge.execute_batch(code + driver, lang_id, test_cases)
            total = batch["total_count"]
            passed = batch["passed_count"]
            solved = total > 0 and passed == total
            return {
                "passed": passed,
                "total": total,
                "output": _format_arena_output(batch),
                "solved": solved,
                "score_delta": ARENA_SOLVED_SCORE_DELTA if solved else 0,
            }
        except Exception:
            # Judge0 调用失败（网络/超时等），回退关键字判定保证可用
            logger.exception("竞技场 Judge0 判题失败，回退关键字判定")
    return judge_arena_code(code, challenge_id, failing_output)


async def judge_cert_code_answer(
    answer: str,
    exam_id: str,
    qid: str,
    includes: list | None,
    test_cases: list | None,
    judge: Judge0Service | None = None,
) -> bool:
    """认证 code 题判分统一入口：Judge0 真判分优先，未配置/异常回退关键片段匹配。

    降级策略（集中在本函数内，调用方无需感知）：
    1. Judge0 未配置、题目无测试用例、无驱动或语言不支持 → 用
       judge_cert_answer 的 includes 分支判定
    2. Judge0 调用抛异常 → 记录日志后回退关键片段匹配

    Args:
        answer: 用户提交的代码
        exam_id: 考试 ID（cert-pointer / cert-recursion / placement）
        qid: 题目编号（q5/q6/p4/p5）
        includes: 关键片段列表（Judge0 不可用时降级用）
        test_cases: 题目的测试用例列表（无则降级）
        judge: 可注入的 Judge0 服务（测试用），默认全局 _judge0

    Returns:
        True 表示全部测试用例通过（降级模式下为包含所有关键片段）。
    """
    judge = judge if judge is not None else _judge0
    driver = CERT_CODE_DRIVERS.get(f"{exam_id}:{qid}")
    lang_id = CERT_EXAM_LANGUAGE_IDS.get(exam_id)
    if judge is not None and driver is not None and lang_id is not None and test_cases:
        try:
            batch = await judge.execute_batch(answer + driver, lang_id, test_cases)
            # 全部测试用例通过才算正确（与 mcq 的单题对错语义一致）
            return (
                batch["total_count"] > 0
                and batch["passed_count"] == batch["total_count"]
            )
        except Exception:
            # Judge0 调用失败（网络/超时等），回退关键片段匹配保证可用
            logger.exception("认证 code 题 Judge0 判题失败，回退关键片段匹配")
    return judge_cert_answer("code", answer, None, includes)


# ── 各挑战的模拟测试输出 ──

# DEBUG-0091
_ARENA_0091_SOLVED = """$ pytest test_median.py -v
test_median.py::test_odd            PASSED   [ 20%]
test_median.py::test_single         PASSED   [ 40%]
test_median.py::test_even           PASSED   [ 60%]
test_median.py::test_even_negative  PASSED   [ 80%]
test_median.py::test_even_unsorted  PASSED   [100%]

======================== 5 passed in 0.08s ========================"""

_ARENA_0091_PARTIAL = """$ pytest test_median.py -v
test_median.py::test_even           FAILED   assert 5.0 == 4.5
test_median.py::test_even_negative  FAILED   assert -4.0 == -4.5

=================== 3 passed, 2 failed in 0.11s ===================
右中位索引还有问题：偶数个时中间两个是 nums[mid-1] 和 nums[mid]。"""

# DEBUG-0092
_ARENA_0092_SOLVED = """$ pytest test_bsearch.py -v
test_bsearch.py::test_found         PASSED   [ 20%]
test_bsearch.py::test_not_found     PASSED   [ 40%]
test_bsearch.py::test_last_element  PASSED   [ 60%]
test_bsearch.py::test_single        PASSED   [ 80%]
test_bsearch.py::test_empty         PASSED   [100%]

======================== 5 passed in 0.06s ========================"""

# DEBUG-0093
_ARENA_0093_SOLVED = """$ gcc -o test test.c && ./test
test_str_reverse("hello")    -> "olleh"   OK
test_str_reverse("a")        -> "a"       OK
test_str_reverse("")         -> ""        OK
test_str_reverse("abcdef")   -> "fedcba"  OK
test_str_reverse("12345")    -> "54321"   OK

======================== 5/5 tests passed ========================"""

# DEBUG-0094
_ARENA_0094_SOLVED = """$ pytest test_unique.py -v
test_unique.py::test_empty          PASSED   [ 20%]
test_unique.py::test_all_unique     PASSED   [ 40%]
test_unique.py::test_all_same       PASSED   [ 60%]
test_unique.py::test_mixed          PASSED   [ 80%]
test_unique.py::test_with_numbers   PASSED   [100%]

======================== 5 passed in 0.04s ========================"""

# DEBUG-0095
_ARENA_0095_SOLVED = """$ pytest test_factorial.py -v
test_factorial.py::test_zero     PASSED   [ 20%]
test_factorial.py::test_one      PASSED   [ 40%]
test_factorial.py::test_five     PASSED   [ 60%]
test_factorial.py::test_three    PASSED   [ 80%]
test_factorial.py::test_ten      PASSED   [100%]

======================== 5 passed in 0.03s ========================"""


# ── 导师脚本（LLM 未配置/调用失败时的降级实现）──────────────
# 苏格拉底导师优先走真实 LLM 追问（见下方「导师 LLM」区块），
# 本区块的脚本式回复（关键词匹配 + 通用追问轮替）作为降级路径，
# 保证开发阶段无需 AI 调用即可测试交互流程。

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


# 苏格拉底问题润色系统提示词：把口语化困惑改写成清晰、具体的技术问题
QUESTION_POLISH_SYSTEM_PROMPT = (
    "你是一位编程导师。把学生对编程困惑的原始描述改写成清晰、具体的技术问题。\n\n"
    "要求：\n"
    "1. 一两句中文，只输出改写后的问题本身，不要任何解释、前缀或引号\n"
    "2. 保留原始描述中的关键细节（报错信息、代码行为、期望与实际的差异）\n"
    "3. 去除口语化冗余，让问题聚焦、可被直接回答"
)


async def question_polish(text: str, ai: AIService | None = None) -> str:
    """把学生的口语化困惑润色为清晰的技术问题。

    降级策略（与 tutor_llm_reply 一致）：AI 未配置、LLM 调用抛异常、
    返回空串/纯空白时回退原文，保证没有 API Key 的环境功能完全可用。
    本函数只改写表述，不改变问题语义。

    Args:
        text: 学生的原始描述
        ai: 可注入的 AI 服务（测试用），默认全局 ai_service

    Returns:
        润色后的问题文本；降级时返回原文。
    """
    ai = ai if ai is not None else ai_service
    if not ai.is_configured():
        return text
    try:
        response = await ai.generate_messages(
            [{"role": "user", "content": text}],
            system_prompt=QUESTION_POLISH_SYSTEM_PROMPT,
        )
        polished = (response or "").strip()
        return polished if polished else text
    except Exception:
        logger.exception("苏格拉底问题润色失败，回退原文")
        return text


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


# ── 导师 LLM（配置 AI 后走真实 LLM，未配置/异常走脚本降级）──
# 苏格拉底导师与费曼检验的 AI 接入层：优先调用全局 ai_service，
# 未配置、调用异常或解析失败时统一回退到上方脚本实现，保证
# 没有配 API Key 的开发环境功能完全可用。降级判断集中在
# tutor_llm_reply / feynman_evaluate 两个统一入口内。

# 传给 LLM 的最近对话历史条数（按时间倒序截取）
TUTOR_HISTORY_LIMIT = 10
# 注入导师 system prompt 的薄弱知识点条数上限（p_l 升序取前 N）
TUTOR_WEAK_KP_LIMIT = 3
# 薄弱知识点注入阈值：只注入 p_l 真正低于该值的知识点（严格小于）。
# 复用 DUE_MASTERY_THRESHOLD（0.6）：与「记忆正在消退」的到期复习口径一致——
# 定级后所有知识点 p_l≈1.0，若不过滤会把「掌握度 100%」的强势点当薄弱点注入，
# 自相矛盾；p_l<0.6 才意味着记忆确实在衰减，值得导师针对追问。
# 近期失败记录条数（按时间倒序取最近 N）
TUTOR_FAILURE_LIMIT = 3

# 苏格拉底导师系统提示词：只提问引导，禁止直接给答案/写代码
SOCRATIC_SYSTEM_PROMPT = (
    "你是一位苏格拉底式追问导师，专精编程教学。\n\n"
    "硬性规则：\n"
    "1. 绝不直接给出答案、不写完整代码、不解释实现步骤。\n"
    "2. 你的唯一输出形式是提问——用层层递进的问题引导用户自己发现答案。\n"
    "3. 每次回复只提一个核心问题（可带 1-2 句铺垫），不要一次抛出多个问题。\n"
    "4. 针对用户发言里的具体细节追问，不要泛泛地问「你觉得呢」。\n"
    "5. 使用中文回复。"
)

# 费曼检验系统提示词：按评分要点判断覆盖情况，输出结构化 JSON
FEYNMAN_SYSTEM_PROMPT = (
    "你是一位费曼检验考官。费曼检验要求学生用自己的话讲清楚一个编程知识点。\n\n"
    "任务：阅读学生的讲解，判断他讲到了评分要点（label）中的哪些关键点。\n"
    "评分要点清单和同义表达示例由用户消息给出，covered/missed 必须使用要点 label 原文。\n\n"
    "只输出一个 JSON 对象，不要任何其他文字，格式如下：\n"
    '{"covered": ["被讲到的要点 label", ...], '
    '"missed": ["没讲到的要点 label", ...], '
    '"structure": true或false, '
    '"grade": "优秀|良好|待加强", '
    '"feedback": "2-3 句中文点评，必须点名学生遗漏的关键点"}'
)


def _socratic_messages(
    text: str, history: list[tuple[str, str]]
) -> list[dict[str, str]]:
    """构造苏格拉底追问的用户消息：最近对话历史 + 最新发言。

    Args:
        text: 用户最新消息文本
        history: (role, text) 对话历史（正序）

    Returns:
        单条 user 消息的消息列表，供 generate_messages 发送。
    """
    if history:
        lines = "\n".join(
            f"学生：{m}" if role == "user" else f"导师：{m}" for role, m in history
        )
        content = f"最近对话历史：\n{lines}\n\n学生最新发言：\n{text}"
    else:
        content = f"学生说：\n{text}"
    return [{"role": "user", "content": content}]


async def _tutor_user_context(db: AsyncSession, user_id: str) -> str:
    """查询并拼装注入导师 system prompt 的用户上下文块（§3.5 P-07）。

    内容三部分：
    1. 三轴等级：审阅/调试/实现各轴 LV.x（get_axes 已含未定级兜底 LV.1）
    2. 薄弱知识点：p_l 严格低于 DUE_MASTERY_THRESHOLD 的，按 p_l 升序取前
       TUTOR_WEAK_KP_LIMIT 个，带掌握度百分比与掌握等级；全部高于阈值时渲染
       「（暂无）」。阈值过滤防止把定级后的强势点（p_l≈1.0）当薄弱点注入。
    3. 近期失败：最近 TUTOR_FAILURE_LIMIT 条答错事件，带知识点名与时间标签

    隐私与克制（设计约束 3/4）：只注入该用户本人数据；用户没有任何能力数据
    （未定级新用户）时返回空串，即不注入、system prompt 保持原样。

    Args:
        db: 异步数据库会话
        user_id: 用户 ID

    Returns:
        追加在 SOCRATIC_SYSTEM_PROMPT 之后的上下文块；无数据时为空串。
    """
    axes = await get_axes(db, user_id)
    # 薄弱知识点：p_l 低于 DUE_MASTERY_THRESHOLD（严格小于）且按 p_l 升序（越靠前
    # 越薄弱），带缓存读模型的 p_l 与等级
    weak_rows = (
        await db.execute(
            select(DeckKnowledgePoint.name, DeckUserMastery.p_l, DeckUserMastery.level)
            .join(DeckUserMastery, DeckUserMastery.kp_id == DeckKnowledgePoint.id)
            .where(
                DeckUserMastery.user_id == user_id,
                DeckUserMastery.p_l < DUE_MASTERY_THRESHOLD,
            )
            .order_by(DeckUserMastery.p_l.asc())
            .limit(TUTOR_WEAK_KP_LIMIT)
        )
    ).all()
    # 近期失败：最近 N 条答错掌握度事件（事实表，含知识点名与时间标签）
    failure_rows = (
        await db.execute(
            select(DeckKnowledgePoint.name, DeckMasteryEvent.created_at)
            .join(DeckMasteryEvent, DeckMasteryEvent.kp_id == DeckKnowledgePoint.id)
            .where(
                DeckMasteryEvent.user_id == user_id,
                DeckMasteryEvent.correct.is_(False),
            )
            .order_by(DeckMasteryEvent.created_at.desc())
            .limit(TUTOR_FAILURE_LIMIT)
        )
    ).all()
    # 无任何能力数据（未定级新用户）→ 不注入，保持无上下文原样
    if not weak_rows and not failure_rows and all(a["level"] <= 1 for a in axes):
        return ""
    axis_text = " · ".join(f"{a['label']} LV.{a['level']}" for a in axes)
    weak_text = "、".join(
        f"{name}（掌握度 {round(p_l * 100)}% · {level}）"
        for name, p_l, level in weak_rows
    ) or "（暂无）"
    failure_text = "、".join(
        f"{name}（{feed_time_label(created_at)}）" for name, created_at in failure_rows
    ) or "（暂无）"
    return (
        "\n\n【学生能力档案】该学生本人的能力数据（仅用于调整追问方向，"
        "不要向学生复述这些数据，不要承诺提供专属课程）：\n"
        f"- 能力轴：{axis_text}\n"
        f"- 薄弱知识点：{weak_text}\n"
        f"- 近期失败：{failure_text}"
    )


async def tutor_llm_reply(
    db: AsyncSession,
    user_id: str,
    text: str,
    history: list[tuple[str, str]],
    ai: AIService | None = None,
) -> str:
    """苏格拉底导师回复统一入口：LLM 追问优先，未配置/异常回退脚本式回复。

    降级策略（集中在本函数内，调用方无需感知），共两层：
    1. 上下文层（P-07 注入）：能力上下文查询失败只丢弃上下文
       （记录 warning），仍走 LLM 调用——有上下文 LLM → 无上下文 LLM
    2. 模型层：AI 未配置、LLM 调用抛异常、返回空串/纯空白 → socratic_reply
       脚本式回复兜底，保证没有 API Key 的环境功能完全可用

    会话不持久化：对话历史由调用方携带传入。

    Args:
        db: 异步数据库会话（用于查询用户能力上下文）
        user_id: 用户 ID
        text: 用户最新消息
        history: 调用方携带的最近对话历史（(role, text)，正序，最多
            TUTOR_HISTORY_LIMIT 条；脚本降级时用其长度轮换通用追问）
        ai: 可注入的 AI 服务（测试用），默认全局 ai_service

    Returns:
        导师回复文本。
    """
    ai = ai if ai is not None else ai_service
    if not ai.is_configured():
        return socratic_reply(text, len(history))
    # ── 第一层降级：上下文查询失败只丢弃上下文，不中断 LLM 主链路 ──
    context_block = ""
    try:
        context_block = await _tutor_user_context(db, user_id)
    except Exception:
        logger.warning("苏格拉底导师用户上下文注入失败，降级为无上下文 LLM 调用", exc_info=True)
    # ── 第二层降级：LLM 调用异常/空响应 → 脚本式回复 ──
    try:
        response = await ai.generate_messages(
            _socratic_messages(text, history),
            system_prompt=SOCRATIC_SYSTEM_PROMPT + context_block,
        )
        reply = (response or "").strip()
        return reply if reply else socratic_reply(text, len(history))
    except Exception:
        # LLM 调用失败（网络/超时等），回退脚本式回复保证可用
        logger.exception("苏格拉底导师 LLM 调用失败，回退脚本式回复")
        return socratic_reply(text, len(history))


def _feynman_prompt(
    text: str, kp_name: str, key_points: list[dict] | None
) -> str:
    """构造费曼检验评分的用户消息：知识点 + 评分要点 + 学生讲解。

    Args:
        text: 学生讲解文本
        kp_name: 知识点名称
        key_points: 评分要点列表（每项含 label/keys）

    Returns:
        拼接好的用户提示词。
    """
    lines = [
        f"- {p['label']}（同义表达：{'/'.join(p.get('keys', []))}）"
        for p in key_points or []
    ]
    points_str = "\n".join(lines) if lines else "（该知识点未配置评分要点）"
    return (
        f"知识点：{kp_name}\n\n评分要点：\n{points_str}\n\n"
        f"学生的讲解：\n{text}"
    )


def _extract_first_json_object(response: str) -> dict:
    """从 LLM 响应中提取第一个 JSON 对象。

    AI 输出不可完全预测：可能包裹 ```json``` 代码块、前后带说明文字。
    取第一个 "{" 到最后一个 "}" 之间的片段尝试解析。

    Args:
        response: LLM 原始响应文本

    Returns:
        解析出的 JSON 对象（dict）。

    Raises:
        json.JSONDecodeError: 响应中不存在可解析的 JSON 对象。
    """
    start = response.find("{")
    end = response.rfind("}")
    if start < 0 or end <= start:
        raise json.JSONDecodeError("响应中不存在 JSON 对象", response, 0)
    return json.loads(response[start : end + 1])


def parse_feynman_llm_result(
    response: str, text: str, labels: list[str]
) -> dict | None:
    """解析并校验费曼检验的 LLM 结构化输出。

    校验规则：
    - 必须是合法 JSON 对象（容忍 ```json 包裹和前后文字）
    - covered 必须是字符串列表；其中不在 labels 里的标签（LLM 臆造）会被过滤
    - missed 由 labels 与 covered 的差集重算（不信任 LLM 的 missed）
    - structure 缺省或类型非法时用文本中的因果/举例词兜底判断

    Args:
        response: LLM 原始响应文本
        text: 学生讲解文本（structure 兜底判断用）
        labels: 知识点全部评分要点的 label 列表

    Returns:
        规范化后的 {"covered", "missed", "structure", "feedback"}；
        解析失败或结构非法时返回 None（由调用方降级）。
    """
    try:
        obj = _extract_first_json_object(response)
    except json.JSONDecodeError:
        return None
    covered = obj.get("covered")
    if not isinstance(covered, list) or not all(
        isinstance(c, str) for c in covered
    ):
        return None
    # 过滤 LLM 臆造的标签，missed 用差集重算
    covered = [c for c in covered if c in labels]
    missed = [l for l in labels if l not in covered]
    # structure 缺省或类型非法时用脚本兜底（因果词 + 举例词）
    structure = obj.get("structure")
    if not isinstance(structure, bool):
        structure = _has_structure(text)
    feedback = obj.get("feedback")
    if not isinstance(feedback, str):
        feedback = ""
    return {
        "covered": covered,
        "missed": missed,
        "structure": structure,
        "feedback": feedback,
    }


def _has_structure(text: str) -> bool:
    """检查文本是否同时包含因果推理词与举例说明词（结构分脚本兜底）。

    Args:
        text: 学生讲解文本

    Returns:
        True 表示具备因果 + 举例结构。
    """
    return any(m in text for m in mastery.CAUSAL_MARKERS) and any(
        m in text for m in mastery.EXAMPLE_MARKERS
    )


async def feynman_llm_evaluate(
    text: str,
    kp_name: str,
    key_points: list[dict] | None,
    ai: AIService | None = None,
) -> dict | None:
    """费曼检验 LLM 评分：判断覆盖/遗漏要点，按量规评级并生成点评。

    流程：
    1. 构造带评分要点的提示词发给 LLM（要求返回结构化 JSON）
    2. 解析并校验（parse_feynman_llm_result）
    3. 用与关键词评分相同的量规（mastery.feynman_grade_from_coverage）定级
    4. feedback 缺失时回退到脚本点评 feynman_feedback

    Args:
        text: 学生讲解文本
        kp_name: 知识点名称
        key_points: 评分要点列表（每项含 label/keys）
        ai: 可注入的 AI 服务（测试用），默认全局 ai_service

    Returns:
        {"grade", "covered", "missed", "feedback"}；
        AI 未配置/调用异常/解析失败时返回 None（由调用方降级）。
    """
    ai = ai if ai is not None else ai_service
    if not ai.is_configured():
        return None
    try:
        labels = [p["label"] for p in key_points or []]
        response = await ai.generate_messages(
            [{"role": "user", "content": _feynman_prompt(text, kp_name, key_points)}],
            system_prompt=FEYNMAN_SYSTEM_PROMPT,
        )
        parsed = parse_feynman_llm_result(response, text, labels)
        if parsed is None:
            return None
        grade = mastery.feynman_grade_from_coverage(
            len(parsed["covered"]) / len(labels) if labels else 0.0,
            parsed["structure"],
            bool(labels),
        )
        feedback = parsed["feedback"].strip() or feynman_feedback(
            grade, parsed["covered"], parsed["missed"]
        )
        return {
            "grade": grade,
            "covered": parsed["covered"],
            "missed": parsed["missed"],
            "feedback": feedback,
        }
    except Exception:
        # LLM 调用失败（网络/超时等），回退脚本评分保证可用
        logger.exception("费曼检验 LLM 评分失败，回退脚本评分")
        return None


async def feynman_evaluate(
    text: str,
    kp_name: str,
    key_points: list[dict] | None,
    ai: AIService | None = None,
) -> tuple[str, str]:
    """费曼检验评分统一入口：LLM 优先，未配置/异常/脏 JSON 回退关键词评分。

    Args:
        text: 学生讲解文本
        kp_name: 知识点名称
        key_points: 评分要点列表（每项含 label/keys）
        ai: 可注入的 AI 服务（测试用），默认全局 ai_service

    Returns:
        (grade, 点评文本) —— 契约与脚本路径完全一致。
    """
    llm = await feynman_llm_evaluate(text, kp_name, key_points, ai=ai)
    if llm is not None:
        return llm["grade"], llm["feedback"]
    result = mastery.feynman_grade(text, key_points)
    return result["grade"], feynman_feedback(
        result["grade"], result["covered"], result["missed"]
    )


# ── 认证判分（对齐 mock judgeExam）───────────────────────
# 认证考试（Certification）的题目判分逻辑，支持两种题型：
# 1. mcq（选择题）：答案完全匹配
# 2. 编程题：Judge0 跑测试用例真判分（见上方「Judge0 判题」区块）；
#    本函数是降级路径——去除空白后判断是否包含所有关键片段（includes）


def judge_cert_answer(kind: str, answer: str, correct: str | None, includes: list | None) -> bool:
    """认证题目判分（关键字匹配降级版）。

    这是 Judge0 不可用时的降级路径（code 题）；mcq 题型始终走本函数。
    判分规则因题型而异：
    - mcq（单选题）：答案字符串与正确选项完全相等
    - 编程题：去除所有空白后，判断是否包含所有 key includes 片段
    （Judge0 真判分入口见 judge_cert_code_answer）

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
