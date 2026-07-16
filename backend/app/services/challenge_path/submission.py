"""Challenge submission service with backend-authoritative judging."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exercise import Exercise
from app.services.challenge_path.errors import (
    ChallengeExerciseNotFoundError,
    JudgeUnavailableError,
    MissingChallengeTestCasesError,
    UnsupportedChallengeLanguageError,
)
from app.services.judge0 import (
    Judge0Service,
    LANGUAGE_C,
    LANGUAGE_CPP,
    LANGUAGE_JAVASCRIPT,
    LANGUAGE_JAVA,
    LANGUAGE_PYTHON,
    LANGUAGE_RUST,
    LANGUAGE_TYPESCRIPT,
)

logger = logging.getLogger(__name__)

# Map frontend language strings to Judge0 language IDs
LANGUAGE_NAME_TO_JUDGE0_ID = {
    "python": LANGUAGE_PYTHON,
    "javascript": LANGUAGE_JAVASCRIPT,
    "typescript": LANGUAGE_TYPESCRIPT,
    "c": LANGUAGE_C,
    "cpp": LANGUAGE_CPP,
    "c++": LANGUAGE_CPP,
    "java": LANGUAGE_JAVA,
    "rust": LANGUAGE_RUST,
}


async def run_authoritative_judge(
    *,
    code: str,
    language: str,
    test_cases: list[dict],
    judge0: Judge0Service | None = None,
) -> dict:
    """Run final challenge judging on backend-owned test cases.

    Args:
        code: User-submitted source code.
        language: Programming language name (e.g., "python", "javascript").
        test_cases: List of backend-owned test cases, each with "input" and "output".
        judge0: Optional Judge0Service instance for dependency injection/tests.

    Returns:
        dict with shape:
        {
            "passed_count": int,
            "total_count": int,
            "results": [
                {"passed": bool, "input": str, "expected": str, "actual": str, "message": str | None}
            ],
        }

    Raises:
        ValueError: If the language is not supported for judging.
        JudgeUnavailableError: If the judge service fails or is unreachable.
    """
    language_id = LANGUAGE_NAME_TO_JUDGE0_ID.get(language.lower())
    if language_id is None:
        raise UnsupportedChallengeLanguageError(language)

    if not test_cases:
        return {
            "passed_count": 0,
            "total_count": 0,
            "results": [],
        }

    # Normalize test_cases to the format Judge0 expects
    judge_test_cases = [
        {"input": tc.get("input", ""), "expected_output": tc.get("output", "")}
        for tc in test_cases
    ]

    judge0_instance = judge0 or Judge0Service()
    try:
        batch_result = await judge0_instance.execute_batch(
            code=code,
            language_id=language_id,
            test_cases=judge_test_cases,
        )
    except Exception as exc:
        logger.error("Judge0 batch execution failed: %s", exc)
        raise JudgeUnavailableError("Judge service unavailable") from exc
    finally:
        if judge0 is None and judge0_instance is not None:
            await judge0_instance.close()

    # Map Judge0 batch result to the expected authoritative shape
    results = []
    for raw in batch_result.get("results", []):
        results.append({
            "passed": raw.get("passed", False),
            "input": raw.get("input", ""),
            "expected": raw.get("expected", ""),
            "actual": raw.get("actual", ""),
            "message": raw.get("message"),
        })

    return {
        "passed_count": batch_result.get("passed_count", 0),
        "total_count": batch_result.get("total_count", 0),
        "results": results,
    }


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
    ) -> dict:
        """Submit exercise answer with backend-authoritative judging.

        The client-supplied ``test_results`` are accepted for compatibility
        but are **not** used as the sole source of correctness.  The backend
        runs its own judge against the exercise's stored ``test_cases`` and
        uses that authoritative verdict for all correctness-dependent state
        (progress, stars, tier, cores).

        If the judge is unavailable the endpoint returns an HTTP error and
        does **not** mutate correctness-dependent state.

        Programming exercises without backend test cases are rejected outright
        so that client-forged results cannot be used to claim rewards.
        """
        # Load exercise to get backend-owned test cases
        exercise_result = await self.db.execute(
            select(Exercise).where(Exercise.id == exercise_id)
        )
        exercise = exercise_result.scalar_one_or_none()
        if not exercise:
            raise ChallengeExerciseNotFoundError(exercise_id)

        # Run authoritative judge on backend-owned test cases
        backend_test_cases = exercise.test_cases or []
        if exercise.type == "programming":
            if not backend_test_cases:
                raise MissingChallengeTestCasesError(exercise_id)
            authoritative_result = await run_authoritative_judge(
                code=code,
                language=language,
                test_cases=backend_test_cases,
            )

            authoritative_test_results = authoritative_result["results"]
        else:
            # Non-programming exercises fall back to client-supplied results
            # for compatibility.  Challenge path only uses programming
            # exercises in this change.
            authoritative_test_results = test_results

        # Delegate to legacy service for mutation / reward logic.
        # The legacy service determines correctness from the test_results
        # we pass in, so we pass the authoritative results.
        return await self.legacy_service._submit_exercise_impl(
            user_id=user_id,
            exercise_id=exercise_id,
            code=code,
            language=language,
            test_results=authoritative_test_results,
        )
