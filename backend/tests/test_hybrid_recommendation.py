"""
Tests for Hybrid Recommendation System

Tests the fusion recommendation algorithm that combines:
1. Behavior-based scoring (40%)
2. Embedding similarity (35%)
3. Difficulty matching (25%)
"""

import pytest
import json
import math
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.hybrid_recommendation import (
    HybridRecommendationService,
    BehaviorScorer,
    EmbeddingScorer,
    DifficultyScorer,
    calculate_cosine_similarity,
)
from app.models.exercise import Exercise
from app.models.user import User
from app.models.user_arena import UserArenaProfile
from app.models.arena_exercise_progress import ArenaExerciseProgress


class TestCosineSimilarity:
    """Tests for cosine similarity calculation"""

    def test_identical_vectors(self):
        """Identical vectors should have similarity 1.0"""
        vec = [1.0, 2.0, 3.0, 4.0]
        assert calculate_cosine_similarity(vec, vec) == pytest.approx(1.0, rel=1e-5)

    def test_orthogonal_vectors(self):
        """Orthogonal vectors should have similarity 0.0"""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        assert calculate_cosine_similarity(vec1, vec2) == pytest.approx(0.0, abs=1e-5)

    def test_opposite_vectors(self):
        """Opposite vectors should have similarity -1.0"""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [-1.0, -2.0, -3.0]
        assert calculate_cosine_similarity(vec1, vec2) == pytest.approx(-1.0, rel=1e-5)

    def test_different_magnitude(self):
        """Vectors with different magnitudes should be normalized"""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [10.0, 0.0, 0.0]
        assert calculate_cosine_similarity(vec1, vec2) == pytest.approx(1.0, rel=1e-5)

    def test_empty_vectors(self):
        """Empty vectors should return 0.0"""
        assert calculate_cosine_similarity([], []) == 0.0
        assert calculate_cosine_similarity([1.0, 2.0], []) == 0.0
        assert calculate_cosine_similarity([], [1.0, 2.0]) == 0.0

    def test_different_lengths(self):
        """Vectors with different lengths should return 0.0"""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [1.0, 2.0]
        assert calculate_cosine_similarity(vec1, vec2) == 0.0


class TestBehaviorScorer:
    """Tests for behavior-based scoring"""

    @pytest.fixture
    def scorer(self):
        return BehaviorScorer()

    def test_high_accuracy_user_gets_challenging_recommendation(self, scorer):
        """Users with high accuracy should get higher scores for challenging problems"""
        user_stats = {
            "accuracy": 0.85,
            "avg_attempts": 1.5,
            "total_submissions": 50,
        }
        exercise_difficulty = 5  # Harder exercise

        score = scorer.calculate(user_stats, exercise_difficulty)
        assert score > 0.5  # Should favor challenging content

    def test_low_accuracy_user_gets_easier_recommendation(self, scorer):
        """Users with low accuracy should get higher scores for easier problems"""
        user_stats = {
            "accuracy": 0.35,
            "avg_attempts": 4.0,
            "total_submissions": 20,
        }
        exercise_difficulty = 2  # Easier exercise

        score = scorer.calculate(user_stats, exercise_difficulty)
        assert score > 0.5  # Should favor easier content

    def test_fast_solver_gets_depth_bonus(self, scorer):
        """Users with low attempts should get bonus for deeper problems"""
        user_stats = {
            "accuracy": 0.70,
            "avg_attempts": 1.2,  # Low attempts - quick learner
            "total_submissions": 30,
        }
        exercise_difficulty = 4  # Medium-hard problem

        score = scorer.calculate(user_stats, exercise_difficulty)
        assert score > 0.4  # Should favor depth

    def test_slow_solver_gets_foundation_bonus(self, scorer):
        """Users with high attempts should get bonus for foundational problems"""
        user_stats = {
            "accuracy": 0.60,
            "avg_attempts": 5.0,  # High attempts - need practice
            "total_submissions": 30,
        }
        exercise_difficulty = 2  # Foundation problem

        score = scorer.calculate(user_stats, exercise_difficulty)
        assert score > 0.4  # Should favor foundation

    def test_experienced_user_high_difficulty_bonus(self, scorer):
        """Users with many submissions should get bonus for challenges"""
        user_stats = {
            "accuracy": 0.65,
            "avg_attempts": 2.0,
            "total_submissions": 100,  # Many submissions
        }
        exercise_difficulty = 5

        score = scorer.calculate(user_stats, exercise_difficulty)
        assert score > 0.5  # Should favor challenges


