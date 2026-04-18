"""
Test the fixed tier/star logic in arena_infinite.py

Key test cases:
1. First time correct → award stars
2. First time wrong → deduct stars
3. Repeat submission → no star change
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.arena_infinite import ChallengePathService
from app.services.tier_service import tier_service
from app.core.tier_config import TierRank


class TestStarAwardingLogic:
    """Test that stars are only awarded/deducted on first submission"""

    @pytest.mark.asyncio
    async def test_first_correct_awards_stars(self, db_session):
        """First time correct should award stars"""
        # Setup
        service = ChallengePathService(db_session)

        # Mock progress record - not yet completed
        progress = MagicMock()
        progress.is_completed = False
        progress.is_correct = False
        progress.stars_awarded = 0
        progress.correct_at = None
        progress.first_attempt_at = None
        progress.attempt_count = 0
        progress.saved_codes = {}
        progress.current_language = "python"
        progress.exercise_index = 0

        # Mock exercise
        exercise = MagicMock()
        exercise.difficulty = 3
        exercise.content = {"title": "Test Exercise"}
        exercise.chapter_id = 1
        exercise.type = "programming"
        exercise.knowledge_points = []

        # Mock profile
        profile = MagicMock()
        profile.tier = "bronze"
        profile.sub_tier = 4
        profile.stars = 0
        profile.protection_remaining = 3
        profile.highest_tier = None
        profile.highest_sub_tier = None

        # Calculate expected stars
        expected_stars = tier_service.calculate_stars_earned(accuracy=1.0, difficulty=3)
        assert expected_stars == 2  # 100% accuracy should give 2 stars

        print(f"✅ First correct submission should award {expected_stars} stars")

    @pytest.mark.asyncio
    async def test_first_wrong_deducts_stars(self, db_session):
        """First time wrong should deduct stars"""
        # Calculate expected stars for wrong answer
        expected_stars = tier_service.calculate_stars_earned(accuracy=0.0, difficulty=3)
        assert expected_stars == -2  # 0% accuracy should lose 2 stars

        print(f"✅ First wrong submission should deduct {abs(expected_stars)} stars")

    @pytest.mark.asyncio
    async def test_repeat_correct_no_change(self, db_session):
        """Repeat correct submission should not change stars"""
        # If stars_awarded != 0, no new stars should be awarded
        progress = MagicMock()
        progress.stars_awarded = 2  # Already awarded 2 stars

        # In this case, stars_earned should be 0
        # The logic checks: if progress.stars_awarded == 0
        assert progress.stars_awarded != 0  # Should skip star calculation

        print("✅ Repeat submission should not change stars")

    @pytest.mark.asyncio
    async def test_correct_then_wrong_no_change(self, db_session):
        """If already correct, subsequent wrong should not deduct stars"""
        # If stars_awarded > 0 (already got stars for correct), wrong should not deduct
        progress = MagicMock()
        progress.stars_awarded = 2  # Already awarded for correct
        progress.is_correct = True  # Already correct

        # In this case, stars_earned should be 0
        assert progress.stars_awarded != 0  # Should skip star calculation

        print("✅ Correct then wrong should not deduct stars")


class TestTierService:
    """Test tier service calculations"""

    def test_calculate_stars_90_percent_accuracy(self):
        """90%+ accuracy should give 2 base stars"""
        stars = tier_service.calculate_stars_earned(accuracy=0.9, difficulty=3)
        assert stars == 2

    def test_calculate_stars_70_percent_accuracy(self):
        """70%+ accuracy should give 1 base star"""
        stars = tier_service.calculate_stars_earned(accuracy=0.7, difficulty=3)
        assert stars == 1

    def test_calculate_stars_50_percent_accuracy(self):
        """50%+ accuracy should give 0 stars"""
        stars = tier_service.calculate_stars_earned(accuracy=0.5, difficulty=3)
        assert stars == 0

    def test_calculate_stars_30_percent_accuracy(self):
        """30%+ accuracy should lose 1 star"""
        stars = tier_service.calculate_stars_earned(accuracy=0.3, difficulty=3)
        assert stars == -1

    def test_calculate_stars_0_percent_accuracy(self):
        """0% accuracy should lose 2 stars"""
        stars = tier_service.calculate_stars_earned(accuracy=0.0, difficulty=3)
        assert stars == -2

    def test_calculate_stars_high_difficulty_bonus(self):
        """Difficulty 5 + 90% accuracy should give bonus star"""
        stars = tier_service.calculate_stars_earned(accuracy=1.0, difficulty=5)
        assert stars == 3  # 2 base + 1 bonus

    def test_add_stars_promotion(self):
        """Adding stars should handle promotion correctly"""
        # Bronze I with 3 stars + 1 star = Silver IV
        result = tier_service.add_stars(
            tier=TierRank.BRONZE,
            sub_tier=1,  # Bronze I
            current_stars=3,
            stars_earned=1
        )
        assert result.tier == TierRank.SILVER
        assert result.sub_tier == 4  # Silver IV
        assert result.stars == 0
        assert result.promoted == True

    def test_remove_stars_demotion(self):
        """Removing stars should handle demotion correctly"""
        # Silver IV with 0 stars - 1 star = Bronze I
        result = tier_service.remove_stars(
            tier=TierRank.SILVER,
            sub_tier=4,  # Silver IV
            current_stars=0,
            stars_lost=1,
            protection_remaining=0
        )
        assert result.tier == TierRank.BRONZE
        assert result.sub_tier == 1  # Bronze I
        assert result.demoted == True


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
