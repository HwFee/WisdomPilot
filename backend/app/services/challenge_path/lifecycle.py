from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.models.arena_exercise_progress import ArenaExerciseProgress
from app.models.exercise import Exercise
from app.models.user import User
from app.services.challenge_path.errors import (
    ChallengeExerciseDetailNotFoundError,
    ChallengeProgressNotFoundError,
)
from app.services.challenge_path.progress import ChallengeProgressService
from app.services.challenge_path.selection import ChallengeSelectionService


def challenge_owner_lock_query(user_id: str) -> Select[tuple[str]]:
    return select(User.id).where(User.id == user_id).with_for_update()


def challenge_progress_lock_query(
    *, user_id: str, exercise_id: int
) -> Select[tuple[ArenaExerciseProgress]]:
    return (
        select(ArenaExerciseProgress)
        .where(
            ArenaExerciseProgress.user_id == user_id,
            ArenaExerciseProgress.exercise_id == exercise_id,
        )
        .with_for_update()
    )


class ChallengePathLifecycleService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.selection = ChallengeSelectionService(db)
        self.progress = ChallengeProgressService(db)

    async def _lock_owner(self, user_id: str) -> None:
        result = await self.db.execute(challenge_owner_lock_query(user_id))
        result.scalar_one()

    def _add_progress_rows(
        self,
        *,
        user_id: str,
        exercises: list[Exercise],
        start_index: int,
        unlock_first: bool,
    ) -> list[ArenaExerciseProgress]:
        created = []
        for index_offset, exercise in enumerate(exercises):
            progress = ArenaExerciseProgress(
                user_id=user_id,
                exercise_id=exercise.id,
                exercise_index=start_index + index_offset,
                is_unlocked=unlock_first and index_offset == 0,
            )
            self.db.add(progress)
            created.append(progress)
        return created

    async def start_path(
        self,
        *,
        user_id: str,
        difficulty_level: int,
        initial_count: int,
    ) -> tuple[list[Exercise], bool]:
        await self._lock_owner(user_id)
        progress_records = await self.progress.list_user_progress(user_id)
        if progress_records:
            exercises = await self.progress.get_exercises_for_progress(
                progress_records
            )
            return exercises, False

        exercises = await self.selection.select_initial_exercises(
            user_id=user_id,
            difficulty_level=difficulty_level,
            count=initial_count,
        )
        self._add_progress_rows(
            user_id=user_id,
            exercises=exercises,
            start_index=0,
            unlock_first=True,
        )
        await self.db.flush()
        return exercises, True

    async def append_exercises(
        self,
        *,
        user_id: str,
        difficulty_level: int | None,
        count: int,
    ) -> list[int]:
        await self._lock_owner(user_id)
        progress_records = await self.progress.list_user_progress(user_id)
        existing_ids = [progress.exercise_id for progress in progress_records]
        selected = await self.selection.select_append_exercises(
            user_id=user_id,
            existing_ids=existing_ids,
            difficulty_level=difficulty_level,
            count=count,
        )
        if not selected:
            return []

        last_progress = max(
            progress_records,
            key=lambda progress: progress.exercise_index,
            default=None,
        )
        start_index = (
            last_progress.exercise_index + 1 if last_progress is not None else 0
        )
        unlock_first = last_progress is None or bool(last_progress.is_completed)
        self._add_progress_rows(
            user_id=user_id,
            exercises=selected,
            start_index=start_index,
            unlock_first=unlock_first,
        )
        await self.db.flush()
        return [exercise.id for exercise in selected]

    async def save_code(
        self,
        *,
        user_id: str,
        exercise_id: int,
        code: str,
        language: str,
    ) -> None:
        result = await self.db.execute(
            challenge_progress_lock_query(
                user_id=user_id,
                exercise_id=exercise_id,
            )
        )
        progress = result.scalar_one_or_none()
        if progress is None:
            raise ChallengeProgressNotFoundError(exercise_id)
        progress.saved_codes = {
            **(progress.saved_codes or {}),
            language: code,
        }
        progress.current_language = language
        await self.db.flush()

    async def get_or_attach_exercise(
        self,
        *,
        user_id: str,
        exercise_id: int,
    ) -> dict:
        detail = await self.progress.get_existing_exercise_detail(
            user_id=user_id,
            exercise_id=exercise_id,
        )
        if detail is not None:
            return detail

        await self._lock_owner(user_id)
        detail = await self.progress.get_existing_exercise_detail(
            user_id=user_id,
            exercise_id=exercise_id,
        )
        if detail is not None:
            return detail

        return await self._attach_verified_exercise(
            user_id=user_id,
            exercise_id=exercise_id,
        )

    async def _attach_verified_exercise(
        self,
        *,
        user_id: str,
        exercise_id: int,
    ) -> dict:
        exercise_result = await self.db.execute(
            select(Exercise).where(
                Exercise.id == exercise_id,
                Exercise.is_verified,
            )
        )
        exercise = exercise_result.scalar_one_or_none()
        if exercise is None:
            raise ChallengeExerciseDetailNotFoundError()

        progress_records = await self.progress.list_user_progress(user_id)
        exercise_index = len(progress_records)
        created_progress = self._add_progress_rows(
            user_id=user_id,
            exercises=[exercise],
            start_index=exercise_index,
            unlock_first=exercise_index == 0,
        )[0]
        await self.db.flush()
        return self.progress.build_exercise_detail(
            progress=created_progress,
            exercise=exercise,
        )
