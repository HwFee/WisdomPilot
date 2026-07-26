"""deck 掌握度引擎（app/deck/mastery.py）纯函数测试。

HLR 半衰期、回忆概率、掌握等级、趋势、费曼评分——全部不碰数据库。
"""

from datetime import datetime, timedelta

from app.deck.mastery import (
    HALF_LIFE_MAX_DAYS,
    HALF_LIFE_MIN_DAYS,
    INITIAL_HALF_LIFE_DAYS,
    MasteryEvent,
    compute_trend,
    feynman_grade,
    half_life_days,
    mastery_level,
    recall_probability,
)

NOW = datetime(2026, 7, 26, 12, 0, 0)


def ev(days_ago: float, correct: bool, source: str = "review_gym") -> MasteryEvent:
    return MasteryEvent(created_at=NOW - timedelta(days=days_ago), correct=correct, source=source)


# ── 半衰期 ───────────────────────────────────────────────


class TestHalfLife:
    def test_no_events_returns_initial(self):
        assert half_life_days([]) == INITIAL_HALF_LIFE_DAYS

    def test_correct_grows_half_life(self):
        h = half_life_days([ev(2, True)])
        assert h == INITIAL_HALF_LIFE_DAYS * 1.8

    def test_wrong_shrinks_half_life(self):
        h = half_life_days([ev(2, False)])
        assert h == INITIAL_HALF_LIFE_DAYS * 0.5

    def test_wrong_after_correct_cancels_one_growth(self):
        h = half_life_days([ev(2, True), ev(1, False)])
        assert abs(h - INITIAL_HALF_LIFE_DAYS * 1.8 * 0.5) < 1e-9

    def test_replay_respects_chronological_order_not_input_order(self):
        # 传入顺序打乱，结果应按 created_at 重放
        ordered = half_life_days([ev(2, False), ev(1, True)])
        shuffled = half_life_days([ev(1, True), ev(2, False)])
        assert ordered == shuffled

    def test_half_life_capped_at_max(self):
        h = half_life_days([ev(20 - i, True) for i in range(20)])
        assert h == HALF_LIFE_MAX_DAYS

    def test_half_life_floored_at_min(self):
        h = half_life_days([ev(20 - i, False) for i in range(20)])
        assert h == HALF_LIFE_MIN_DAYS


# ── 回忆概率 ─────────────────────────────────────────────


class TestRecallProbability:
    def test_no_events_is_zero(self):
        assert recall_probability([], NOW) == 0.0

    def test_just_answered_correct_is_near_one(self):
        p = recall_probability([ev(0, True)], NOW)
        assert p > 0.99

    def test_decays_over_time(self):
        events = [ev(0, True)]
        p_now = recall_probability(events, NOW)
        p_later = recall_probability(events, NOW + timedelta(days=5))
        assert p_later < p_now

    def test_one_half_life_gives_half(self):
        # 答对一次 h=1.8 天；1.8 天后 p 应约为 0.5
        p = recall_probability([ev(1.8, True)], NOW)
        assert abs(p - 0.5) < 0.01

    def test_never_correct_uses_first_event_plus_offset(self):
        # 从未答对：Δ = 距首次事件天数 + 1，h=0.5（一次答错）
        p = recall_probability([ev(1, False)], NOW)
        assert abs(p - 2 ** (-(1 + 1) / 0.5)) < 1e-9

    def test_result_within_unit_interval(self):
        events = [ev(10, False), ev(9, True), ev(8, False), ev(1, True)]
        p = recall_probability(events, NOW)
        assert 0.0 <= p <= 1.0


# ── 掌握等级 ─────────────────────────────────────────────


class TestMasteryLevel:
    def test_no_events_is_chushi(self):
        assert mastery_level([], NOW) == "初识"

    def test_low_probability_is_chushi(self):
        # 很久以前答对一次，早已遗忘
        assert mastery_level([ev(30, True)], NOW) == "初识"

    def test_recent_correct_is_shuxi(self):
        assert mastery_level([ev(0, True)], NOW) == "熟悉"

    def test_proficient_needs_three_correct_and_p(self):
        # 3 次近期答对，h=1.8^3，p≈1 → 熟练；不足 4 次到不了精通
        events = [ev(2, True), ev(1, True), ev(0, True)]
        assert mastery_level(events, NOW) == "熟练"

    def test_master_requires_practical_source(self):
        # 4 次答对含间隔对，但全是 feynman → 永远到不了精通
        feynman_only = [ev(4, True, "feynman"), ev(3, True, "feynman"),
                        ev(1, True, "feynman"), ev(0, True, "feynman")]
        assert mastery_level(feynman_only, NOW) == "熟练"
        # 换成实战来源之一 → 精通
        with_practical = [ev(4, True, "feynman"), ev(3, True, "feynman"),
                          ev(1, True, "arena"), ev(0, True, "feynman")]
        assert mastery_level(with_practical, NOW) == "精通"

    def test_master_requires_spaced_pair(self):
        # 4 次答对但都挤在 1 天内（无 ≥3 天间隔对）→ 熟练
        cramped = [ev(0.75, True), ev(0.5, True), ev(0.25, True), ev(0, True)]
        assert mastery_level(cramped, NOW) == "熟练"

    def test_master_requires_min_correct_count(self):
        # 3 次答对间隔足够、含实战，但不到 4 次 → 熟练
        events = [ev(6, True, "arena"), ev(3, True), ev(0, True)]
        assert mastery_level(events, NOW) == "熟练"

    def test_master_full_path(self):
        events = [ev(6, True, "feynman"), ev(3, True, "certification"),
                  ev(1, True, "feynman"), ev(0, True, "feynman")]
        assert mastery_level(events, NOW) == "精通"


