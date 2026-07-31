# ──────────────────────────────────────────────────────────────────
# 掌握度纯函数引擎（mastery.py）
# ──────────────────────────────────────────────────────────────────
# 本文件实现了训练舱的"记忆模型"，是整个平台学习效果追踪的核心算法。
#
# 设计理念：
#   - 事件溯源（Event Sourcing）：deck_mastery_events 事件表是唯一事实源，
#     DeckUserMastery 缓存表只是本模块计算结果的快照。
#   - 纯函数：本模块所有函数不碰数据库、不产生副作用，
#     输入是事件列表 + 当前时间，输出是掌握度指标，方便单元测试和数学推理。
#
# 两套算法：
#   1. HLR（Half-Life Regression）记忆模型：
#      - 模拟人类记忆遗忘曲线，用"半衰期"衡量知识遗忘速度
#      - 答对 -> 半衰期增长（记得更久）/ 答错 -> 半衰期缩短（忘得更快）
#      - 回忆概率 p = 2^(-Δ/h)，Δ=距上次答对天数，h=当前半衰期
#   2. Khan 式四级掌握等级（初识/熟悉/熟练/精通）：
#      - 不仅看回忆概率，还看答对次数、间隔重复、实战来源
#      - 精通级别要求最严格，纯费曼讲述永远到不了精通
#
# 参考论文：Settles & Meeder (2016) "A Trainable Spaced Reproduction Model
#           for Language Learning"（HLR 原始论文）
# ──────────────────────────────────────────────────────────────────

"""掌握度纯函数引擎：HLR（半衰期回归）记忆模型 + Khan 式掌握等级。

不碰数据库——输入是事件记录序列（created_at/correct/source），输出是
回忆概率、掌握等级、趋势与费曼评级。事件表 deck_mastery_events 是事实源，
DeckUserMastery 只是本模块计算结果的缓存。
"""

# dataclass：定义轻量级数据容器（MasteryEvent，与 ORM 模型解耦）
from dataclasses import dataclass
# datetime：事件时间戳和"当前时间"参数的类型
from datetime import datetime

# ── 半衰期（HLR）参数 ────────────────────────────────────
# HLR（Half-Life Regression）模型：模拟人类记忆的遗忘-巩固曲线。
# 核心思想：每次答题（正确/错误）会改变知识的"半衰期"，
#           半衰期越长 = 记忆越持久 = 遗忘越慢。

# 首次接触后的初始半衰期（天）。用户第一次答对某知识点后，
# 半衰期为 1 天，即 1 天后回忆概率降至 50%。
INITIAL_HALF_LIFE_DAYS = 1.0   # 首次接触后的初始半衰期
# 答对增长倍率：每次答对，半衰期乘以 1.8（记忆更持久）
# 数学效果：1 → 1.8 → 3.24 → 5.83 → ... 逐步逼近上限
HALF_LIFE_GROWTH = 1.8         # 答对一次半衰期倍率
# 答错衰减倍率：每次答错，半衰期乘以 0.5（记忆更快遗忘）
# 一次答对建立的半衰期，需 2-3 次连续答错才会完全消退
HALF_LIFE_DECAY = 0.5          # 答错一次半衰期倍率
# 半衰期上限：防止持续答对导致半衰期无限增长
# 180 天约等于半个学年，届时即使不再练习也有较高回忆概率
HALF_LIFE_MAX_DAYS = 180.0     # 半衰期上限（约半年）
# 半衰期下限：防止答错太多导致半衰期趋近 0
# 0.2 天约 5 小时，避免回忆概率在极端情况下剧烈波动
HALF_LIFE_MIN_DAYS = 0.2       # 半衰期下限
# 从未答对时的偏置天数：当用户一直在答错（没有一次 correct），
# Δ 计算为 "距首次事件天数 + 1"，避免 Δ=0 导致 p=1 的不合理情况
NO_CORRECT_OFFSET_DAYS = 1.0   # 从未答对时 Δ 在距首次事件天数上加的偏置

# ── 掌握等级阈值 ─────────────────────────────────────────
# 四级掌握度判定：借鉴 Khan Academy 的分级思想，
# 综合回忆概率、答对次数、间隔重复和实战来源四个维度。

