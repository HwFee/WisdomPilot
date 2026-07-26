"""训练舱领域服务：判定逻辑、主任务分发、能力轴、智核经济。

判定规则与 frontend/lib/api/deck/mock/ 下的纯函数一一对应
（mock 即本服务的参考实现；cert code 题后续应换 Judge0 真判分）。
"""

import random
import re
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deck import mastery
from app.deck.models import (
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
from app.models import User

BJT = timezone(timedelta(hours=8))  # 自然日按北京时间

AXES = ("review", "debug", "implement")
AXIS_LABELS = {"review": "审阅", "debug": "调试", "implement": "实现"}
TUTOR_COST = 2
CERT_COOLDOWN_DAYS = 3


def today_bjt() -> date:
    return datetime.now(BJT).date()


# ── 能力轴 ──────────────────────────────────────────────


def axis_level(xp: int) -> int:
    return 1 + xp // 400


async def get_axes(db: AsyncSession, user_id: str) -> list[dict]:
    rows = (
        await db.execute(select(DeckAbilityAxis).where(DeckAbilityAxis.user_id == user_id))
    ).scalars().all()
    xp_map = {r.axis: r.xp for r in rows}

    # 每轴短板：p_l 最低的知识点
    mastery_rows = (
        await db.execute(
            select(DeckUserMastery, DeckKnowledgePoint)
            .join(DeckKnowledgePoint, DeckUserMastery.kp_id == DeckKnowledgePoint.id)
            .where(DeckUserMastery.user_id == user_id)
        )
    ).all()
    weakest: dict[str, str] = {}
    for axis in AXES:
        axis_rows = [(m.p_l, kp.name) for m, kp in mastery_rows if kp.axis == axis]
        if axis_rows:
            weakest[axis] = min(axis_rows)[1]

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
                "xp_next": level * 400,
                "weakest_focus": weakest.get(axis),
            }
        )
    return axes


async def add_axis_xp(db: AsyncSession, user_id: str, axis: str, amount: int) -> None:
    row = await db.get(DeckAbilityAxis, {"user_id": user_id, "axis": axis})
    if row is None:
        row = DeckAbilityAxis(user_id=user_id, axis=axis, xp=0)
        db.add(row)
    row.xp += amount


async def has_placement(db: AsyncSession, user_id: str) -> bool:
    count = await db.scalar(
        select(func.count()).select_from(DeckUserMastery).where(
            DeckUserMastery.user_id == user_id
        )
    )
    return bool(count and count > 0)


async def _mastery_events_of(
    db: AsyncSession, user_id: str, kp_id: str
) -> list[mastery.MasteryEvent]:
    """读出某用户某知识点的全部事件（事实源），转成引擎输入"""
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
    """写入一条掌握度事件并重算 p_l/level 缓存。返回 (重算前 p_l, 重算后 p_l, 等级)"""
    row = await db.get(DeckUserMastery, {"user_id": user_id, "kp_id": kp_id})
    p_l_before = row.p_l if row is not None else None
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
    await db.flush()  # 让新事件进入后续查询

    events = await _mastery_events_of(db, user_id, kp_id)
    now = datetime.now(timezone.utc)
    p_l_after = mastery.recall_probability(events, now)
    level = mastery.mastery_level(events, now)
    if row is None:
        row = DeckUserMastery(user_id=user_id, kp_id=kp_id, p_l=p_l_after, level=level)
        db.add(row)
    else:
        row.p_l = p_l_after
        row.level = level
    return p_l_before, p_l_after, level


async def mastery_trends(db: AsyncSession, user_id: str) -> dict[str, str]:
    """各知识点 7 天趋势（无事件的 kp 不出现，调用方按 flat 兜底）"""
    rows = (
        await db.execute(
            select(DeckMasteryEvent).where(DeckMasteryEvent.user_id == user_id)
        )
    ).scalars().all()
    by_kp: dict[str, list[mastery.MasteryEvent]] = {}
    for r in rows:
        by_kp.setdefault(r.kp_id, []).append(
            mastery.MasteryEvent(created_at=r.created_at, correct=bool(r.correct), source=r.source)
        )
    now = datetime.now(timezone.utc)
    return {kp_id: mastery.compute_trend(events, now) for kp_id, events in by_kp.items()}


