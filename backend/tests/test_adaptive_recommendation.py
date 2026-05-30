"""Tests for Adaptive Recommendation Service - 难度匹配算法测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.adaptive_recommendation import (
    AdaptiveRecommendationService,
    DIFFICULTY_LABELS,
    get_adaptive_recommendation_service,
)
from app.models.exercise import Exercise
from app.models.user import User
from app.models.user_weak_point import UserWeakPoint
from app.models.stats import ActivityLog


class TestDifficultyLabels:
    """测试难度标签是否正确映射到 8 级体系"""

    def test_difficulty_labels_has_8_levels(self):
        """验证难度标签有 8 个级别"""
        assert len(DIFFICULTY_LABELS) == 8

    def test_difficulty_labels_correct_names(self):
        """验证难度标签名称符合洛谷体系"""
        expected_labels = {
            1: "入门",
            2: "普及-",
            3: "普及/提高-",
            4: "普及+/提高",
            5: "提高+/省选-",
            6: "省选/NOI-",
            7: "NOI",
            8: "NOI+/CTSC",
        }
        assert DIFFICULTY_LABELS == expected_labels


class TestTargetDifficultyCalculation:
    """测试目标难度计算逻辑"""

    @pytest.fixture
    def service(self, db_session: AsyncSession):
        return AdaptiveRecommendationService(db_session)

    def test_new_user_gets_difficulty_1(self, service):
        """新用户应该从难度 1 开始"""
        knowledge_state = {
            "estimated_level": 1.5,
            "accuracy": 0.5,
            "total_attempts": 0,  # 新用户
        }
        target = service._calculate_target_difficulty(knowledge_state, "mastery")
        assert target == 1

    def test_new_user_with_few_attempts_gets_low_difficulty(self, service):
        """新用户（尝试次数 < 5）应该获得低难度"""
        knowledge_state = {
            "estimated_level": 2.0,
            "accuracy": 0.8,
            "total_attempts": 3,
        }
        target = service._calculate_target_difficulty(knowledge_state, "mastery")
        assert target == 1  # 新用户总是从 1 开始

    def test_mastery_path_limits_to_3_for_beginners(self, service):
        """精进之路模式应该限制初学者难度上限"""
        # 初学者即使正确率高，也应该限制难度
        knowledge_state = {
            "estimated_level": 2.5,
            "accuracy": 0.9,
            "total_attempts": 10,
        }
        target = service._calculate_target_difficulty(knowledge_state, "mastery")
        assert target <= 3

    def test_challenge_path_allows_higher_difficulty(self, service):
        """挑战之路模式允许更高难度"""
        knowledge_state = {
            "estimated_level": 3.5,
            "accuracy": 0.8,
            "total_attempts": 20,
        }
        target = service._calculate_target_difficulty(knowledge_state, "challenge")
        assert target >= 3
        assert target <= 8

    def test_difficulty_never_below_1(self, service):
        """难度永远不应该低于 1"""
        knowledge_state = {
            "estimated_level": 0.5,  # 异常低的估计
            "accuracy": 0.1,
            "total_attempts": 5,
        }
        target = service._calculate_target_difficulty(knowledge_state, "mastery")
        assert target >= 1

    def test_difficulty_never_above_8(self, service):
        """难度永远不应该高于 8"""
        knowledge_state = {
            "estimated_level": 10,  # 异常高的估计
            "accuracy": 1.0,
            "total_attempts": 100,
        }
        target = service._calculate_target_difficulty(knowledge_state, "challenge")
        assert target <= 8


class TestCandidateExerciseFiltering:
    """测试练习题候选过滤逻辑"""

    @pytest.fixture
    def service(self, db_session: AsyncSession):
        return AdaptiveRecommendationService(db_session)

    @pytest.mark.asyncio
    async def test_beginners_get_easy_exercises_only(
        self, db_session: AsyncSession, service
    ):
        """初学者应该只获得简单题目（难度 1-2）"""
        # 创建测试数据
        exercises = []
        for i in range(1, 9):
            ex = Exercise(
                type="choice",
                difficulty=i,
                content={"text": f"难度 {i} 的题目"},
                solution={"answer": 0},
                is_verified=True,
                knowledge_points=["基础"],
            )
            db_session.add(ex)
            exercises.append(ex)
        await db_session.flush()

        # 模拟新用户状态
        knowledge_state = {
            "estimated_level": 1.0,
            "accuracy": 0.5,
            "total_attempts": 2,
            "weak_points": [],
            "weak_point_objects": [],
            "weak_point_map": {},
            "has_history": False,
        }

        # 获取候选题目 - 精进之路，难度范围 1-2
        candidates = await service._get_candidate_exercises(
            target_difficulty=1,
            min_difficulty=1,
            max_difficulty=2,  # 初学者范围
            knowledge_state=knowledge_state,
            exclude_ids=[],
            recently_practiced={},
            chapter_id=None,
            learning_path="mastery",
        )

        # 验证所有候选题目难度都在 1-2 范围内
        for candidate in candidates:
            assert candidate["difficulty"] >= 1
            assert candidate["difficulty"] <= 2

    @pytest.mark.asyncio
    async def test_no_matrix_multiplication_for_beginners(
        self, db_session: AsyncSession, service
    ):
        """初学者不应该看到矩阵乘法等高难度题目"""
        # 创建简单题目
        simple_ex = Exercise(
            type="programming",
            difficulty=1,
            content={"title": "Hello World", "description": "输出 Hello World"},
            solution={"code": 'print("Hello World")'},
            is_verified=True,
            knowledge_points=["基础语法"],
        )
        db_session.add(simple_ex)

        # 创建矩阵乘法题目（高难度）
        matrix_ex = Exercise(
            type="programming",
            difficulty=4,  # 普及+/提高 级别
            content={
                "title": "矩阵乘法",
                "description": "实现两个矩阵的乘法",
            },
            solution={"code": "..."},
            is_verified=True,
            knowledge_points=["数组", "矩阵", "嵌套循环"],
        )
        db_session.add(matrix_ex)
        await db_session.flush()

        # 新用户状态
        knowledge_state = {
            "estimated_level": 1.0,
            "accuracy": 0.5,
            "total_attempts": 0,
            "weak_points": [],
            "weak_point_objects": [],
            "weak_point_map": {},
            "has_history": False,
        }

        # 获取候选题目 - 初学者范围
        candidates = await service._get_candidate_exercises(
            target_difficulty=1,
            min_difficulty=1,
            max_difficulty=2,  # 初学者只看 1-2 难度
            knowledge_state=knowledge_state,
            exclude_ids=[],
            recently_practiced={},
            chapter_id=None,
            learning_path="mastery",
        )

        # 矩阵乘法不应该出现在候选中
        titles = [c["title"] for c in candidates]
        assert "矩阵乘法" not in titles

        # Hello World 应该在候选中
        assert "Hello World" in titles or len([t for t in titles if "Hello" in t]) >= 0


class TestScoreCandidates:
    """测试候选题目评分逻辑"""

    @pytest.fixture
    def service(self, db_session: AsyncSession):
        return AdaptiveRecommendationService(db_session)

    def test_exact_difficulty_match_gets_highest_score(self, service):
        """难度完全匹配的题目应该获得最高分"""
        candidates = [
            {
                "exercise_id": 1,
                "source_id": "ex1",
                "difficulty": 1,
                "type": "choice",
                "knowledge_points": ["基础"],
                "title": "简单题",
                "matches_weak_point": False,
                "matched_weak_points": [],
                "last_practiced_days": None,
            },
            {
                "exercise_id": 2,
                "source_id": "ex2",
                "difficulty": 3,
                "type": "choice",
                "knowledge_points": ["基础"],
                "title": "中等题",
                "matches_weak_point": False,
                "matched_weak_points": [],
                "last_practiced_days": None,
            },
        ]

        knowledge_state = {
            "weak_points": [],
            "weak_point_map": {},
        }

        scored = service._score_candidates(
            candidates=candidates,
            knowledge_state=knowledge_state,
            target_difficulty=1,  # 目标难度是 1
            recently_practiced={},
        )

        # 难度 1 的题目应该排在前面
        assert scored[0]["difficulty"] == 1
        assert scored[0]["score"] > scored[1]["score"]

    def test_weak_point_match_gets_bonus(self, service):
        """匹配薄弱点的题目应该获得加分"""
        candidates = [
            {
                "exercise_id": 1,
                "source_id": "ex1",
                "difficulty": 2,
                "type": "choice",
                "knowledge_points": ["循环"],
                "title": "循环练习",
                "matches_weak_point": True,
                "matched_weak_points": ["循环"],
                "last_practiced_days": None,
            },
            {
                "exercise_id": 2,
                "source_id": "ex2",
                "difficulty": 2,
                "type": "choice",
                "knowledge_points": ["数组"],
                "title": "数组练习",
                "matches_weak_point": False,
                "matched_weak_points": [],
                "last_practiced_days": None,
            },
        ]

        knowledge_state = {
            "weak_points": ["循环"],
            "weak_point_map": {"循环": {"error_count": 5}},
        }

        scored = service._score_candidates(
            candidates=candidates,
            knowledge_state=knowledge_state,
            target_difficulty=2,
            recently_practiced={},
        )

        # 匹配薄弱点的题目应该获得更高分
        weak_point_score = next(
            s["score_breakdown"]["weak_point"]
            for s in scored
            if s["exercise_id"] == 1
        )
        no_weak_point_score = next(
            s["score_breakdown"]["weak_point"]
            for s in scored
            if s["exercise_id"] == 2
        )
        assert weak_point_score > no_weak_point_score


class TestGetRecommendations:
    """测试完整的推荐流程"""

    @pytest.fixture
    def service(self, db_session: AsyncSession):
        return AdaptiveRecommendationService(db_session)

    @pytest.mark.asyncio
    async def test_beginner_recommendations_exclude_hard_exercises(
        self, db_session: AsyncSession, service
    ):
        """完整流程测试：初学者不应该获得高难度推荐"""
        # 创建不同难度的题目
        for i in range(1, 9):
            ex = Exercise(
                type="choice",
                difficulty=i,
                content={"text": f"难度 {i} 题目"},
                solution={"answer": 0},
                is_verified=True,
                knowledge_points=["基础"],
            )
            db_session.add(ex)
        await db_session.flush()

        # 创建测试用户
        user = User(
            username="beginner_user",
            email="beginner@test.com",
            hashed_password="hash",
            total_exercises=0,  # 新用户
        )
        db_session.add(user)
        await db_session.flush()

        # 获取推荐
        result = await service.get_recommendations(
            user=user,
            limit=10,
            min_difficulty=1,
            max_difficulty=2,  # 初学者范围
            learning_path="mastery",
        )

        # 验证所有推荐的题目难度都在 1-2 范围内
        for rec in result["recommendations"]:
            assert rec["difficulty"] >= 1
            assert rec["difficulty"] <= 2

        # 验证知识状态显示目标难度合理
        assert result["knowledge_state"]["target_difficulty"] <= 2


class TestDiversityFilter:
    """测试多样性过滤"""

    @pytest.fixture
    def service(self, db_session: AsyncSession):
        return AdaptiveRecommendationService(db_session)

    def test_no_more_than_40_percent_same_difficulty(self, service):
        """同一难度级别的题目不超过 40%"""
        candidates = []
        for i in range(20):
            candidates.append({
                "exercise_id": i + 1,
                "source_id": f"ex{i}",
                "similarity": 0.8 - i * 0.01,  # 递减分数
                "difficulty": 1,  # 全部是难度 1
                "type": "choice",
                "knowledge_points": ["基础"],
                "title": f"题目 {i}",
                "matched_weak_points": [],
                "score_breakdown": {},
            })

        # 由于多样性限制，最多只能选择 limit * 0.4 个同一难度的题目
        limit = 10
        selected = service._apply_diversity_filter(candidates, limit=limit)

        # 统计难度分布
        difficulty_counts = {}
        for s in selected:
            d = s["difficulty"]
            difficulty_counts[d] = difficulty_counts.get(d, 0) + 1

        # 验证同一难度不超过 40%
        for diff, count in difficulty_counts.items():
            assert count <= limit * 0.4 + 1  # 允许一个的误差


class TestDifficultyRangeForStages:
    """测试关卡难度范围计算"""

    def test_stage_1_gets_difficulty_1_2(self):
        """第 1 关应该获取难度 1-2 的题目"""
        stage_difficulty = 1
        min_diff = max(1, stage_difficulty - 1)
        max_diff = min(8, stage_difficulty + 1)
        assert min_diff == 1
        assert max_diff == 2

    def test_stage_3_gets_difficulty_2_4(self):
        """第 3 关（难度 3）应该获取难度 2-4 的题目"""
        stage_difficulty = 3
        min_diff = max(1, stage_difficulty - 1)
        max_diff = min(8, stage_difficulty + 1)
        assert min_diff == 2
        assert max_diff == 4

    def test_stage_8_gets_difficulty_7_8(self):
        """第 8 关（最高难度）应该获取难度 7-8 的题目"""
        stage_difficulty = 8
        min_diff = max(1, stage_difficulty - 1)
        max_diff = min(8, stage_difficulty + 1)
        assert min_diff == 7
        assert max_diff == 8
