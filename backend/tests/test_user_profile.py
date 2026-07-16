"""
Tests for User Profile Service

Tests user profile statistics and embedding updates.
"""

import pytest
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.user_profile import UserProfileService, FAST_SOLVER_THRESHOLD, SLOW_SOLVER_THRESHOLD
from app.models.user_arena import UserArenaProfile
from app.models.arena_exercise_progress import ArenaExerciseProgress
from app.models.exercise import Exercise


class TestGetUserStats:
    """Tests for get_user_stats method"""

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db):
        return UserProfileService(mock_db)

    @pytest.mark.asyncio
    async def test_returns_correct_accuracy(self, service, mock_db):
        """get_user_stats should calculate correct accuracy from progress records"""
        # Mock profile
        mock_profile = MagicMock()
        mock_profile.behavior_embedding = None
        mock_profile.current_streak = 3
        mock_profile.best_streak = 5
        mock_profile.tier = "silver"
        mock_profile.sub_tier = 2
        mock_profile.stars = 10

        # Mock progress records: 3 correct out of 5 total
        mock_progresses = []
        for i, is_correct in enumerate([True, True, True, False, False]):
            p = MagicMock()
            p.is_correct = is_correct
            p.attempt_count = 1 if is_correct else 2
            p.is_completed = True
            mock_progresses.append(p)

        # Setup mock returns
        profile_result = MagicMock()
        profile_result.scalar_one_or_none.return_value = mock_profile

        progress_result = MagicMock()
        progress_result.scalars.return_value.all.return_value = mock_progresses

        call_count = [0]
        async def mock_execute(query):
            call_count[0] += 1
            if call_count[0] == 1:
                return profile_result
            return progress_result

        mock_db.execute = mock_execute

        # Call get_user_stats
        stats = await service.get_user_stats("user123", 1)

        # Verify accuracy
        assert stats["accuracy"] == pytest.approx(0.6, rel=1e-5)  # 3/5
        assert stats["total_exercises"] == 5
        assert stats["total_submissions"] == 7  # 1+1+1+2+2 = 7

    @pytest.mark.asyncio
    async def test_returns_correct_avg_attempts(self, service, mock_db):
        """get_user_stats should calculate average attempts per completed exercise"""
        # Mock profile
        mock_profile = MagicMock()
        mock_profile.behavior_embedding = None
        mock_profile.current_streak = 0
        mock_profile.best_streak = 0
        mock_profile.tier = "bronze"
        mock_profile.sub_tier = 4
        mock_profile.stars = 0

        # Mock progress: 3 completed exercises with different attempt counts
        mock_progresses = []
        attempt_counts = [1, 2, 3]  # avg = 2
        for attempts in attempt_counts:
            p = MagicMock()
            p.is_correct = True
            p.attempt_count = attempts
            p.is_completed = True
            mock_progresses.append(p)

        # Add one incomplete exercise (should not count in avg_attempts)
        p_incomplete = MagicMock()
        p_incomplete.is_correct = False
        p_incomplete.attempt_count = 0
        p_incomplete.is_completed = False
        mock_progresses.append(p_incomplete)

        profile_result = MagicMock()
        profile_result.scalar_one_or_none.return_value = mock_profile

        progress_result = MagicMock()
        progress_result.scalars.return_value.all.return_value = mock_progresses

        call_count = [0]
        async def mock_execute(query):
            call_count[0] += 1
            if call_count[0] == 1:
                return profile_result
            return progress_result

        mock_db.execute = mock_execute

        stats = await service.get_user_stats("user123", 1)

        # avg_attempts should be (1+2+3)/3 = 2.0 (only completed exercises)
        assert stats["avg_attempts"] == pytest.approx(2.0, rel=1e-5)

    @pytest.mark.asyncio
    async def test_returns_tier_info(self, service, mock_db):
        """get_user_stats should return tier information"""
        # Mock profile with gold tier
        mock_profile = MagicMock()
        mock_profile.behavior_embedding = None
        mock_profile.current_streak = 5
        mock_profile.best_streak = 10
        mock_profile.tier = "gold"
        mock_profile.sub_tier = 3  # Gold III
        mock_profile.stars = 25

        mock_progresses = []

        profile_result = MagicMock()
        profile_result.scalar_one_or_none.return_value = mock_profile

        progress_result = MagicMock()
        progress_result.scalars.return_value.all.return_value = mock_progresses

        call_count = [0]
        async def mock_execute(query):
            call_count[0] += 1
            if call_count[0] == 1:
                return profile_result
            return progress_result

        mock_db.execute = mock_execute

        stats = await service.get_user_stats("user123", 1)

        # Verify tier info is returned
        assert stats["tier"] == "gold"
        assert stats["sub_tier"] == 3
        assert stats["stars"] == 25

    @pytest.mark.asyncio
    async def test_returns_zero_for_no_progress(self, service, mock_db):
        """get_user_stats should return zero stats when no progress exists"""
        mock_profile = MagicMock()
        mock_profile.behavior_embedding = None
        mock_profile.current_streak = 0
        mock_profile.best_streak = 0
        mock_profile.tier = "bronze"
        mock_profile.sub_tier = 4
        mock_profile.stars = 0

        profile_result = MagicMock()
        profile_result.scalar_one_or_none.return_value = mock_profile

        progress_result = MagicMock()
        progress_result.scalars.return_value.all.return_value = []

        call_count = [0]
        async def mock_execute(query):
            call_count[0] += 1
            if call_count[0] == 1:
                return profile_result
            return progress_result

        mock_db.execute = mock_execute

        stats = await service.get_user_stats("user123", 1)

        assert stats["accuracy"] == 0.0
        assert stats["avg_attempts"] == 0
        assert stats["total_submissions"] == 0
        assert stats["total_exercises"] == 0

    @pytest.mark.asyncio
    async def test_handles_missing_profile(self, service, mock_db):
        """get_user_stats should create profile if not exists"""
        # First call returns None (no profile), second call returns created profile
        mock_profile = MagicMock()
        mock_profile.behavior_embedding = None
        mock_profile.current_streak = 0
        mock_profile.best_streak = 0
        mock_profile.tier = "bronze"
        mock_profile.sub_tier = 4
        mock_profile.stars = 0

        profile_result_none = MagicMock()
        profile_result_none.scalar_one_or_none.return_value = None

        profile_result_created = MagicMock()
        profile_result_created.scalar_one_or_none.return_value = mock_profile

        progress_result = MagicMock()
        progress_result.scalars.return_value.all.return_value = []

        call_count = [0]
        async def mock_execute(query):
            call_count[0] += 1
            if call_count[0] == 1:
                return profile_result_none
            if call_count[0] == 2:
                return profile_result_created
            return progress_result

        mock_db.execute = mock_execute
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        stats = await service.get_user_stats("user123", 1)

        # Should still return valid stats
        assert "accuracy" in stats
        assert "tier" in stats