# 等级名称（从低到高），与前端展示保持一致
LEVELS = ("初识", "熟悉", "熟练", "精通")
# "熟悉"门槛：回忆概率 ≥ 0.3，即约 1-2 天前学过的内容还记得
P_FAMILIAR = 0.3               # 熟悉：回忆概率下限
# "熟练"门槛：回忆概率 ≥ 0.6，学习效果已稳定
P_PROFICIENT = 0.6             # 熟练：回忆概率下限
# "熟练"额外要求：至少答对 3 次，防止碰运气升到熟练
PROFICIENT_MIN_CORRECT = 3     # 熟练：最少答对次数
# "精通"门槛：回忆概率 ≥ 0.8，近乎完全掌握
P_MASTER = 0.8                 # 精通：回忆概率下限
# "精通"额外要求：至少答对 4 次，且不是集中刷题
MASTER_MIN_CORRECT = 4         # 精通：最少答对次数
# "精通"的间隔重复条件：必须存在一对间隔 ≥3 天的答对
# 含义：不是一次性刷题，而是真正跨天复习过
SPACED_PAIR_GAP_DAYS = 3.0     # 精通：间隔重复成功对的最小间隔（天）
# 实战来源（非纯讲述）：精通要求至少一次实战答题
# review_gym=代码审查室 / arena=调试竞技场 / certification=认证考试
# 纯费曼讲述（"考考我"模式）永远到不了精通，这是一个有意的设计决策
PRACTICAL_SOURCES = frozenset({"review_gym", "arena", "certification"})  # 实战来源

# ── 趋势 ─────────────────────────────────────────────────
# 趋势判定：比较"现在"与"7 天前"的回忆概率，
# 判断用户对该知识点的掌握是在上升、下降还是平稳。

# 回看窗口：取 7 天前的事件快照计算当时的回忆概率
TREND_WINDOW_DAYS = 7.0        # 对比窗口：现在 vs 7 天前
# 趋势判定精度：变化量超过 0.02 才算 up/down
# 小于此值视为 flat（平稳），避免浮点精度噪声导致误判
TREND_EPSILON = 0.02           # 判定 up/down 的最小变化量

# ── 费曼评分 ─────────────────────────────────────────────
# 费曼检验评分：在苏格拉底导师的"考考我"模式中使用。
# 评分两个维度：(1) 要点覆盖率——用户是否讲到了关键知识点；
#               (2) 结构分——是否包含因果推理和举例说明。

# "优秀"条件：覆盖率 ≥ 80% 且需要有结构分
COVERAGE_EXCELLENT = 0.8       # 优秀：要点覆盖率下限（且需结构分）
# "良好"条件（无结构分）：覆盖率达到一半即可
COVERAGE_GOOD = 0.5            # 良好：要点覆盖率下限
# "良好"条件（有结构分）：有逻辑推理可放宽覆盖率要求到 34%
COVERAGE_GOOD_WITH_STRUCTURE = 0.34  # 良好：有结构分时的覆盖率下限
# 因果推理标志词：包含这些词说明用户在解释"为什么"
CAUSAL_MARKERS = ("因为", "所以", "否则", "如果")
# 举例说明标志词：包含这些词说明用户在提供具体例证
EXAMPLE_MARKERS = ("比如", "例如", "假设", "当")


@dataclass(frozen=True)
class MasteryEvent:
    """一条掌握度事件（与 DeckMasteryEvent 同构，纯数据）。

    设计为纯数据容器（frozen=True 不可变），与数据库 ORM 模型解耦。
    本模块所有函数只接受 MasteryEvent 列表，不依赖任何数据库连接，
    这使得算法可以脱离数据库独立测试和推理。

    Attributes:
        created_at: 事件发生时间（datetime），HLR 模型计算时间衰减的核心输入。
        correct: 是否答对（bool），True 则半衰期增长，False 则缩短。
        source: 事件来源（str），用于精通判定的实战来源检查。
               可选值：review_gym / arena / feynman / certification / placement。
    """

    created_at: datetime
    correct: bool
    source: str


