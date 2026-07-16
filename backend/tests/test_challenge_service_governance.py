from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.challenge import Challenge, ChallengeType
from app.models.user import User
from app.services.challenge import ChallengeService, resolve_challenge_target
from app.services.challenge_errors import InvalidChallengeDefinitionError


def challenge_definition(
    challenge_type: ChallengeType,
    requirements: dict[str, object],
) -> Challenge:
    return Challenge(
        code=f"TEST_{challenge_type.value}",
        title="Target test",
        type=challenge_type.value,
        requirements=requirements,
        rewards={},
    )


@pytest.mark.parametrize(
    ("challenge_type", "requirements", "expected"),
    [
        (ChallengeType.EXERCISE_COUNT, {"exercise_count": 5}, 5),
        (ChallengeType.STREAK, {"days": 7}, 7),
        (ChallengeType.TIME_SPENT, {"minutes": 30}, 30),
        (ChallengeType.ACCURACY, {"accuracy": 80}, 80),
        (ChallengeType.CHAPTER_COMPLETE, {"chapter_id": 1}, 1),
        (ChallengeType.COURSE_COMPLETE, {"course_id": 1}, 1),
        (ChallengeType.STREAK, {"target": 4, "days": 7}, 4),
    ],
)
def test_resolve_challenge_target_uses_type_specific_requirement(
    challenge_type: ChallengeType,
    requirements: dict[str, object],
    expected: int,
) -> None:
    assert resolve_challenge_target(
        challenge_definition(challenge_type, requirements)
    ) == expected


@pytest.mark.parametrize("invalid_target", [None, True, 0, -1, "5"])
def test_resolve_challenge_target_rejects_invalid_definition(
    invalid_target: object,
) -> None:
    challenge = challenge_definition(
        ChallengeType.EXERCISE_COUNT,
        {} if invalid_target is None else {"exercise_count": invalid_target},
    )

    with pytest.raises(InvalidChallengeDefinitionError):
        resolve_challenge_target(challenge)


@pytest.mark.asyncio
async def test_start_streak_challenge_uses_days_target(
    db_session: AsyncSession, auth_user: User
) -> None:
    challenge = challenge_definition(ChallengeType.STREAK, {"days": 7})
    db_session.add(challenge)
    await db_session.commit()
    service = ChallengeService()

    user_challenge = await service.start_challenge(
        db_session, auth_user, challenge.id
    )

    assert user_challenge.target_value == 7


@pytest.mark.asyncio
async def test_default_initialization_fills_missing_codes_without_committing(
    db_session: AsyncSession,
) -> None:
    service = ChallengeService()
    db_session.add(
        Challenge(
            code="FIRST_STEPS",
            title="Existing",
            type=ChallengeType.EXERCISE_COUNT.value,
            requirements={"exercise_count": 5},
            rewards={"quota_bonus": 10},
        )
    )
    await db_session.commit()

    with patch.object(db_session, "commit", new=AsyncMock()) as commit_mock:
        await service.create_default_challenges(db_session)

    codes = set(
        (await db_session.execute(select(Challenge.code))).scalars().all()
    )
    assert codes == {"FIRST_STEPS", "CHAPTER_MASTER", "STREAK_7"}
    commit_mock.assert_not_awaited()
