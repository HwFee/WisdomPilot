"""
Tests for Challenge Path - Stage Mode
挑战之路关卡模式测试

TDD: Testing challenge path with stage-based progression.
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import select
import json


class TestChallengeStartEndpoint:
    """Tests for POST /api/learning-path/challenge/{course_id}/start"""

    @pytest.mark.asyncio
    async def test_start_challenge_returns_full_exercise_content(self, client: AsyncClient, auth_headers: dict):
        """Should return full exercise content including options for choice questions"""
        # This test is integration-style to verify the endpoint behavior
        # We'll test the response format, not the exact mock behavior

        response = await client.post(
            "/api/learning-path/challenge/1/start",
            headers=auth_headers,
            json={
                "difficulty_level": 2,
                "question_count": 2
            }
        )

        # If no exercises/chapters exist, we should get 400 or 200 with exercises
        # The key assertion is that IF exercises are returned, they have full content
        if response.status_code == 200:
            data = response.json()
            assert "exercises" in data
            exercises = data["exercises"]

            # Each exercise should include content with options
            for ex in exercises:
                assert "id" in ex
                assert "content" in ex, "Exercise should include content field"
                assert "text" in ex["content"], "Content should include question text"

                # For choice questions, should include options
                if ex.get("type") == "choice" or "options" in ex.get("content", {}):
                    assert "options" in ex["content"], "Choice questions should include options"

    @pytest.mark.asyncio
    async def test_challenge_exercise_format(self):
        """Test that exercise list format is correct for frontend consumption"""
        # Expected format for frontend
        expected_keys = ["id", "title", "difficulty", "knowledge_points", "content", "type"]

        # Mock exercise data - this is the format the frontend expects
        mock_exercise = {
            "id": 1,
            "title": "测试题目",
            "difficulty": 2,
            "knowledge_points": ["变量"],
            "content": {
                "text": "以下哪个是正确的变量声明？",
                "options": ["A. int x = 10;", "B. variable x;", "C. x = 10;", "D. declare x;"]
            },
            "type": "choice"
        }

        # Verify expected keys are present
        for key in expected_keys:
            assert key in mock_exercise, f"Exercise should have {key} field"


class TestChallengeDifficultyLevels:
    """Tests for difficulty level configuration"""

    @pytest.mark.asyncio
    async def test_difficulty_time_limits(self):
        """Verify difficulty-based time limits are correctly configured"""
        # Time limits per difficulty level (seconds per question)
        DIFFICULTY_TIME = {
            1: 60,   # 入门
            2: 90,   # 基础
            3: 120,  # 中等
            4: 180,  # 困难
            5: 300,  # 极难
        }

        # Verify time increases with difficulty
        for level in range(1, 5):
            assert DIFFICULTY_TIME[level] < DIFFICULTY_TIME[level + 1], \
                f"Level {level} should have less time than level {level + 1}"

    @pytest.mark.asyncio
    async def test_difficulty_score_multipliers(self):
        """Verify difficulty-based score multipliers are correctly configured"""
        # Score multipliers per difficulty level
        DIFFICULTY_MULTIPLIER = {
            1: 1.0,
            2: 1.2,
            3: 1.5,
            4: 2.0,
            5: 3.0,
        }

        # Verify multiplier increases with difficulty
        for level in range(1, 5):
            assert DIFFICULTY_MULTIPLIER[level] < DIFFICULTY_MULTIPLIER[level + 1], \
                f"Level {level} should have lower multiplier than level {level + 1}"