def _days_between(earlier: datetime, later: datetime) -> float:
    """两个时间之间的天数（忽略时区，统一按朴素时间比较）。

    计算逻辑：(later - earlier) 的秒数 / 86400（一天的秒数）。
    使用 replace(tzinfo=None) 剥离时区信息，避免 DST 边界问题。

    Args:
        earlier: 较早的时间点。
        later: 较晚的时间点。

    Returns:
        float: 两时间点间隔的天数，始终 ≥ 0。
    """
    # 剥离时区后相减得到 timedelta，再转换为天（秒 / 86400）
    return (later.replace(tzinfo=None) - earlier.replace(tzinfo=None)).total_seconds() / 86400


def _sort_events(events: list[MasteryEvent]) -> list[MasteryEvent]:
    """按事件创建时间升序排列事件列表。

    HLR 模型是顺序敏感的——事件发生的先后直接影响半衰期演变路径。
    答对/答错的影响是按时间顺序累积的，所以必须先排序再计算。

    Args:
        events: 待排序的事件列表。

    Returns:
        list[MasteryEvent]: 按 created_at 升序排列的事件列表。
    """
    return sorted(events, key=lambda e: e.created_at)


def half_life_days(events: list[MasteryEvent]) -> float:
    """按事件序列重放半衰期：答对 ×1.8（封顶 180 天），答错 ×0.5（保底 0.2 天）。

    这是 HLR 模型的核心算法。按时间顺序逐条处理事件：
    - 答对 → h = min(h * 1.8, 180)：半衰期增长但不超过上限
    - 答错 → h = max(h * 0.5, 0.2)：半衰期缩短但不低于下限

    Args:
        events: 同一用户同一知识点的全部事件（不要求已排序，内部会排序）。

    Returns:
        float: 当前半衰期（天）。值越大表示记忆越持久。
    """
    # 从初始半衰期开始
    h = INITIAL_HALF_LIFE_DAYS
    # 按时间顺序逐个重放事件，累积更新半衰期
    for event in _sort_events(events):
        if event.correct:
            h = min(h * HALF_LIFE_GROWTH, HALF_LIFE_MAX_DAYS)
        else:
            h = max(h * HALF_LIFE_DECAY, HALF_LIFE_MIN_DAYS)
    return h


def recall_probability(events: list[MasteryEvent], now: datetime) -> float:
    """当前回忆概率 p = 2^(-Δ/h)。

    公式含义：类似放射性衰变，回忆概率以半衰期方式衰减。
    - 刚答对时（Δ ≈ 0），p ≈ 1（几乎确定能回忆）
    - 经过 h 天后（Δ = h），p = 2^(-1) = 0.5（一半概率能回忆）
    - 经过 2h 天后（Δ = 2h），p = 2^(-2) = 0.25（四分之一的概率）
    - 经过 5h 天后（Δ = 5h），p ≈ 0.03（几乎不可能回忆）

    Δ（delta）的计算：
    - 有答对记录：Δ = 当前时间 - 最近一次答对时间
    - 无答对记录：Δ = 当前时间 - 首次事件时间 + 1 天偏移

    Args:
        events: 同一用户同一知识点的全部事件。
        now: 当前时间点（通常为 utc_now()）。

    Returns:
        float: 回忆概率 p_l，范围 [0, 1]。
    """
    # 空事件列表：用户从未接触过此知识点，回忆概率为 0
    if not events:
        return 0.0
    # 按时间排序，保证计算的一致性
    ordered = _sort_events(events)
    # 先算出当前半衰期（基于全部事件序列）
    h = half_life_days(ordered)
    # 筛选出所有答对事件，用于计算 Δ
    correct_events = [e for e in ordered if e.correct]
    if correct_events:
        # 有答对记录：Δ = 距最近一次答对的天数
        # max(0.0, ...) 确保 Δ 不会为负（当 now 比事件时间还早时）
        delta = max(0.0, _days_between(correct_events[-1].created_at, now))
    else:
        # 从未答对：Δ = 距首次事件天数 + 1 天偏置
        # +1 避免首次事件刚发生时的 Δ=0 导致 p=1.0 不合理
        delta = max(0.0, _days_between(ordered[0].created_at, now)) + NO_CORRECT_OFFSET_DAYS
    # 回忆概率公式：p = 2^(-Δ/h)
    return 2 ** (-delta / h)


