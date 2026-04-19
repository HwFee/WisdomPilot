"""
BKT Model Unit Tests

测试 BKT 核心算法的正确性。
"""

import pytest
from app.services.bkt import BKTModel, BKTParams, BKTCalculator


class TestBKTParams:
    """BKT 参数测试"""

    def test_default_params_valid(self):
        """默认参数应该有效"""
        params = BKTParams()
        assert params.validate() is True

    def test_params_boundary(self):
        """参数边界测试"""
        # 有效边界
        params = BKTParams(p_l0=0.0, p_t=0.0, p_g=0.0, p_s=0.0)
        assert params.validate() is True

        params = BKTParams(p_l0=1.0, p_t=1.0, p_g=1.0, p_s=1.0)
        assert params.validate() is True

        # 无效边界
        params = BKTParams(p_l0=-0.1)
        assert params.validate() is False

        params = BKTParams(p_g=1.1)
        assert params.validate() is False

    def test_params_to_dict(self):
        """参数序列化测试"""
        params = BKTParams(p_l0=0.2, p_t=0.15, p_g=0.25, p_s=0.1)
        data = params.to_dict()

        assert data["p_l0"] == 0.2
        assert data["p_t"] == 0.15
        assert data["p_g"] == 0.25
        assert data["p_s"] == 0.1

    def test_params_from_dict(self):
        """参数反序列化测试"""
        data = {"p_l0": 0.2, "p_t": 0.15, "p_g": 0.25, "p_s": 0.1}
        params = BKTParams.from_dict(data)

        assert params.p_l0 == 0.2
        assert params.p_t == 0.15
        assert params.p_g == 0.25
        assert params.p_s == 0.1


class TestBKTModel:
    """BKT 模型核心测试"""

    def test_correct_answer_increases_mastery(self):
        """答对应该增加掌握概率"""
        model = BKTModel()
        p_l_initial = 0.15

        p_l_new, _ = model.update(p_l_initial, is_correct=True)

        assert p_l_new > p_l_initial, f"P(L) should increase: {p_l_initial} -> {p_l_new}"

    def test_wrong_answer_decreases_posterior(self):
        """答错后的后验概率应该降低"""
        model = BKTModel()
        p_l = 0.5

        # 计算后验（不含学习）
        p_l_correct = model._compute_p_l_correct(p_l)
        p_l_wrong = model._compute_p_l_wrong(p_l)

        # 答对后验 > 原始 > 答错后验
        assert p_l_correct > p_l > p_l_wrong

    def test_mastery_convergence(self):
        """连续答对应该收敛到掌握"""
        model = BKTModel()
        p_l = 0.15

        mastered = False
        for i in range(20):
            p_l, mastered = model.update(p_l, is_correct=True)
            if mastered:
                break

        assert mastered is True, f"Should reach mastery after 20 correct answers, got P(L)={p_l}"
        assert p_l >= 0.95

    def test_wrong_answers_slow_convergence(self):
        """答错会减缓收敛"""
        model = BKTModel()

        # 全对序列
        p_l_correct = 0.15
        for _ in range(10):
            p_l_correct, _ = model.update(p_l_correct, is_correct=True)

        # 混合序列（80%正确率）
        p_l_mixed = 0.15
        pattern = [True, True, False, True, True]  # 80% 正确率
        for i in range(10):
            p_l_mixed, _ = model.update(p_l_mixed, pattern[i % len(pattern)])

        assert p_l_correct > p_l_mixed, "全对应比混合序列收敛更快"

    def test_difficulty_adjustment(self):
        """难度调整应该影响参数"""
        model = BKTModel()

        easy = model.get_difficulty_adjusted_params(1)
        hard = model.get_difficulty_adjusted_params(8)

        assert hard.p_g > easy.p_g, "难题猜测率应该更高"
        assert hard.p_t > easy.p_t, "难题学习率应该更高"

    def test_question_type_params(self):
        """题型参数测试"""
        model = BKTModel()

        choice = model.get_question_type_params("choice")
        programming = model.get_question_type_params("programming")

        assert choice.p_g > programming.p_g, "选择题猜测率应该高于编程题"

    def test_predict_correct_probability(self):
        """测试答对概率预测"""
        model = BKTModel()

        # 未掌握时（P(L) = 0.1）
        p_correct_low = model.predict_correct_probability(0.1)
        # P(correct) = 0.1 * (1 - 0.05) + 0.9 * 0.2 = 0.095 + 0.18 = 0.275
        assert 0.15 < p_correct_low < 0.35

        # 已掌握时（P(L) = 0.95）
        p_correct_high = model.predict_correct_probability(0.95)
        # P(correct) = 0.95 * 0.95 + 0.05 * 0.2 = 0.9025 + 0.01 = 0.9125
        assert p_correct_high > 0.85

    def test_boundary_conditions(self):
        """边界条件测试"""
        model = BKTModel()

        # P(L) = 0 时答对
        p_l, _ = model.update(0.0, is_correct=True)
        assert p_l > 0, "P(L)=0 答对应该增加"

        # P(L) = 1 时答错
        # 注意：BKT 数学上，当 P(L)=1.0 时，答错被解释为"失误"而非"不掌握"
        # 因此 P(L|wrong) = 1.0 * P(S) / (1.0 * P(S) + 0) = 1.0
        # 这是数学正确的边界行为，实践中 P(L) 不会真正达到 1.0
        p_l, _ = model.update(1.0, is_correct=False)
        # 由于学习更新 P(L_new) = 1.0 + (1-1.0) * P(T) = 1.0，保持 1.0
        # 这是预期行为，不应下降
        assert p_l == 1.0, "P(L)=1 答错后由于学习率更新仍为 1.0（数学正确）"

    def test_probability_bounds(self):
        """概率应该在 [0, 1] 范围内"""
        model = BKTModel()

        p_l = 0.5
        for _ in range(100):
            import random
            is_correct = random.random() > 0.3  # 70% 正确率
            p_l, _ = model.update(p_l, is_correct)
            assert 0 <= p_l <= 1, f"P(L) should be in [0, 1], got {p_l}"


