"""Tests that challenge rewards require backend-authoritative judging."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.exercise import Exercise
from app.models.arena_exercise_progress import ArenaExerciseProgress
from app.models.user_arena import UserArenaProfile
from app.services.challenge_path.submission import JudgeUnavailableError
from app.utils.security import decode_token


def _user_id_from_headers(auth_headers: dict) -> str:
    token = auth_headers["Authorization"].split(" ")[1]
    return decode_token(token)["sub"]


@pytest.mark.asyncio
async def test_forged_client_passing_results_do_not_award_progress(
    client: AsyncClient,
    auth_headers: dict,
    db_session,
    monkeypatch,
):
    exercise = Exercise(
        content={"title": "权威判题", "text": "输出 42", "code_template": "print(0)"},
        type="programming",
        difficulty=3,
        is_verified=True,
        test_cases=[{"input": "", "output": "42"}],
    )
    db_session.add(exercise)
    await db_session.commit()
    await db_session.refresh(exercise)

    user_id = _user_id_from_headers(auth_headers)
    progress = ArenaExerciseProgress(
        user_id=user_id,
        exercise_id=exercise.id,
        exercise_index=0,
        is_unlocked=True,
    )
    db_session.add(progress)
    await db_session.commit()

    async def fake_backend_judge(*args, **kwargs):
        return {
            "passed_count": 0,
            "total_count": 1,
            "results": [
                {"passed": False, "input": "", "expected": "42", "actual": "0", "message": "Wrong Answer"}
            ],
        }

    monkeypatch.setattr(
        "app.services.challenge_path.submission.run_authoritative_judge",
        fake_backend_judge,
        raising=False,
    )

    response = await client.post(
        "/api/learning-path/challenge/submit",
        headers=auth_headers,
        json={
            "exercise_id": exercise.id,
            "code": "print(0)",
            "language": "python",
            "test_results": [
                {"passed": True, "input": "", "expected": "42", "actual": "42"}
            ],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_correct"] is False
    assert data["stars_earned"] <= 0

    await db_session.refresh(progress)
    assert progress.is_correct is False

    profile_result = await db_session.execute(
        select(UserArenaProfile).where(UserArenaProfile.user_id == user_id)
    )
    profile = profile_result.scalar_one_or_none()
    assert profile is not None
    assert profile.stars == 0


@pytest.mark.asyncio
async def test_unavailable_judge_does_not_award_progress(
    client: AsyncClient,
    auth_headers: dict,
    db_session,
    monkeypatch,
):
    exercise = Exercise(
        content={"title": "权威判题", "text": "输出 42", "code_template": "print(0)"},
        type="programming",
        difficulty=3,
        is_verified=True,
        test_cases=[{"input": "", "output": "42"}],
    )
    db_session.add(exercise)
    await db_session.commit()
    await db_session.refresh(exercise)

    user_id = _user_id_from_headers(auth_headers)
    progress = ArenaExerciseProgress(
        user_id=user_id,
        exercise_id=exercise.id,
        exercise_index=0,
        is_unlocked=True,
    )
    db_session.add(progress)
    await db_session.commit()

    async def unavailable_judge(*args, **kwargs):
        raise JudgeUnavailableError("judge down")

    monkeypatch.setattr(
        "app.services.challenge_path.submission.run_authoritative_judge",
        unavailable_judge,
        raising=False,
    )

    response = await client.post(
        "/api/learning-path/challenge/submit",
        headers=auth_headers,
        json={
            "exercise_id": exercise.id,
            "code": "print(42)",
            "language": "python",
            "test_results": [
                {"passed": True, "input": "", "expected": "42", "actual": "42"}
            ],
        },
    )

    assert response.status_code == 503
    data = response.json()
    assert "Judge service unavailable" in data.get("detail", "")

    await db_session.refresh(progress)
    assert progress.is_correct is False
    assert progress.is_completed is False


@pytest.mark.asyncio
async def test_programming_exercise_without_backend_test_cases_is_rejected(
    client: AsyncClient,
    auth_headers: dict,
    db_session,
):
    exercise = Exercise(
        content={"title": "无后台测试", "text": "输出 1", "code_template": "print(1)"},
        type="programming",
        difficulty=3,
        is_verified=True,
        test_cases=[],
    )
    db_session.add(exercise)
    await db_session.commit()
    await db_session.refresh(exercise)

    user_id = _user_id_from_headers(auth_headers)
    progress = ArenaExerciseProgress(
        user_id=user_id,
        exercise_id=exercise.id,
        exercise_index=0,
        is_unlocked=True,
    )
    db_session.add(progress)
    await db_session.commit()

    response = await client.post(
        "/api/learning-path/challenge/submit",
        headers=auth_headers,
        json={
            "exercise_id": exercise.id,
            "code": "print(1)",
            "language": "python",
            "test_results": [
                {"passed": True, "input": "", "expected": "1", "actual": "1"}
            ],
        },
    )

    assert response.status_code == 400
    data = response.json()
    assert "backend test cases" in data.get("detail", "").lower()

    await db_session.refresh(progress)
    assert progress.is_correct is False
    assert progress.is_completed is False

    profile_result = await db_session.execute(
        select(UserArenaProfile).where(UserArenaProfile.user_id == user_id)
    )
    profile = profile_result.scalar_one_or_none()
    assert profile is None or profile.stars == 0
