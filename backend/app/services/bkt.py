"""
BKT (Bayesian Knowledge Tracing) Core Service

实现标准 BKT 算法，用于追踪学生对知识点的掌握状态。

BKT 是教育数据挖掘中经典的知识追踪模型，广泛应用于：
- Khan Academy
- ASSISTments
- Duolingo

核心思想：
- 用概率表示掌握状态
- 区分"猜测"和"真正掌握"
- 建模学习过程（从未掌握到掌握的转变）

算法参考：
- Corbett, A. T., & Anderson, J. R. (1994). Knowledge tracing: Modeling the acquisition of procedural knowledge.
"""

import logging
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class BKTParams:
    """
    BKT 模型参数

    四个核心参数 + 掌握阈值

    参数含义：
    - p_l0: 初始掌握概率 - 学习前已掌握的概率
    - p_t: 学习率 - 每次练习从未掌握变为掌握的概率
    - p_g: 猜测率 - 未掌握但猜对的概率（如选择题 4 选 1 理论猜测率 0.25）
    - p_s: 失误率 - 已掌握但答错的概率（如粗心、紧张等）
    """

    p_l0: float = 0.15  # 初始掌握概率
    p_t: float = 0.1  # 学习率（从未掌握到掌握）
    p_g: float = 0.2  # 猜测率（未掌握但答对）
    p_s: float = 0.05  # 失误率（已掌握但答错）
    mastery_threshold: float = 0.80  # 掌握阈值 - 全对3题可达，答对概率约81%

    def validate(self) -> bool:
        """验证参数有效性"""
        return all(
            0 <= v <= 1
            for v in [self.p_l0, self.p_t, self.p_g, self.p_s, self.mastery_threshold]
        )

    def to_dict(self) -> dict:
        """转换为字典（用于存储）"""
        return {
            "p_l0": self.p_l0,
            "p_t": self.p_t,
            "p_g": self.p_g,
            "p_s": self.p_s,
            "mastery_threshold": self.mastery_threshold,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BKTParams":
        """从字典创建"""
        return cls(
            p_l0=data.get("p_l0", 0.15),
            p_t=data.get("p_t", 0.1),
            p_g=data.get("p_g", 0.2),
            p_s=data.get("p_s", 0.05),
            mastery_threshold=data.get("mastery_threshold", 0.95),
        )


# 不同题型的默认参数
# 根据实际系统情况：主要是选择题和填空题
DEFAULT_BKT_PARAMS = {
    "choice": BKTParams(p_g=0.25),  # 选择题猜测率较高（4选1理论猜测率）
    "fill_blank": BKTParams(p_g=0.15),  # 填空题猜测率中等
    "fill": BKTParams(p_g=0.15),  # 填空题别名
    "default": BKTParams(),
}


class BKTModel:
    """
    Bayesian Knowledge Tracing 模型

    核心方法：
    - update: 根据答题结果更新掌握概率
    - predict_correct_probability: 预测答对概率

    使用示例：
    ```python
    model = BKTModel()
    p_l = 0.15  # 初始掌握概率

    # 答对一题
    p_l, mastered = model.update(p_l, is_correct=True)

    # 答错一题
    p_l, mastered = model.update(p_l, is_correct=False)

    # 预测下一题答对的概率
    p_correct = model.predict_correct_probability(p_l)
    ```
    """

    def __init__(self, params: Optional[BKTParams] = None):
        self.params = params or BKTParams()

    def update(
        self, p_l: float, is_correct: bool, knowledge_point: str = ""
    ) -> Tuple[float, bool]:
        """
        根据答题结果更新掌握概率

        这是 BKT 的核心算法。

        Args:
            p_l: 当前掌握概率 P(L)
            is_correct: 是否答对
            knowledge_point: 知识点名称（用于日志）

        Returns:
            (新的掌握概率 P(L_new), 是否达到掌握阈值)

        算法步骤：
        1. 计算后验概率 P(L|answer)
        2. 应用学习更新 P(L_new) = P(L|answer) + (1 - P(L|answer)) * P(T)
        """
        p = self.params

        logger.info("[BKT] ┌─────────────────────────────────────────────────────")
        logger.info(f"[BKT] │ 知识点: {knowledge_point}")
        logger.info(f"[BKT] │ 答题结果: {'✓ 正确' if is_correct else '✗ 错误'}")
        logger.info(f"[BKT] │ 答题前 P(L) = {p_l:.4f}")
        logger.info("[BKT] ├─────────────────────────────────────────────────────")
        logger.info("[BKT] │ BKT参数:")
        logger.info(f"[BKT] │   P(L0) 初始掌握概率 = {p.p_l0:.2f}")
        logger.info(f"[BKT] │   P(T) 学习率 = {p.p_t:.2f}")
        logger.info(f"[BKT] │   P(G) 猜测率 = {p.p_g:.2f}")
        logger.info(f"[BKT] │   P(S) 失误率 = {p.p_s:.2f}")

        if is_correct:
            # 答对：计算 P(L|correct)
            p_l_given_answer = self._compute_p_l_correct(p_l, knowledge_point)
        else:
            # 答错：计算 P(L|wrong)
            p_l_given_answer = self._compute_p_l_wrong(p_l, knowledge_point)

        # 学习更新：P(L_new) = P(L|answer) + (1 - P(L|answer)) * P(T)
        p_l_new = p_l_given_answer + (1 - p_l_given_answer) * p.p_t

        # 防止数值问题（浮点误差）
        p_l_new = max(0.0, min(1.0, p_l_new))

        is_mastered = p_l_new >= p.mastery_threshold

        logger.info("[BKT] ├─────────────────────────────────────────────────────")
        logger.info("[BKT] │ 计算结果:")
        logger.info(f"[BKT] │   后验概率 P(L|answer) = {p_l_given_answer:.4f}")
        logger.info(
            f"[BKT] │   学习更新 P(L_new) = {p_l_given_answer:.4f} + (1 - {p_l_given_answer:.4f}) × {p.p_t:.2f}"
        )
        logger.info(f"[BKT] │                   = {p_l_new:.4f}")
        logger.info(
            f"[BKT] │   掌握状态: {'✓ 已掌握 (>=0.95)' if is_mastered else '学习中 (<0.95)'}"
        )
        logger.info("[BKT] └─────────────────────────────────────────────────────")

        return p_l_new, is_mastered

    def _compute_p_l_correct(self, p_l: float, knowledge_point: str = "") -> float:
        """
        计算答对后的后验掌握概率 P(L|correct)

        使用贝叶斯公式：
        P(L|correct) = P(correct|L) * P(L) / P(correct)
                     = P(L) * (1 - P(S)) / [P(L) * (1 - P(S)) + (1 - P(L)) * P(G)]

        含义：
        - 分子：已掌握且答对的概率
        - 分母：答对的总概率（已掌握答对 + 未掌握猜对）
        """
        p = self.params
        numerator = p_l * (1 - p.p_s)
        denominator = p_l * (1 - p.p_s) + (1 - p_l) * p.p_g

        if denominator == 0:
            return p_l  # 防止除零

        result = numerator / denominator

        logger.info("[BKT] │ 答对，计算 P(L|correct):")
        logger.info(
            f"[BKT] │   分子 = P(L) × (1 - P(S)) = {p_l:.4f} × {1 - p.p_s:.2f} = {numerator:.4f}"
        )
        logger.info(
            f"[BKT] │   分母 = {p_l:.4f} × {1 - p.p_s:.2f} + {1 - p_l:.4f} × {p.p_g:.2f} = {denominator:.4f}"
        )
        logger.info(
            f"[BKT] │   P(L|correct) = {numerator:.4f} / {denominator:.4f} = {result:.4f}"
        )

        return result

    def _compute_p_l_wrong(self, p_l: float, knowledge_point: str = "") -> float:
        """
        计算答错后的后验掌握概率 P(L|wrong)

        使用贝叶斯公式：
        P(L|wrong) = P(wrong|L) * P(L) / P(wrong)
                   = P(L) * P(S) / [P(L) * P(S) + (1 - P(L)) * (1 - P(G))]

        含义：
        - 分子：已掌握但答错的概率（失误）
        - 分母：答错的总概率（已掌握失误 + 未掌握答错）
        """
        p = self.params
        numerator = p_l * p.p_s
        denominator = p_l * p.p_s + (1 - p_l) * (1 - p.p_g)

        if denominator == 0:
            return p_l  # 防止除零

        result = numerator / denominator

        logger.info("[BKT] │ 答错，计算 P(L|wrong):")
        logger.info(
            f"[BKT] │   分子 = P(L) × P(S) = {p_l:.4f} × {p.p_s:.2f} = {numerator:.4f}"
        )
        logger.info(
            f"[BKT] │   分母 = {p_l:.4f} × {p.p_s:.2f} + {1 - p_l:.4f} × {1 - p.p_g:.2f} = {denominator:.4f}"
        )
        logger.info(
            f"[BKT] │   P(L|wrong) = {numerator:.4f} / {denominator:.4f} = {result:.4f}"
        )

        return result

    def predict_correct_probability(self, p_l: float) -> float:
        """
        预测答对的概率

        P(correct) = P(L) * (1 - P(S)) + (1 - P(L)) * P(G)

        含义：
        - 如果已掌握，答对概率 = 1 - 失误率
        - 如果未掌握，答对概率 = 猜测率
        """
        p = self.params
        return p_l * (1 - p.p_s) + (1 - p_l) * p.p_g

    def get_difficulty_adjusted_params(self, difficulty: int) -> BKTParams:
        """
        根据题目难度调整 BKT 参数

        难度范围：1-3（根据实际基础题难度）

        调整策略：
        - 难题：更高的猜测率（可能碰运气），更高的学习率（做对学到更多）
        - 简单题：更低的猜测率，更低的学习率

        Args:
            difficulty: 难度等级 1-3

        Returns:
            调整后的参数
        """
        # 难度标准化到 [-0.5, 0.5]（范围 1-3，中点 2）
        diff_factor = (difficulty - 2) / 2.0

        return BKTParams(
            p_l0=self.params.p_l0,
            p_t=min(0.20, max(0.08, self.params.p_t * (1 + diff_factor * 0.3))),
            p_g=min(0.30, max(0.15, self.params.p_g * (1 + diff_factor * 0.4))),
            p_s=self.params.p_s,
            mastery_threshold=self.params.mastery_threshold,
        )

    def get_question_type_params(self, question_type: str) -> BKTParams:
        """
        根据题目类型获取参数

        不同题型的猜测率不同：
        - 选择题：4选1，理论猜测率 0.25
        - 编程题：几乎不能猜
        - 填空题：部分猜测可能
        """
        return DEFAULT_BKT_PARAMS.get(question_type, DEFAULT_BKT_PARAMS["default"])


class BKTCalculator:
    """
    BKT 批量计算工具

    用于模拟、测试和分析 BKT 模型行为。
    """

    @staticmethod
    def simulate_learning_sequence(
        model: BKTModel,
        initial_p_l: float,
        answers: List[bool],
    ) -> List[Tuple[float, float, bool]]:
        """
        模拟学习序列，返回每一步的状态

        Args:
            model: BKT 模型
            initial_p_l: 初始掌握概率
            answers: 答题序列 (True=正确, False=错误)

        Returns:
            List of (p_l_before, p_l_after, is_mastered)
        """
        results = []
        p_l = initial_p_l

        for is_correct in answers:
            p_l_before = p_l
            p_l, is_mastered = model.update(p_l, is_correct)
            results.append((p_l_before, p_l, is_mastered))

        return results

    @staticmethod
    def estimate_learning_steps(
        model: BKTModel,
        initial_p_l: float,
        target_p_l: float = 0.95,
        assume_correct: bool = True,
        max_steps: int = 50,
    ) -> int:
        """
        估计达到目标掌握度所需的步数

        Args:
            model: BKT 模型
            initial_p_l: 初始掌握概率
            target_p_l: 目标掌握概率
            assume_correct: 假设答对还是答错
            max_steps: 最大模拟步数

        Returns:
            所需步数（如果无法达到返回 max_steps）
        """
        p_l = initial_p_l

        for step in range(max_steps):
            if p_l >= target_p_l:
                return step
            p_l, _ = model.update(p_l, assume_correct)

        return max_steps

    @staticmethod
    def compute_mastery_trend(
        model: BKTModel,
        initial_p_l: float,
        num_steps: int = 10,
    ) -> Dict[str, List[float]]:
        """
        计算掌握趋势（答对 vs 答错）

        Args:
            model: BKT 模型
            initial_p_l: 初始掌握概率
            num_steps: 模拟步数

        Returns:
            {"all_correct": [...], "all_wrong": [...], "mixed": [...]}
        """
        # 全对
        p_l = initial_p_l
        all_correct = [p_l]
        for _ in range(num_steps):
            p_l, _ = model.update(p_l, True)
            all_correct.append(p_l)

        # 全错
        p_l = initial_p_l
        all_wrong = [p_l]
        for _ in range(num_steps):
            p_l, _ = model.update(p_l, False)
            all_wrong.append(p_l)

        # 混合 (80% 正确率)
        p_l = initial_p_l
        mixed = [p_l]
        pattern = [True, True, False, True, True]  # 80% 正确率
        for i in range(num_steps):
            p_l, _ = model.update(p_l, pattern[i % len(pattern)])
            mixed.append(p_l)

        return {
            "all_correct": all_correct,
            "all_wrong": all_wrong,
            "mixed": mixed,
        }

    @staticmethod
    def analyze_question_impact(
        model: BKTModel,
        current_p_l: float,
    ) -> Dict[str, float]:
        """
        分析下一题的潜在影响

        Returns:
            {
                "p_l_if_correct": 如果答对的掌握概率,
                "p_l_if_wrong": 如果答错的掌握概率,
                "delta_correct": 答对带来的提升,
                "delta_wrong": 答错带来的下降,
            }
        """
        p_l_correct, _ = model.update(current_p_l, True)
        p_l_wrong, _ = model.update(current_p_l, False)

        return {
            "p_l_if_correct": p_l_correct,
            "p_l_if_wrong": p_l_wrong,
            "delta_correct": p_l_correct - current_p_l,
            "delta_wrong": current_p_l - p_l_wrong,
        }