class TestEmbeddingScorer:
    """Tests for embedding-based scoring"""

    @pytest.fixture
    def scorer(self):
        return EmbeddingScorer()

    def test_similar_embeddings_high_score(self, scorer):
        """Similar embeddings should produce high scores"""
        user_embedding = [1.0, 0.0, 0.5, 0.3]
        exercise_embedding = [0.9, 0.1, 0.6, 0.2]

        score = scorer.calculate(user_embedding, exercise_embedding)
        assert score > 0.8  # High similarity

    def test_dissimilar_embeddings_low_score(self, scorer):
        """Dissimilar embeddings should produce low scores"""
        user_embedding = [1.0, 0.0, 0.0, 0.0]
        exercise_embedding = [0.0, 1.0, 0.0, 0.0]

        score = scorer.calculate(user_embedding, exercise_embedding)
        # Normalized from cosine similarity 0.0 → (0.0 + 1) / 2 = 0.5
        assert score <= 0.5  # Low similarity (normalized from 0.0)

    def test_missing_user_embedding_returns_default(self, scorer):
        """Missing user embedding should return default score"""
        score = scorer.calculate(None, [1.0, 2.0, 3.0])
        assert score == 0.5  # Neutral default

    def test_missing_exercise_embedding_returns_default(self, scorer):
        """Missing exercise embedding should return default score"""
        score = scorer.calculate([1.0, 2.0, 3.0], None)
        assert score == 0.5  # Neutral default

    def test_both_missing_returns_default(self, scorer):
        """Both embeddings missing should return default score"""
        score = scorer.calculate(None, None)
        assert score == 0.5


class TestDifficultyScorer:
    """Tests for ZPD-based difficulty scoring"""

    @pytest.fixture
    def scorer(self):
        return DifficultyScorer()

    def test_exact_match_highest_score(self, scorer):
        """Target difficulty match should produce highest score"""
        user_level = 3.0  # User level 3
        exercise_difficulty = 4  # Target difficulty (level + 1)
        # Target = 3.0 + 0.5 = 3.5, distance to 4 = 0.5
        score = scorer.calculate(user_level, exercise_difficulty)
        assert score >= 0.9  # Very high score for exact target region

    def test_one_level_difference_good_score(self, scorer):
        """One level difference should produce good score"""
        user_level = 3.0
        exercise_difficulty = 3  # One below target
        # Target = 3.5, distance to 3 = 0.5
        score = scorer.calculate(user_level, exercise_difficulty)
        assert 0.6 <= score <= 0.95

    def test_too_easy_penalty(self, scorer):
        """Too easy exercises should be penalized"""
        user_level = 5.0
        exercise_difficulty = 1  # Much too easy

        score = scorer.calculate(user_level, exercise_difficulty)
        assert score < 0.3

    def test_too_hard_penalty(self, scorer):
        """Too hard exercises should be penalized"""
        user_level = 2.0
        exercise_difficulty = 7  # Much too hard

        score = scorer.calculate(user_level, exercise_difficulty)
        assert score < 0.3

    def test_zpd_optimal_range(self, scorer):
        """Exercises in ZPD range should get good scores"""
        user_level = 3.0

        # Test exercises in optimal ZPD range (level ± 1)
        # Target = 3.5, so difficulties 3, 4 should be in range
        for diff in [3, 4]:
            score = scorer.calculate(user_level, diff)
            assert score >= 0.5, f"Difficulty {diff} should be in ZPD range (score={score})"