# ── 智核经济（唯一变动途径）──────────────────────────────


async def change_cores(
    db: AsyncSession, user: User, delta: int, reason: str
) -> int:
    """增减智核并记账，返回新余额。余额不会变负。"""
    new_balance = max(0, user.cores + delta)
    user.cores = new_balance
    db.add(
        DeckCoreTransaction(
            user_id=user.id, delta=delta, reason=reason, balance_after=new_balance
        )
    )
    return new_balance


async def today_cores_used(db: AsyncSession, user_id: str) -> int:
    total = await db.scalar(
        select(func.coalesce(func.sum(DeckCoreTransaction.delta), 0)).where(
            DeckCoreTransaction.user_id == user_id,
            DeckCoreTransaction.delta < 0,
            func.date(DeckCoreTransaction.created_at) == today_bjt().isoformat(),
        )
    )
    return abs(int(total or 0))


# ── 活动 / 动态 ─────────────────────────────────────────


async def touch_activity(
    db: AsyncSession, user_id: str, *, minutes: int = 0, correct: int = 0
) -> None:
    row = await db.get(DeckDailyActivity, {"user_id": user_id, "day": today_bjt()})
    if row is None:
        row = DeckDailyActivity(user_id=user_id, day=today_bjt(), minutes=0, exercises=0, correct=0)
        db.add(row)
    row.minutes += minutes
    row.exercises += 1
    row.correct += correct


async def add_feed(db: AsyncSession, user_id: str, kind: str, segments: list[dict]) -> None:
    db.add(DeckFeedEvent(user_id=user_id, kind=kind, payload={"segments": segments}))


def feed_time_label(created_at: datetime) -> str:
    now = datetime.now(BJT)
    created = created_at.replace(tzinfo=timezone.utc).astimezone(BJT)
    days = (now.date() - created.date()).days
    if days == 0:
        return created.strftime("%H:%M")
    if days == 1:
        return "昨天"
    return f"{days}天前"


# ── 段位 ────────────────────────────────────────────────

TIER_TABLE = [
    (2400, "王者"),
    (2100, "钻石"),
    (1800, "铂金 II"),
    (1500, "黄金"),
    (1200, "白银"),
    (0, "青铜"),
]


def tier_of(rating: int) -> str:
    for threshold, name in TIER_TABLE:
        if rating >= threshold:
            return name
    return "青铜"


async def get_or_create_rating(db: AsyncSession, user_id: str) -> DeckArenaRating:
    row = await db.get(DeckArenaRating, user_id)
    if row is None:
        row = DeckArenaRating(user_id=user_id, rating=1200, win_streak=0)
        db.add(row)
        await db.flush()
    return row


async def week_rank(db: AsyncSession, rating: int) -> int:
    higher = await db.scalar(
        select(func.count()).select_from(DeckArenaRating).where(DeckArenaRating.rating > rating)
    )
    return int(higher or 0) + 1


# ── 审查判定（对齐 mock judgeMarks）──────────────────────


def judge_marks(defects: list[dict], marks: list[dict]) -> dict:
    hits, missed, false_alarms = [], [], []
    used: set[int] = set()
    for defect in defects:
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
    false_alarms = [m for i, m in enumerate(marks) if i not in used]

    precision = 1.0 if not marks else 1 - len(false_alarms) / len(marks)
    score = round(len(hits) / len(defects) * 70 + precision * 30)
    accuracy = 0.0 if not marks else len(hits) / len(marks)
    return {"hits": hits, "missed": missed, "false_alarms": false_alarms,
            "score": score, "accuracy": accuracy}


# ── 竞技场判定（对齐 mock judgeArenaCode；后续换 Judge0）──


ARENA_SOLVED_OUTPUT = """$ pytest test_median.py -v
test_median.py::test_odd            PASSED   [ 20%]
test_median.py::test_single         PASSED   [ 40%]
test_median.py::test_even           PASSED   [ 60%]
test_median.py::test_even_negative  PASSED   [ 80%]
test_median.py::test_even_unsorted  PASSED   [100%]

======================== 5 passed in 0.08s ========================"""

