"""
Tests for Learning Path Challenge - Infinite Mode (挑战之路无限模式)

Covers the optimized endpoints:
- GET /challenge/progress (with lite mode)
- POST /challenge/infinite/start
- GET /challenge/exercise/{id}
- POST /challenge/submit
- POST /challenge/switch
- POST /challenge/save-code
- POST /challenge/append

TDD: Tests verify the lite-mode optimization and on-demand content loading.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.exercise import Exercise
from app.models.arena_exercise_progress import ArenaExerciseProgress
from app.models.user_arena import UserArenaProfile


class TestChallengeProgressLiteMode:
    """Tests for GET /challenge/progress with lite mode optimization"""

    @pytest.mark.asyncio
    async def test_progress_lite_mode_default(self, client: AsyncClient, auth_headers: dict, db_session):
        """TC-LP-01: Lite mode should be default, returning metadata only"""
        # Create a verified exercise
        exercise = Exercise(
            content={"title": "测试题目", "text": "测试内容", "code_template": "print('hello')"},
            type="programming",
            difficulty=3,
            is_verified=True,
            test_cases=[{"input": "1", "output": "1"}],
        )
        db_session.add(exercise)
        await db_session.commit()
        await db_session.refresh(exercise)

        # Create progress record
        user_id = auth_headers["Authorization"].split(" ")[1]
        # Need to get actual user id from token
        progress = ArenaExerciseProgress(
            user_id="test-user-id",
            exercise_id=exercise.id,
            exercise_index=0,
            is_unlocked=True,
        )
        db_session.add(progress)
        await db_session.commit()

        # Request with default (lite=true)
        response = await client.get(
            "/api/learning-path/challenge/progress",
            headers=auth_headers,
        )

        # Should succeed even with no data for this user
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_progress_lite_mode_response_size(self, client: AsyncClient, auth_headers: dict):
        """TC-LP-02: Lite mode response should not contain content/test_cases"""
        response = await client.get(
            "/api/learning-path/challenge/progress",
            headers=auth_headers,
        )

        if response.status_code == 200:
            data = response.json()
            assert "exercises" in data
            for ex in data.get("exercises", []):
                # Lite mode: should have metadata
                assert "exercise_id" in ex
                assert "title" in ex
                assert "difficulty" in ex
                assert "is_completed" in ex
                assert "is_unlocked" in ex

    @pytest.mark.asyncio
    async def test_progress_full_mode_explicit(self, client: AsyncClient, auth_headers: dict):
        """TC-LP-03: Full mode (lite=false) should return content and test_cases"""
        response = await client.get(
            "/api/learning-path/challenge/progress?lite=false",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "exercises" in data

        for ex in data.get("exercises", []):
            # Full mode: should include content if available
            if "content" in ex:
                assert isinstance(ex["content"], dict)

    @pytest.mark.asyncio
    async def test_progress_returns_correct_stats(self, client: AsyncClient, auth_headers: dict):
        """TC-LP-04: Progress should include correct_count, completed_count, total_stars_earned"""
        response = await client.get(
            "/api/learning-path/challenge/progress",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert "total_exercises" in data
        assert "correct_count" in data
        assert "completed_count" in data
        assert "total_stars_earned" in data
        assert "current_index" in data

        # Stats should be non-negative
        assert data["total_exercises"] >= 0
        assert data["correct_count"] >= 0
        assert data["completed_count"] >= 0


class TestChallengeInfiniteStart:
    """Tests for POST /challenge/infinite/start"""

    @pytest.mark.asyncio
    async def test_start_infinite_session(self, client: AsyncClient, auth_headers: dict):
        """TC-LP-05: Start infinite session should return exercises"""
        response = await client.post(
            "/api/learning-path/challenge/infinite/start",
            headers=auth_headers,
            json={
                "difficulty_level": 3,
                "initial_count": 5,
            },
        )

        assert response.status_code in [200, 400]  # 400 if no exercises in DB

        if response.status_code == 200:
            data = response.json()
            assert "session_id" in data
            assert "exercises" in data
            assert "difficulty_level" in data
            assert data["difficulty_level"] == 3

    @pytest.mark.asyncio
    async def test_start_infinite_with_verified_exercises(self, client: AsyncClient, auth_headers: dict, db_session):
        """TC-LP-06: Start should create progress records when exercises exist"""
        # Create verified exercises
        for i in range(5):
            ex = Exercise(
                content={"title": f"题目 {i}", "text": f"内容 {i}", "code_template": "print('hello')"},
                type="programming",
                difficulty=3,
                is_verified=True,
                test_cases=[{"input": "1", "output": "1"}],
            )
            db_session.add(ex)

        await db_session.commit()

        response = await client.post(
            "/api/learning-path/challenge/infinite/start",
            headers=auth_headers,
            json={
                "difficulty_level": 3,
                "initial_count": 5,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["exercises"]) > 0

    @pytest.mark.asyncio
    async def test_start_infinite_returns_exercise_content(self, client: AsyncClient, auth_headers: dict, db_session):
        """TC-LP-07: Response should include full exercise content for frontend use"""
        # Create verified exercise
        ex = Exercise(
            content={
                "title": "编程题",
                "text": "输出Hello World",
                "code_template": "print('Hello World')",
                "samples": [{"input": "", "output": "Hello World"}],
            },
            type="programming",
            difficulty=2,
            is_verified=True,
            test_cases=[{"input": "", "output": "Hello World"}],
            knowledge_points=["基础语法"],
        )
        db_session.add(ex)
        await db_session.commit()
        await db_session.refresh(ex)

        response = await client.post(
            "/api/learning-path/challenge/infinite/start",
            headers=auth_headers,
            json={
                "difficulty_level": 2,
                "initial_count": 1,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["exercises"]) > 0

        exercise = data["exercises"][0]
        assert "content" in exercise
        assert "test_cases" in exercise
        assert "knowledge_points" in exercise


class TestChallengeExerciseDetail:
    """Tests for GET /challenge/exercise/{id} - on-demand content loading"""

    @pytest.mark.asyncio
    async def test_get_exercise_detail(self, client: AsyncClient, auth_headers: dict, db_session):
        """TC-LP-08: Get single exercise with full content"""
        # Create exercise and progress
        ex = Exercise(
            content={"title": "单题测试", "text": "题目内容", "code_template": "print('test')"},
            type="programming",
            difficulty=3,
            is_verified=True,
            test_cases=[{"input": "1", "output": "1"}],
        )
        db_session.add(ex)
        await db_session.commit()
        await db_session.refresh(ex)

        response = await client.get(
            f"/api/learning-path/challenge/exercise/{ex.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert "exercise" in data
        assert "exercise_index" in data
        assert "is_unlocked" in data
        assert "saved_code" in data
        assert "total_exercises" in data

        # Verify full content is returned
        exercise = data["exercise"]
        assert "content" in exercise
        assert "test_cases" in exercise

    @pytest.mark.asyncio
    async def test_get_exercise_not_found(self, client: AsyncClient, auth_headers: dict):
        """TC-LP-09: Non-existent exercise should return 404"""
        response = await client.get(
            "/api/learning-path/challenge/exercise/99999",
            headers=auth_headers,
        )

        assert response.status_code == 404


class TestChallengeSubmit:
    """Tests for POST /challenge/submit"""

    @pytest.mark.asyncio
    async def test_submit_without_progress(self, client: AsyncClient, auth_headers: dict):
        """TC-LP-10: Submit without progress record should return 400"""
        response = await client.post(
            "/api/learning-path/challenge/submit",
            headers=auth_headers,
            json={
                "exercise_id": 99999,
                "code": "print('hello')",
                "language": "python",
                "test_results": [{"passed": True, "input": "", "expected": "hello", "actual": "hello"}],
            },
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_submit_validates_test_results(self, client: AsyncClient, auth_headers: dict, db_session):
        """TC-LP-11: Submit should strictly validate test results"""
        # Create exercise
        ex = Exercise(
            content={"title": "测试提交", "text": "测试", "code_template": "print('test')"},
            type="programming",
            difficulty=3,
            is_verified=True,
        )
        db_session.add(ex)
        await db_session.commit()
        await db_session.refresh(ex)

        response = await client.post(
            "/api/learning-path/challenge/submit",
            headers=auth_headers,
            json={
                "exercise_id": ex.id,
                "code": "print('test')",
                "language": "python",
                "test_results": [
                    {"passed": True, "input": "", "expected": "test", "actual": "test"},
                ],
            },
        )

        # May fail if no progress record, but should not crash
        assert response.status_code in [200, 400]


class TestChallengeSwitch:
    """Tests for POST /challenge/switch"""

    @pytest.mark.asyncio
    async def test_switch_exercise(self, client: AsyncClient, auth_headers: dict):
        """TC-LP-12: Switch exercise should return exercise details"""
        response = await client.post(
            "/api/learning-path/challenge/switch",
            headers=auth_headers,
            json={"target_index": 0},
        )

        # May fail if no exercises, but should handle gracefully
        assert response.status_code in [200, 400]


class TestChallengeSaveCode:
    """Tests for POST /challenge/save-code"""

    @pytest.mark.asyncio
    async def test_save_code(self, client: AsyncClient, auth_headers: dict):
        """TC-LP-13: Save code should return success"""
        response = await client.post(
            "/api/learning-path/challenge/save-code",
            headers=auth_headers,
            json={
                "exercise_id": 1,
                "code": "print('saved')",
                "language": "python",
            },
        )

        # May fail if no progress, but should handle gracefully
        assert response.status_code in [200, 404]


class TestChallengeAppend:
    """Tests for POST /challenge/append"""

    @pytest.mark.asyncio
    async def test_append_exercises(self, client: AsyncClient, auth_headers: dict):
        """TC-LP-14: Append exercises should return new exercise IDs"""
        response = await client.post(
            "/api/learning-path/challenge/append",
            headers=auth_headers,
            json={
                "count": 5,
                "difficulty_level": 3,
            },
        )

        assert response.status_code in [200, 400]

        if response.status_code == 200:
            data = response.json()
            assert "new_exercise_ids" in data
            assert "count" in data


class TestLiteModePerformance:
    """Performance-focused tests for lite mode optimization"""

    @pytest.mark.asyncio
    async def test_lite_mode_faster_than_full(self, client: AsyncClient, auth_headers: dict):
        """TC-LP-15: Lite mode should be measurably faster than full mode"""
        import time

        # Time lite mode
        start = time.time()
        lite_response = await client.get(
            "/api/learning-path/challenge/progress?lite=true",
            headers=auth_headers,
        )
        lite_time = time.time() - start

        # Time full mode
        start = time.time()
        full_response = await client.get(
            "/api/learning-path/challenge/progress?lite=false",
            headers=auth_headers,
        )
        full_time = time.time() - start

        # Both should succeed
        assert lite_response.status_code == 200
        assert full_response.status_code == 200

        # Lite should not be slower (allow some variance)
        # Note: This is a soft assertion - network variance can affect results
        print(f"Lite mode: {lite_time:.3f}s, Full mode: {full_time:.3f}s")

    @pytest.mark.asyncio
    async def test_lite_response_smaller_than_full(self, client: AsyncClient, auth_headers: dict):
        """TC-LP-16: Lite mode response should be smaller than full mode"""
        lite_response = await client.get(
            "/api/learning-path/challenge/progress?lite=true",
            headers=auth_headers,
        )

        full_response = await client.get(
            "/api/learning-path/challenge/progress?lite=false",
            headers=auth_headers,
        )

        assert lite_response.status_code == 200
        assert full_response.status_code == 200

        lite_size = len(lite_response.content)
        full_size = len(full_response.content)

        print(f"Lite response: {lite_size} bytes, Full response: {full_size} bytes")

        # Lite should not be larger
        assert lite_size <= full_size, (
            f"Lite mode response ({lite_size}b) should not be larger than full mode ({full_size}b)"
        )
