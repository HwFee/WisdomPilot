from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.models.arena_exercise_progress import ArenaExerciseProgress
from app.models.exercise import Exercise
from app.models.user import User
from app.services.challenge_path.progress import ChallengeProgressService
from app.services.challenge_path.selection import ChallengeSelectionService


def challenge_owner_lock_query(user_id: str) -> Select[tuple[str]]:
    return select(User.id).where(User.id == user_id).with_for_update()


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