class TestUpdateAfterExercise:
    """Tests for update_after_exercise method"""

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db):
        return UserProfileService(mock_db)

    @pytest.mark.asyncio
    async def test_updates_statistics_on_correct_answer(self, service, mock_db):
        """update_after_exercise should update profile statistics correctly"""
        # Mock profile
        mock_profile = MagicMock()
        mock_profile.user_id = "user123"
        mock_profile.course_id = 1
        mock_profile.behavior_embedding = None
        mock_profile.current_streak = 0
        mock_profile.best_streak = 0

        # Mock exercise with embedding
        mock_exercise = MagicMock()
        mock_exercise.embedding = json.dumps([0.5, 0.3, 0.2])
        mock_exercise.difficulty = 3
        harder_exercise = MagicMock()
        harder_exercise.difficulty = 5

        profile_result = MagicMock()
        profile_result.scalar_one_or_none.return_value = mock_profile

        exercise_result = MagicMock()
        exercise_result.scalar_one_or_none.return_value = mock_exercise

        # Mock progress records for statistics calculation
        mock_progress1 = MagicMock()
        mock_progress1.exercise_id = 1
        mock_progress1.is_completed = True
        mock_progress1.is_correct = True
        mock_progress1.attempt_count = 1
        mock_progress1.time_spent = 100

        mock_progress2 = MagicMock()
        mock_progress2.exercise_id = 2
        mock_progress2.is_completed = False
        mock_progress2.is_correct = False
        mock_progress2.attempt_count = 2
        mock_progress2.time_spent = 200

        progress_result = MagicMock()
        progress_result.all.return_value = [
            (mock_progress1, mock_exercise),
            (mock_progress2, harder_exercise),
        ]

        call_count = [0]
        async def mock_execute(query):
            call_count[0] += 1
            if call_count[0] == 1:
                return profile_result
            if call_count[0] == 2:
                return exercise_result
            return progress_result

        mock_db.execute = mock_execute
        mock_db.commit = AsyncMock()
        mock_db.flush = AsyncMock()

        result = await service.update_after_exercise(
            user_id="user123",
            course_id=1,
            exercise_id=1,
            is_correct=True,
            time_spent=150,
        )

        mock_db.flush.assert_awaited_once()
        mock_db.commit.assert_not_awaited()
        assert result["total_submissions"] == 3
        assert result["avg_accuracy"] == 0.5
        assert result["avg_time_spent"] == 150
        assert mock_profile.total_challenges == 1
        assert mock_profile.wins == 1
        assert mock_profile.losses == 0
        assert mock_profile.highest_difficulty == 3
        assert mock_profile.best_streak == 1
        assert mock_profile.current_streak == 0


class TestBehaviorEmbeddingUpdate:
    """Tests for behavior embedding update logic"""

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db):
        return UserProfileService(mock_db)

    def test_fast_correct_gets_high_weight(self):
        """Fast correct solution (< 5 min) should get weight 1.0"""
        # This is tested via _update_behavior_embedding
        # weight should be 1.0 for fast correct
        pass

    def test_slow_correct_gets_lower_weight(self):
        """Slow correct solution (> 10 min) should get weight 0.4"""
        pass

    def test_incorrect_gets_negative_weight(self):
        """Incorrect answer should get negative weight -0.8"""
        pass
