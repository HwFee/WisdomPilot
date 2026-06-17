from sqlalchemy.ext.asyncio import AsyncSession


DEFAULT_DIFFICULTY_LEVEL = 3
DEFAULT_INITIAL_COUNT = 3
DEFAULT_APPEND_COUNT = 5


class ChallengeSelectionService:
    def __init__(self, db: AsyncSession, legacy_service):
        self.db = db
        self.legacy_service = legacy_service

    async def get_or_create_challenge_path(
        self,
        user_id: str,
        difficulty_level: int = DEFAULT_DIFFICULTY_LEVEL,
        initial_count: int = DEFAULT_INITIAL_COUNT,
    ) -> tuple[list, bool]:
        return await self.legacy_service.get_or_create_challenge_path(
            user_id=user_id,
            difficulty_level=difficulty_level,
            initial_count=initial_count,
        )

    async def append_exercises(
        self,
        user_id: str,
        difficulty_level: int | None = None,
        count: int = DEFAULT_APPEND_COUNT,
    ) -> list[int]:
        return await self.legacy_service.append_exercises(
            user_id=user_id,
            difficulty_level=difficulty_level,
            count=count,
        )
