"""Tests that challenge rewards require backend-authoritative judging."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.exercise import Exercise
from app.models.arena_exercise_progress import ArenaExerciseProgress
from app.models.user_arena import UserArenaProfile
from app.utils.security import decode_token


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

    user_id = decode_token(auth_headers["Authorization"].split(" ")[1])["sub"]
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
    assert profile is None or profile.stars == 0