def _has_spaced_success_pair(correct_events: list[MasteryEvent]) -> bool:
    """是否存在一对间隔 ≥3 天的答对事件。

    这是精通判定的条件之一：用户必须在不同日子成功过，
    证明不是靠短期记忆刷题，而是真正掌握了知识。
    使用双重循环（O(n²)），但单个知识点的答对事件通常很少（<100），
    所以性能不是问题。

    Args:
        correct_events: 按时间排序的所有答对事件。

    Returns:
        bool: 存在间隔 ≥3 天的答对对返回 True，否则 False。
    """
    # 对每对 (i, j) 其中 j > i，检查时间间隔
    for i, earlier in enumerate(correct_events):
        for later in correct_events[i + 1:]:
            if _days_between(earlier.created_at, later.created_at) >= SPACED_PAIR_GAP_DAYS:
                return True
    return False


def mastery_level(events: list[MasteryEvent], now: datetime) -> str:
    """Khan 式四级掌握：初识/熟悉/熟练/精通。

    判定规则（按优先级，逐层过滤）：
    1. 无事件 → 初识
    2. p < 0.3 → 初识
    3. p < 0.6 或 答对 < 3 次 → 熟悉
    4. p < 0.8 或 答对 < 4 次 → 熟练
    5. 无间隔重复成功对 → 熟练
    6. 无实战来源答对 → 熟练
    7. 以上全部满足 → 精通

    关键设计决策：精通要求至少一次实战（review_gym/arena/certification），
    这意味着纯靠费曼讲述永远到不了精通——用户必须真正动手实践。
    这符合"10% 学、70% 练、20% 复盘"的产品设计理念。

    Args:
        events: 同一用户同一知识点的全部事件。
        now: 当前时间点。

    Returns:
        str: 掌握等级（"初识" / "熟悉" / "熟练" / "精通"）。
    """
    if not events:
        return "初识"
    # 计算当前回忆概率
    p = recall_probability(events, now)
    if p < P_FAMILIAR:
        return "初识"
    # 筛选所有答对事件，用于后续条件判断
    correct_events = [e for e in _sort_events(events) if e.correct]
    if p < P_PROFICIENT or len(correct_events) < PROFICIENT_MIN_CORRECT:
        return "熟悉"
    if p < P_MASTER or len(correct_events) < MASTER_MIN_CORRECT:
        return "熟练"
    # 精通级别额外检查：间隔重复
    if not _has_spaced_success_pair(correct_events):
        return "熟练"
    # 精通级别额外检查：实战来源
    if not any(e.source in PRACTICAL_SOURCES for e in correct_events):
        return "熟练"
    return "精通"


def compute_trend(events: list[MasteryEvent], now: datetime) -> str:
    """趋势：现在的 p 与 7 天前（只计入当时已发生的事件）的 p 之差。

    计算逻辑：
    1. 取 7 天前的 cutoff 时间点
    2. 筛选出 cutoff 之前发生的所有事件（模拟 7 天前的"已知信息"）
    3. 用当时的事件计算当时的回忆概率
    4. 与现在的回忆概率比较差值

    趋势含义：
    - "up"：你现在比 7 天前更可能回忆起这个知识（正在进步）
    - "down"：你现在比 7 天前更可能遗忘这个知识（需要复习）
    - "flat"：变化很小（±0.02 以内），保持稳定

    注意：past_events 只取 cutoff 之前的事件——7 天前"你不可能知道自己
          未来会答对或答错"，这是一种保守的因果视角。

    Args:
        events: 同一用户同一知识点的全部事件。
        now: 当前时间点。

    Returns:
        str: 趋势方向（"up" / "down" / "flat"）。
    """
    from datetime import timedelta

    # 计算 7 天前的截止时间点
    cutoff = now - timedelta(days=TREND_WINDOW_DAYS)
    # 筛选 cutoff 之前的事件：模拟 7 天前"已知的信息"
    # 去掉时区避免比较时的类型不匹配问题
    past_events = [e for e in events if e.created_at.replace(tzinfo=None) <= cutoff.replace(tzinfo=None)]
    # 计算现在的回忆概率与 7 天前的回忆概率之差
    diff = recall_probability(events, now) - recall_probability(past_events, cutoff)
    # 与阈值（±0.02）比较，判定趋势方向
    if diff > TREND_EPSILON:
        return "up"
    if diff < -TREND_EPSILON:
        return "down"
    return "flat"


