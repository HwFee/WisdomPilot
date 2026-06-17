from sqlalchemy.ext.asyncio import AsyncSession


class ChallengeRewardService:
    def __init__(self, db: AsyncSession, legacy_service):
        self.db = db
        self.legacy_service = legacy_service

    async def get_stats(self, user_id: str) -> dict:
        return await self.legacy_service.get_stats(user_id=user_id)
