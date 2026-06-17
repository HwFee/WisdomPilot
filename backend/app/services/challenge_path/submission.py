from sqlalchemy.ext.asyncio import AsyncSession


class ChallengeSubmissionService:
    def __init__(self, db: AsyncSession, legacy_service):
        self.db = db
        self.legacy_service = legacy_service

    async def submit_exercise(
        self,
        user_id: str,
        exercise_id: int,
        code: str,
        language: str,
        test_results: list[dict],
        time_spent: int | None = None,
        hint_used: bool = False,
    ) -> dict:
        return await self.legacy_service.submit_exercise(
            user_id=user_id,
            exercise_id=exercise_id,
            code=code,
            language=language,
            test_results=test_results,
            time_spent=time_spent,
            hint_used=hint_used,
        )


async def run_authoritative_judge(
    exercise_id: int,
    code: str,
    language: str,
) -> dict:
    """Placeholder for authoritative judge runner.

    Will be implemented in a later task. For now, raises NotImplementedError
    so that tests can monkeypatch it when needed.
    """
    raise NotImplementedError("run_authoritative_judge is not yet implemented")