def feynman_grade_from_coverage(
    coverage: float, structure: bool, has_points: bool
) -> str:
    """费曼评级量规：按要点覆盖率 + 结构分定级（LLM 评分与关键词评分共用）。

    规则（与 docs/backend-api/01 §5 对齐）：
    - 未配置要点（has_points=False）：只看结构分 → 有结构"良好"，否则"待加强"
    - 覆盖 ≥80% 且有结构 → "优秀"
    - 覆盖 ≥50%，或 ≥1/3 且有结构 → "良好"
    - 其余 → "待加强"

    抽成独立纯函数是为了让 LLM 评分路径与关键词评分路径使用同一套
    量规，避免两处规则漂移。

    Args:
        coverage: 已覆盖要点数 / 总要点数（0~1 之间的浮点数）。
        structure: 是否同时具备因果推理词与举例说明词。
        has_points: 是否配置了评分要点（False 表示该知识点无要点配置）。

    Returns:
        评级字符串：优秀 / 良好 / 待加强。
    """
    if not has_points:
        return "良好" if structure else "待加强"
    if coverage >= COVERAGE_EXCELLENT and structure:
        return "优秀"
    if coverage >= COVERAGE_GOOD or (
        coverage >= COVERAGE_GOOD_WITH_STRUCTURE and structure
    ):
        return "良好"
    return "待加强"


def feynman_grade(text: str, key_points: list[dict] | None) -> dict:
    """费曼检验评分：要点覆盖率 + 结构分（同义词关键词匹配）。

    费曼技巧的本质：如果你无法用简单的语言向别人解释清楚一个概念，
    说明你还没有真正掌握它。本函数量化了这一检验过程。

    评分两个维度：
    A. 要点覆盖率：用户是否讲到了知识点的关键要点？
       - 每个要点配置了同义词列表，用户文本中命中任一关键词即算覆盖
    B. 结构分：用户的表达是否有逻辑？
       - 必须同时包含因果推理词（"因为""所以"等）和举例说明词（"比如""例如"等）
       - 结构分的设计依据：费曼本人强调的"用自己的话"需要包含推理和例证

    评级规则见 ``feynman_grade_from_coverage``（关键词匹配与 LLM 评分共用）。

    Args:
        text: 用户讲述的文本内容。
        key_points: 知识点配置的评分要点列表，每项为 {"keys": [...], "label": "..."}。
                    None 表示未配置要点。

    Returns:
        dict: {"grade": 评级, "covered": 已覆盖要点标签列表,
               "missed": 缺失要点标签列表, "structure": 是否有结构分}。
    """
    # 检查是否同时包含因果标记和举例标记
    # any(m in text for m in MARKERS) 是 O(n) 字符串搜索，对中文短文本足够快
    structure = any(m in text for m in CAUSAL_MARKERS) and any(
        m in text for m in EXAMPLE_MARKERS
    )
    # 遍历每个评分要点，检查是否在文本中命中
    covered, missed = [], []
    for point in key_points or []:
        # 对每个要点，检查其同义词列表中是否有任一命中
        if any(key in text for key in point.get("keys", [])):
            covered.append(point["label"])
        else:
            missed.append(point["label"])

    # 计算要点覆盖率并套用量规定级（无要点时走纯结构分）
    coverage = len(covered) / len(key_points) if key_points else 0.0
    grade = feynman_grade_from_coverage(coverage, structure, bool(key_points))

    # 返回完整评分结果，供前端展示点评文案
    return {"grade": grade, "covered": covered, "missed": missed, "structure": structure}