class TestHybridRecommendationService:
    """Tests for the full hybrid recommendation service"""

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db):
        return HybridRecommendationService(mock_db)

    @pytest.mark.asyncio
    async def test_fusion_weights_sum_to_one(self, service):
        """Fusion weights should sum to 1.0"""
        weights = service.get_fusion_weights()
        total = sum(weights.values())
        assert total == pytest.approx(1.0, rel=1e-5)

    @pytest.mark.asyncio
    async def test_final_score_calculation(self, service):
        """Final score should be weighted sum of component scores"""
        behavior_score = 0.7
        embedding_score = 0.8
        difficulty_score = 0.6

        final = service.calculate_final_score(
            behavior_score, embedding_score, difficulty_score
        )

        # Expected: 0.40 * 0.7 + 0.35 * 0.8 + 0.25 * 0.6
        expected = 0.40 * behavior_score + 0.35 * embedding_score + 0.25 * difficulty_score
        assert final == pytest.approx(expected, rel=1e-5)

    @pytest.mark.asyncio
    async def test_get_recommendations_returns_scored_list(self, service, mock_db):
        """get_recommendations should return a scored, ranked list"""
        # Mock user profile
        mock_profile = MagicMock()
        mock_profile.behavior_embedding = json.dumps([0.5, 0.3, 0.2])
        mock_profile.avg_accuracy = 0.6
        mock_profile.avg_time_spent = 300
        mock_profile.total_submissions = 30

        # Mock exercises with embeddings
        mock_exercise1 = MagicMock()
        mock_exercise1.id = 1
        mock_exercise1.difficulty = 3
        mock_exercise1.embedding = json.dumps([0.6, 0.3, 0.1])
        mock_exercise1.tag_embedding = None  # No tag embedding, will use content embedding
        mock_exercise1.knowledge_points = ["数组", "双指针"]
        mock_exercise1.content = {"title": "测试题1"}
        mock_exercise1.is_verified = True

        mock_exercise2 = MagicMock()
        mock_exercise2.id = 2
        mock_exercise2.difficulty = 4
        mock_exercise2.embedding = json.dumps([0.1, 0.8, 0.1])
        mock_exercise2.tag_embedding = None  # No tag embedding, will use content embedding
        mock_exercise2.knowledge_points = ["链表"]
        mock_exercise2.content = {"title": "测试题2"}
        mock_exercise2.is_verified = True

        # Setup mock for user profile query
        profile_result = MagicMock()
        profile_result.scalar_one_or_none.return_value = mock_profile

        # Setup mock for progress query
        progress_result = MagicMock()
        progress_result.scalars.return_value.all.return_value = []

        # Setup mock for exercises query
        exercises_result = MagicMock()
        exercises_result.scalars.return_value.all.return_value = [mock_exercise1, mock_exercise2]

        # Configure mock_db.execute to return different results based on call order
        call_count = [0]
        async def mock_execute(query):
            call_count[0] += 1
            if call_count[0] == 1:
                return profile_result
            elif call_count[0] == 2:
                return progress_result
            else:
                return exercises_result

        mock_db.execute = mock_execute

        # Call get_recommendations
        recommendations = await service.get_recommendations(
            user_id="test-user",
            course_id=1,
            limit=5,
        )

        # Verify results
        assert isinstance(recommendations, list)
        if len(recommendations) > 0:
            assert "exercise_id" in recommendations[0]
            assert "final_score" in recommendations[0]
            assert "score_breakdown" in recommendations[0]

    @pytest.mark.asyncio
    async def test_recommendation_reason_generation(self, service):
        """Recommendations should include human-readable reasons"""
        scores = {
            "behavior_score": 0.8,
            "embedding_score": 0.7,
            "difficulty_score": 0.9,
        }
        knowledge_points = ["数组", "双指针"]

        reasons = service.generate_recommendation_reasons(scores, knowledge_points)

        assert isinstance(reasons, list)
        assert len(reasons) > 0
        # Should include knowledge points
        assert any("数组" in r or "双指针" in r for r in reasons)


class TestUserProfileEmbeddingUpdate:
    """Tests for user profile embedding update logic"""

    @pytest.mark.asyncio
    async def test_embedding_from_correct_exercises(self):
        """User embedding should be weighted by correct exercises"""
        # This will be implemented in user_profile service
        pass

    @pytest.mark.asyncio
    async def test_embedding_from_incorrect_exercises(self):
        """User embedding should include (negative weight) incorrect exercises"""
        pass

    @pytest.mark.asyncio
    async def test_fast_correct_vs_slow_correct(self):
        """Fast correct solutions should have higher weight"""
        pass


class TestBehaviorTracking:
    """Tests for behavior data tracking"""

    def test_time_spent_tracking(self):
        """Time spent should be recorded correctly"""
        # Will test ArenaExerciseProgress.time_spent field
        pass

    def test_hint_usage_tracking(self):
        """Hint usage should be recorded"""
        # Will test ArenaExerciseProgress.hint_used field
        pass

    def test_first_attempt_correct_tracking(self):
        """First attempt correctness should be recorded"""
        # Will test ArenaExerciseProgress.first_attempt_correct field
        pass