# ── 趋势 ─────────────────────────────────────────────────


class TestTrend:
    def test_no_events_is_flat(self):
        assert compute_trend([], NOW) == "flat"

    def test_recent_progress_is_up(self):
        # 7 天前窗口内没有事件，现在有答对 → up
        assert compute_trend([ev(1, True)], NOW) == "up"

    def test_forgetting_is_down(self):
        # 8 天前答对过，之后没有新事件 → p 持续衰减 → down
        assert compute_trend([ev(8, True)], NOW) == "down"

    def test_recent_correct_stays_up(self):
        # 窗口内从无到有 → up
        assert compute_trend([ev(0.5, True)], NOW) == "up"

    def test_steady_review_is_flat(self):
        # h 已封顶 180 天：窗口前后各有一次答对，p 变化 < 0.02 → flat
        events = [ev(30 - i, True) for i in range(20)]  # 30..11 天前，h 封顶
        events += [ev(6, True), ev(1, True)]
        assert compute_trend(events, NOW) == "flat"


# ── 费曼评分 ─────────────────────────────────────────────

KEY_POINTS = [
    {"keys": ["越界", "arr[n]"], "label": "越界访问"},
    {"keys": ["<= n", "i < n", "边界"], "label": "循环边界"},
    {"keys": ["下标", "索引"], "label": "下标从 0 开始"},
    {"keys": ["段错误", "未定义"], "label": "后果"},
]


class TestFeynmanGrade:
    def test_full_coverage_with_structure_is_excellent(self):
        text = ("因为下标从 0 开始，所以 i < n 才对；如果写成 <= n 就会越界访问 arr[n]。"
                "比如循环到最后一次会读到数组外，后果是未定义行为。")
        result = feynman_grade(text, KEY_POINTS)
        assert result["grade"] == "优秀"
        assert result["missed"] == []
        assert len(result["covered"]) == 4

    def test_half_coverage_is_good(self):
        text = "循环会越界访问 arr[n]，因为边界写错了。"
        result = feynman_grade(text, KEY_POINTS)
        assert result["grade"] == "良好"
        assert "越界访问" in result["covered"]
        assert "下标从 0 开始" in result["missed"]

    def test_mid_coverage_with_structure_is_good(self):
        # 2/5=0.4 覆盖率：不达 0.5，但 ≥0.34 且有结构 → 良好
        five_points = KEY_POINTS + [{"keys": ["内存"], "label": "内存布局"}]
        text = "因为会越界访问，所以循环边界要写 i < n。比如最后一次会读到数组外。"
        result = feynman_grade(text, five_points)
        assert result["grade"] == "良好"

    def test_mid_coverage_without_structure_is_weak(self):
        # 同样 2/5 覆盖率但无因果/举例 → 待加强
        five_points = KEY_POINTS + [{"keys": ["内存"], "label": "内存布局"}]
        text = "越界访问 arr[n]，循环边界 i < n。"
        result = feynman_grade(text, five_points)
        assert result["grade"] == "待加强"

    def test_low_coverage_without_structure_is_weak(self):
        text = "这个知识点很重要，要多练习。"
        result = feynman_grade(text, KEY_POINTS)
        assert result["grade"] == "待加强"
        assert result["covered"] == []

    def test_full_coverage_without_structure_is_only_good(self):
        text = "越界访问 arr[n]，循环边界 i < n，下标从 0 开始，后果是未定义行为。"
        result = feynman_grade(text, KEY_POINTS)
        assert result["grade"] == "良好"

    def test_synonym_matching(self):
        text = "因为索引从 0 开始，所以最大能取到 n-1，比如 5 个元素最后是 4。"
        result = feynman_grade(text, KEY_POINTS)
        assert "下标从 0 开始" in result["covered"]  # 命中同义词「索引」

    def test_no_key_points_falls_back_to_structure(self):
        assert feynman_grade("因为所以，比如例如。", None)["grade"] == "良好"
        assert feynman_grade("随便讲讲。", None)["grade"] == "待加强"

    def test_empty_key_points_list(self):
        assert feynman_grade("因为所以，比如例如。", [])["grade"] == "良好"
