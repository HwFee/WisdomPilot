from sqlalchemy.ext.asyncio import AsyncSession


class ChallengeProgressService:
    def __init__(self, db: AsyncSession, legacy_service):
        self.db = db
        self.legacy_service = legacy_service

    async def get_progress(self, user_id: str, lite: bool = True) -> dict:
        return await self.legacy_service.get_progress(user_id=user_id, lite=lite)

    async def get_exercise_by_id(self, user_id: str, exercise_id: int) -> dict | None:
        return await self.legacy_service.get_exercise_by_id(
            user_id=user_id,
            exercise_id=exercise_id,
        )

    async def get_exercise_by_index(self, user_id: str, exercise_index: int) -> dict | None:
        return await self.legacy_service.get_exercise_by_index(
            user_id=user_id,
            exercise_index=exercise_index,
        )

    async def save_code(self, user_id: str, exercise_id: int, code: str, language: str) -> bool:
        return await self.legacy_service.save_code(
            user_id=user_id,
            exercise_id=exercise_id,
            code=code,
            language=language,
        )

    async def switch_exercise(self, user_id: str, target_index: int) -> dict:
        return await self.legacy_service.switch_exercise(
            user_id=user_id,
            target_index=target_index,
        )