class TestBKTCalculator:
    """BKT 计算工具测试"""

    def test_simulate_learning_sequence(self):
        """模拟学习序列"""
        model = BKTModel()

        # 10次答题，80%正确率
        answers = [True, True, False, True, True, True, True, False, True, True]
        results = BKTCalculator.simulate_learning_sequence(model, 0.15, answers)

        assert len(results) == 10

        # 掌握度应该整体上升
        first_p_l = results[0][0]
        last_p_l = results[-1][1]
        assert last_p_l > first_p_l

    def test_estimate_learning_steps(self):
        """估计学习步数"""
        model = BKTModel()

        # 从 0.15 到 0.95，假设全对
        steps = BKTCalculator.estimate_learning_steps(model, 0.15, 0.95, assume_correct=True)

        # 应该在合理范围内（通常 5-15 步）
        assert 3 <= steps <= 20, f"Steps should be reasonable: {steps}"

        # 假设全错，应该无法达到
        steps_wrong = BKTCalculator.estimate_learning_steps(model, 0.15, 0.95, assume_correct=False, max_steps=100)
        assert steps_wrong == 100, "全错应该无法达到掌握"

    def test_compute_mastery_trend(self):
        """计算掌握趋势"""
        model = BKTModel()

        trends = BKTCalculator.compute_mastery_trend(model, 0.15, num_steps=10)

        assert len(trends["all_correct"]) == 11  # 包含初始值
        assert len(trends["all_wrong"]) == 11
        assert len(trends["mixed"]) == 11

        # 全对 > 混合 > 全错
        assert trends["all_correct"][-1] > trends["mixed"][-1] > trends["all_wrong"][-1]

    def test_analyze_question_impact(self):
        """分析题目影响"""
        model = BKTModel()

        impact = BKTCalculator.analyze_question_impact(model, 0.5)

        assert impact["p_l_if_correct"] > 0.5
        assert impact["p_l_if_wrong"] < 0.5
        assert impact["delta_correct"] > 0
        assert impact["delta_wrong"] > 0


class TestBKTAntiGaming:
    """BKT 防刷分测试"""

    def test_repeated_correct_same_question(self):
        """
        模拟同一题重复答对的场景

        注意：BKT 模型本身不处理防刷分，
        防刷分逻辑在 BKTMasteryService 中实现。
        这里测试的是 BKT 模型对重复输入的行为。
        """
        model = BKTModel()
        p_l = 0.15

        # 模拟重复答对同一题 10 次
        p_l_values = [p_l]
        for _ in range(10):
            p_l, _ = model.update(p_l, True)
            p_l_values.append(p_l)

        # BKT 会持续增加，这说明了防刷分的必要性
        assert p_l_values[-1] > p_l_values[-2]

        # 但增长会逐渐减缓（边际递减）
        early_gain = p_l_values[5] - p_l_values[4]
        late_gain = p_l_values[10] - p_l_values[9]
        assert early_gain > late_gain, "增长应该边际递减"

    def test_single_wrong_after_many_correct(self):
        """多次正确后一次错误的恢复能力"""
        model = BKTModel()
        p_l = 0.15

        # 连续答对 10 次
        for _ in range(10):
            p_l, _ = model.update(p_l, True)

        p_l_before_wrong = p_l

        # 答错一次
        p_l, _ = model.update(p_l, False)

        # 掌握度应该下降，但不会下降太多（因为已经掌握）
        drop = p_l_before_wrong - p_l
        assert drop > 0, "答错应该导致下降"
        assert drop < 0.3, "但下降幅度应该有限（已经掌握）"
