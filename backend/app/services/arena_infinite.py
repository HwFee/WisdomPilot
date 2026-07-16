"""Challenge Path Service (挑战之路服务)

Service for managing Challenge Path:
- No session concept - direct course-based management
- Persistent exercise records per user per course
- New exercises are appended to existing list
- exercise_id is stable for wrong question book / favorites integration

Design:
- Each course has ONE challenge path per user
- Old exercises have fixed index, new exercises are appended
- exercise_id is used for cross-references (wrong book, favorites, notes)
- Uses AdaptiveRecommendationService for intelligent exercise matching based on user profile
"""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exercise import Exercise

# Import focused services
from app.services.challenge_path.lifecycle import ChallengePathLifecycleService
from app.services.challenge_path.selection import ChallengeSelectionService
from app.services.challenge_path.progress import ChallengeProgressService
from app.services.challenge_path.rewards import ChallengeRewardService

class ChallengePathService:
    """Service for Challenge Path operations - delegates to focused services."""

    def __init__(self, db: AsyncSession):
        self.lifecycle = ChallengePathLifecycleService(db)
        self.selection = ChallengeSelectionService(db)
        self.progress = ChallengeProgressService(db)
        self.rewards = ChallengeRewardService(db)

    # ========================================
    # Compatibility delegates - Selection
    # ========================================

    async def get_or_create_challenge_path(
        self,
        user_id: str,
        difficulty_level: int = 3,
        initial_count: int = 3,
    ) -> tuple[list[Exercise], bool]:
        """Get existing exercises or create initial set."""
        return await self.lifecycle.start_path(
            user_id=user_id,
            difficulty_level=difficulty_level,
            initial_count=initial_count,
        )

    async def append_exercises(
        self,
        user_id: str,
        difficulty_level: Optional[int] = None,
        count: int = 5,
    ) -> list[int]:
        """Append more exercises to the challenge path."""
        return await self.selection.append_exercises(
            user_id=user_id,
            difficulty_level=difficulty_level,
            count=count,
        )

    # ========================================
    # Compatibility delegates - Progress
    # ========================================

    async def get_progress(self, user_id: str, lite: bool = True) -> dict:
        """Get current progress for challenge path."""
        return await self.progress.get_progress(user_id=user_id, lite=lite)

    async def get_exercise_by_id(
        self, user_id: str, exercise_id: int
    ) -> Optional[dict]:
        """Get specific exercise progress by exercise_id."""
        return await self.progress.get_exercise_by_id(
            user_id=user_id, exercise_id=exercise_id
        )

    async def get_exercise_by_index(
        self, user_id: str, exercise_index: int
    ) -> Optional[dict]:
        """Get exercise by its index in the challenge path."""
        return await self.progress.get_exercise_by_index(
            user_id=user_id, exercise_index=exercise_index
        )

    async def save_code(
        self, user_id: str, exercise_id: int, code: str, language: str
    ) -> bool:
        """Save code for a specific language."""
        return await self.progress.save_code(
            user_id=user_id,
            exercise_id=exercise_id,
            code=code,
            language=language,
        )

    async def switch_exercise(
        self, user_id: str, target_index: int
    ) -> dict:
        """Switch to a different exercise by index."""
        return await self.progress.switch_exercise(
            user_id=user_id, target_index=target_index
        )

    async def get_stats(self, user_id: str) -> dict:
        """Get challenge path statistics."""
        return await self.rewards.get_stats(user_id=user_id)


def get_challenge_path_service(db: AsyncSession) -> ChallengePathService:
    """Get ChallengePathService instance."""
    return ChallengePathService(db)


# Backward compatibility alias
ArenaInfiniteService = ChallengePathService
get_arena_infinite_service = get_challenge_path_service