ARENA_PARTIAL_OUTPUT = """$ pytest test_median.py -v
test_median.py::test_even           FAILED   assert 5.0 == 4.5
test_median.py::test_even_negative  FAILED   assert -4.0 == -4.5

=================== 3 passed, 2 failed in 0.11s ===================
右中位索引还有问题：偶数个时中间两个是 nums[mid-1] 和 nums[mid]。"""


def judge_arena_code(code: str, failing_output: str) -> dict:
    normalized = re.sub(r"\s+", "", code)
    rule_loop = "lo=mid-1" in normalized
    rule_index = "nums[lo]+nums[mid])" in normalized
    if rule_loop and rule_index:
        return {"passed": 5, "total": 5, "output": ARENA_SOLVED_OUTPUT,
                "solved": True, "score_delta": 23}
    if rule_loop:
        return {"passed": 3, "total": 5, "output": ARENA_PARTIAL_OUTPUT,
                "solved": False, "score_delta": 0}
    return {"passed": 2, "total": 5, "output": failing_output,
            "solved": False, "score_delta": 0}


# ── 导师脚本（后续换 LLM 追问）───────────────────────────

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

GENERIC_PROBES = [
    "在你给出答案之前——你觉得这段代码最可能在哪一类输入上出错？",
    "你说的「正确」具体指什么？我们怎么验证它？",
    "如果输入规模放大 1000 倍，你的方案还成立吗？哪一步先撑不住？",
    "试着构造一个让自己代码出错的反例。最小的那个是什么？",
    "如果让你给这段代码写三条测试用例，你会先写哪三条？为什么？",
]


def socratic_reply(text: str, history_len: int) -> str:
    for keys, reply in KEYWORD_PROBES:
        if any(k in text for k in keys):
            return reply
    return GENERIC_PROBES[history_len % len(GENERIC_PROBES)]


def feynman_opening(topic: str) -> str:
    return f"好，「{topic}」。用你自己的话讲给我听——假装你在教一个完全不懂编程的人。不许用术语搪塞，讲到他能复述为止。"


def feynman_feedback(grade: str, covered: list[str], missed: list[str]) -> str:
    """按评分结果生成点评：点明已覆盖/缺失的要点"""
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


def judge_cert_answer(kind: str, answer: str, correct: str | None, includes: list | None) -> bool:
    if kind == "mcq":
        return answer == (correct or "")
    normalized = re.sub(r"\s+", "", answer)
    return all(re.sub(r"\s+", "", frag) in normalized for frag in (includes or []))


def new_verify_code(topic_prefix: str) -> str:
    return f"{topic_prefix}-{''.join(random.choices('0123456789ABCDEF', k=4))}"


# ── 连续训练天数 ─────────────────────────────────────────


async def streak_days(db: AsyncSession, user_id: str) -> int:
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
    expected = today_bjt()
    for day in rows:
        if day == expected:
            streak += 1
            expected -= timedelta(days=1)
        elif day < expected:
            break
    return streak


async def next_cert_available_days(db: AsyncSession, user_id: str) -> int | None:
    last = (
        await db.execute(
            select(DeckCertification.created_at)
            .where(DeckCertification.user_id == user_id)
            .order_by(DeckCertification.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if last is None:
        return None
    elapsed = (today_bjt() - last.replace(tzinfo=timezone.utc).astimezone(BJT).date()).days
    return max(0, CERT_COOLDOWN_DAYS - elapsed)


async def attempts_today(db: AsyncSession, user_id: str) -> tuple[int, float]:
    """审查室今日完成数与平均准确率"""
    rows = (
        await db.execute(
            select(DeckReviewAttempt.verdict).where(
                DeckReviewAttempt.user_id == user_id,
                func.date(DeckReviewAttempt.created_at) == today_bjt().isoformat(),
            )
        )
    ).scalars().all()
    if not rows:
        return 0, 0.0
    avg = sum(v.get("accuracy", 0) for v in rows) / len(rows)
    return len(rows), avg
