"""掌握度纯函数引擎：HLR（半衰期回归）记忆模型 + Khan 式掌握等级。

不碰数据库——输入是事件记录序列（created_at/correct/source），输出是
回忆概率、掌握等级、趋势与费曼评级。事件表 deck_mastery_events 是事实源，
DeckUserMastery 只是本模块计算结果的缓存。
"""

from dataclasses import dataclass
from datetime import datetime

# ── 半衰期（HLR）参数 ────────────────────────────────────

INITIAL_HALF_LIFE_DAYS = 1.0   # 首次接触后的初始半衰期
HALF_LIFE_GROWTH = 1.8         # 答对一次半衰期倍率
HALF_LIFE_DECAY = 0.5          # 答错一次半衰期倍率
HALF_LIFE_MAX_DAYS = 180.0     # 半衰期上限（约半年）
HALF_LIFE_MIN_DAYS = 0.2       # 半衰期下限
NO_CORRECT_OFFSET_DAYS = 1.0   # 从未答对时 Δ 在距首次事件天数上加的偏置

# ── 掌握等级阈值 ─────────────────────────────────────────

LEVELS = ("初识", "熟悉", "熟练", "精通")
P_FAMILIAR = 0.3               # 熟悉：回忆概率下限
P_PROFICIENT = 0.6             # 熟练：回忆概率下限
PROFICIENT_MIN_CORRECT = 3     # 熟练：最少答对次数
P_MASTER = 0.8                 # 精通：回忆概率下限
MASTER_MIN_CORRECT = 4         # 精通：最少答对次数
SPACED_PAIR_GAP_DAYS = 3.0     # 精通：间隔重复成功对的最小间隔（天）
PRACTICAL_SOURCES = frozenset({"review_gym", "arena", "certification"})  # 实战来源

# ── 趋势 ─────────────────────────────────────────────────

TREND_WINDOW_DAYS = 7.0        # 对比窗口：现在 vs 7 天前
TREND_EPSILON = 0.02           # 判定 up/down 的最小变化量

# ── 费曼评分 ─────────────────────────────────────────────

COVERAGE_EXCELLENT = 0.8       # 优秀：要点覆盖率下限（且需结构分）
COVERAGE_GOOD = 0.5            # 良好：要点覆盖率下限
COVERAGE_GOOD_WITH_STRUCTURE = 0.34  # 良好：有结构分时的覆盖率下限
CAUSAL_MARKERS = ("因为", "所以", "否则", "如果")
EXAMPLE_MARKERS = ("比如", "例如", "假设", "当")


@dataclass(frozen=True)
class MasteryEvent:
    """一条掌握度事件（与 DeckMasteryEvent 同构，纯数据）"""

    created_at: datetime
    correct: bool
    source: str


def _days_between(earlier: datetime, later: datetime) -> float:
    """两个时间之间的天数（忽略时区，统一按朴素时间比较）"""
    return (later.replace(tzinfo=None) - earlier.replace(tzinfo=None)).total_seconds() / 86400


def _sort_events(events: list[MasteryEvent]) -> list[MasteryEvent]:
    return sorted(events, key=lambda e: e.created_at)


def half_life_days(events: list[MasteryEvent]) -> float:
    """按事件序列重放半衰期：答对 ×1.8（封顶 180 天），答错 ×0.5（保底 0.2 天）"""
    h = INITIAL_HALF_LIFE_DAYS
    for event in _sort_events(events):
        if event.correct:
            h = min(h * HALF_LIFE_GROWTH, HALF_LIFE_MAX_DAYS)
        else:
            h = max(h * HALF_LIFE_DECAY, HALF_LIFE_MIN_DAYS)
    return h


def recall_probability(events: list[MasteryEvent], now: datetime) -> float:
    """当前回忆概率 p = 2^(-Δ/h)。

    Δ = 距最近一次答对的天数；从未答对时 Δ = 距首次事件天数 + 1。
    """
    if not events:
        return 0.0
    ordered = _sort_events(events)
    h = half_life_days(ordered)
    correct_events = [e for e in ordered if e.correct]
    if correct_events:
        delta = max(0.0, _days_between(correct_events[-1].created_at, now))
    else:
        delta = max(0.0, _days_between(ordered[0].created_at, now)) + NO_CORRECT_OFFSET_DAYS
    return 2 ** (-delta / h)


def _has_spaced_success_pair(correct_events: list[MasteryEvent]) -> bool:
    """是否存在一对间隔 ≥3 天的答对事件"""
    for i, earlier in enumerate(correct_events):
        for later in correct_events[i + 1:]:
            if _days_between(earlier.created_at, later.created_at) >= SPACED_PAIR_GAP_DAYS:
                return True
    return False


def mastery_level(events: list[MasteryEvent], now: datetime) -> str:
    """Khan 式四级掌握：初识/熟悉/熟练/精通。

    精通需要：p≥0.8、答对 ≥4 次、至少一对间隔 3 天的答对、且至少一次
    实战来源（review_gym/arena/certification）答对——纯费曼永远到不了精通。
    """
    if not events:
        return "初识"
    p = recall_probability(events, now)
    if p < P_FAMILIAR:
        return "初识"
    correct_events = [e for e in _sort_events(events) if e.correct]
    if p < P_PROFICIENT or len(correct_events) < PROFICIENT_MIN_CORRECT:
        return "熟悉"
    if p < P_MASTER or len(correct_events) < MASTER_MIN_CORRECT:
        return "熟练"
    if not _has_spaced_success_pair(correct_events):
        return "熟练"
    if not any(e.source in PRACTICAL_SOURCES for e in correct_events):
        return "熟练"
    return "精通"


def compute_trend(events: list[MasteryEvent], now: datetime) -> str:
    """趋势：现在的 p 与 7 天前（只计入当时已发生的事件）的 p 之差"""
    from datetime import timedelta

    cutoff = now - timedelta(days=TREND_WINDOW_DAYS)
    past_events = [e for e in events if e.created_at.replace(tzinfo=None) <= cutoff.replace(tzinfo=None)]
    diff = recall_probability(events, now) - recall_probability(past_events, cutoff)
    if diff > TREND_EPSILON:
        return "up"
    if diff < -TREND_EPSILON:
        return "down"
    return "flat"


def feynman_grade(text: str, key_points: list[dict] | None) -> dict:
    """费曼检验评分：要点覆盖率 + 结构分（因果词 + 举例词）。

    key_points: [{"keys": [同义词...], "label": 要点名}]。返回评级与
    已覆盖/缺失要点标签，供点评文案引用。
    """
    structure = any(m in text for m in CAUSAL_MARKERS) and any(
        m in text for m in EXAMPLE_MARKERS
    )
    covered, missed = [], []
    for point in key_points or []:
        if any(key in text for key in point.get("keys", [])):
            covered.append(point["label"])
        else:
            missed.append(point["label"])

    if not key_points:
        # 未配置要点的知识点：只看结构
        grade = "良好" if structure else "待加强"
    else:
        coverage = len(covered) / len(key_points)
        if coverage >= COVERAGE_EXCELLENT and structure:
            grade = "优秀"
        elif coverage >= COVERAGE_GOOD or (
            coverage >= COVERAGE_GOOD_WITH_STRUCTURE and structure
        ):
            grade = "良好"
        else:
            grade = "待加强"

    return {"grade": grade, "covered": covered, "missed": missed, "structure": structure}
