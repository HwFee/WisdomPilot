"""
Challenge Path Service (挑战之路服务)

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

import random
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload

from app.models.arena_exercise_progress import ArenaExerciseProgress
from app.models.exercise import Exercise
from app.models.chapter import Chapter
from app.models.user import User
from app.services.wrong_question import wrong_question_service
from app.services.adaptive_recommendation import AdaptiveRecommendationService, DIFFICULTY_LABELS


class ChallengePathService:
    """Service for Challenge Path operations - no session concept"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ========================================
    # Core Methods - Course-based Management
    # ========================================

    async def get_or_create_challenge_path(
        self,
        user_id: str,
        course_id: int,
        difficulty_level: int = 3,
        initial_count: int = 10,
    ) -> tuple[list[Exercise], bool]:
        """Get existing exercises or create initial set

        Returns:
            tuple: (exercises, is_new)
        """
        # Get existing progress records
        existing_progress = await self._get_user_progress(user_id, course_id)

        if existing_progress:
            # User has existing exercises - fetch them
            exercises = await self._get_exercises_from_progress(existing_progress)
            return exercises, False

        # No existing exercises - create initial set
        exercises = await self._create_initial_exercises(
            user_id, course_id, difficulty_level, initial_count
        )
        return exercises, True

    async def _get_user_progress(
        self,
        user_id: str,
        course_id: int,
    ) -> list[ArenaExerciseProgress]:
        """Get all progress records for user's challenge path in a course"""
        result = await self.db.execute(
            select(ArenaExerciseProgress).where(
                ArenaExerciseProgress.user_id == user_id,
                ArenaExerciseProgress.course_id == course_id,
            ).order_by(ArenaExerciseProgress.exercise_index)
        )
        return list(result.scalars().all())

    async def _get_exercises_from_progress(
        self,
        progress_records: list[ArenaExerciseProgress],
    ) -> list[Exercise]:
        """Fetch Exercise objects from progress records"""
        exercise_ids = [p.exercise_id for p in progress_records]
        if not exercise_ids:
            return []

        result = await self.db.execute(
            select(Exercise).where(Exercise.id.in_(exercise_ids))
        )
        exercises_map = {ex.id: ex for ex in result.scalars().all()}

        # Return in order of exercise_index
        return [exercises_map[p.exercise_id] for p in progress_records if p.exercise_id in exercises_map]

    async def _create_initial_exercises(
        self,
        user_id: str,
        course_id: int,
        difficulty_level: int,
        count: int,
    ) -> list[Exercise]:
        """Create initial exercise set for a new challenge path using adaptive recommendation"""
        # Get user for adaptive recommendation
        user_result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()

        if user:
            # Use adaptive recommendation service for intelligent matching
            adaptive_service = AdaptiveRecommendationService(self.db)
            recommendation = await adaptive_service.get_recommendations(
                user=user,
                limit=count,
                min_difficulty=max(1, difficulty_level - 1),
                max_difficulty=min(8, difficulty_level + 1),
                course_id=course_id,
                learning_path="challenge",
            )

            # Extract exercise IDs from recommendations
            recommended_ids = [rec["exercise_id"] for rec in recommendation.get("recommendations", [])]

            if recommended_ids:
                # Fetch recommended exercises
                result = await self.db.execute(
                    select(Exercise).where(Exercise.id.in_(recommended_ids))
                )
                exercises_map = {ex.id: ex for ex in result.scalars().all()}
                # Preserve recommendation order
                selected = [exercises_map[eid] for eid in recommended_ids if eid in exercises_map]

                if len(selected) >= count:
                    # Create progress records
                    for i, ex in enumerate(selected[:count]):
                        progress = ArenaExerciseProgress(
                            user_id=user_id,
                            course_id=course_id,
                            exercise_id=ex.id,
                            exercise_index=i,
                            is_unlocked=(i == 0),
                        )
                        self.db.add(progress)

                    await self.db.flush()
                    return selected[:count]

        # Fallback: traditional random selection if adaptive fails
        chapters_result = await self.db.execute(
            select(Chapter.id).where(Chapter.course_id == course_id)
        )
        chapter_ids = [c[0] for c in chapters_result.fetchall()]

        if not chapter_ids:
            raise ValueError("No chapters available for this course")

        exercises_result = await self.db.execute(
            select(Exercise).where(
                Exercise.chapter_id.in_(chapter_ids),
                Exercise.difficulty == difficulty_level
            ).limit(count * 3)
        )
        all_exercises = exercises_result.scalars().all()

        if len(all_exercises) < count:
            exercises_result = await self.db.execute(
                select(Exercise).where(
                    Exercise.chapter_id.in_(chapter_ids)
                ).limit(count * 3)
            )
            all_exercises = exercises_result.scalars().all()

        if len(all_exercises) < count:
            raise ValueError("Not enough exercises available")

        selected = random.sample(list(all_exercises), count)

        for i, ex in enumerate(selected):
            progress = ArenaExerciseProgress(
                user_id=user_id,
                course_id=course_id,
                exercise_id=ex.id,
                exercise_index=i,
                is_unlocked=(i == 0),
            )
            self.db.add(progress)

        await self.db.flush()
        return selected

    # ========================================
    # Progress Methods
    # ========================================

    async def get_progress(
        self,
        user_id: str,
        course_id: int,
    ) -> dict:
        """Get current progress for challenge path"""
        progress_records = await self._get_user_progress(user_id, course_id)

        if not progress_records:
            return {
                "total_exercises": 0,
                "exercises": [],
                "correct_count": 0,
                "completed_count": 0,
                "total_xp_earned": 0,
                "current_index": 0,
            }

        # Get exercises
        exercise_ids = [p.exercise_id for p in progress_records]
        exercises_result = await self.db.execute(
            select(Exercise).where(Exercise.id.in_(exercise_ids))
        )
        exercises = {ex.id: ex for ex in exercises_result.scalars().all()}

        # Find current index (first incomplete or first after last completed)
        current_index = 0
        for i, p in enumerate(progress_records):
            if not p.is_completed:
                current_index = i
                break
            current_index = i + 1
        if current_index >= len(progress_records):
            current_index = len(progress_records) - 1

        # Build progress list with full exercise content
        progress_list = []
        for p in progress_records:
            ex = exercises.get(p.exercise_id)
            if ex:
                progress_list.append({
                    "exercise_id": p.exercise_id,
                    "exercise_index": p.exercise_index,
                    "is_completed": p.is_completed,
                    "is_correct": p.is_correct,
                    "is_unlocked": p.is_unlocked,
                    "saved_code": (p.saved_codes or {}).get(p.current_language, ""),
                    "current_language": p.current_language,
                    "title": (ex.content or {}).get("title", f"题目 {p.exercise_index + 1}"),
                    "difficulty": ex.difficulty,
                    # 完整题目内容
                    "content": {
                        "text": (ex.content or {}).get("text", ""),
                        "title": (ex.content or {}).get("title", ""),
                        "description": (ex.content or {}).get("description", ""),
                        "options": (ex.content or {}).get("options", []),
                        "code_template": (ex.content or {}).get("code_template", ""),
                        "input_format": (ex.content or {}).get("input_format", ""),
                        "output_format": (ex.content or {}).get("output_format", ""),
                        "sample_input": (ex.content or {}).get("sample_input", ""),
                        "sample_output": (ex.content or {}).get("sample_output", ""),
                        "samples": (ex.content or {}).get("samples", []),
                        "time_limit": (ex.content or {}).get("time_limit", 1000),
                        "memory_limit": (ex.content or {}).get("memory_limit", 256),
                    },
                    "knowledge_points": ex.knowledge_points or [],
                    "test_cases": ex.test_cases if ex.type == "programming" else None,
                    "type": ex.type,
                })

        # Calculate stats
        correct_count = sum(1 for p in progress_records if p.is_correct)
        completed_count = sum(1 for p in progress_records if p.is_completed)

        return {
            "total_exercises": len(progress_records),
            "exercises": progress_list,
            "correct_count": correct_count,
            "completed_count": completed_count,
            "total_xp_earned": correct_count * 10,
            "current_index": current_index,
        }

    async def get_exercise_by_id(
        self,
        user_id: str,
        course_id: int,
        exercise_id: int,
    ) -> Optional[dict]:
        """Get specific exercise progress by exercise_id (for wrong book / favorites)"""
        result = await self.db.execute(
            select(ArenaExerciseProgress).where(
                ArenaExerciseProgress.user_id == user_id,
                ArenaExerciseProgress.course_id == course_id,
                ArenaExerciseProgress.exercise_id == exercise_id,
            )
        )
        progress = result.scalar_one_or_none()
        if not progress:
            return None

        # Get exercise
        ex_result = await self.db.execute(
            select(Exercise).where(Exercise.id == exercise_id)
        )
        exercise = ex_result.scalar_one_or_none()
        if not exercise:
            return None

        return {
            "exercise_id": progress.exercise_id,
            "exercise_index": progress.exercise_index,
            "is_completed": progress.is_completed,
            "is_correct": progress.is_correct,
            "is_unlocked": progress.is_unlocked,
            "saved_code": (progress.saved_codes or {}).get(progress.current_language, ""),
            "current_language": progress.current_language,
            "title": (exercise.content or {}).get("title", f"题目 {progress.exercise_index + 1}"),
            "difficulty": exercise.difficulty,
            "exercise": exercise,
        }

    async def get_exercise_by_index(
        self,
        user_id: str,
        course_id: int,
        exercise_index: int,
    ) -> Optional[dict]:
        """Get exercise by its index in the challenge path"""
        result = await self.db.execute(
            select(ArenaExerciseProgress).where(
                ArenaExerciseProgress.user_id == user_id,
                ArenaExerciseProgress.course_id == course_id,
                ArenaExerciseProgress.exercise_index == exercise_index,
            )
        )
        progress = result.scalar_one_or_none()
        if not progress:
            return None

        return await self.get_exercise_by_id(user_id, course_id, progress.exercise_id)

    # ========================================
    # Action Methods
    # ========================================

    async def submit_exercise(
        self,
        user_id: str,
        course_id: int,
        exercise_id: int,
        code: str,
        language: str,
        test_results: list[dict],
    ) -> dict:
        """Submit exercise answer and update progress"""
        # Get progress record
        result = await self.db.execute(
            select(ArenaExerciseProgress).where(
                ArenaExerciseProgress.user_id == user_id,
                ArenaExerciseProgress.course_id == course_id,
                ArenaExerciseProgress.exercise_id == exercise_id,
            )
        )
        progress = result.scalar_one_or_none()
        if not progress:
            raise ValueError("Progress record not found")

        # Determine if correct
        all_passed = all(r.get("passed", False) for r in test_results)
        now = datetime.utcnow()

        # Update progress
        progress.is_completed = True
        progress.is_correct = all_passed
        progress.last_attempt_at = now
        progress.attempt_count += 1
        progress.current_language = language

        # Save code for this language
        saved_codes = progress.saved_codes or {}
        saved_codes[language] = code
        progress.saved_codes = saved_codes

        if not progress.first_attempt_at:
            progress.first_attempt_at = now

        if all_passed and not progress.correct_at:
            progress.correct_at = now

        # Collect wrong question if incorrect
        added_to_wrong_book = False
        if not all_passed:
            exercise_result = await self.db.execute(
                select(Exercise).where(Exercise.id == exercise_id)
            )
            exercise = exercise_result.scalar_one_or_none()
            if exercise:
                # Use exercise_key format: arena-{courseId}-{exerciseId}
                exercise_key = f"arena-{course_id}-{exercise_id}"
                await wrong_question_service.collect_wrong_question_by_key(
                    db=self.db,
                    user_id=user_id,
                    exercise_key=exercise_key,
                    user_answer=code,
                    course_id=course_id,
                    exercise_content=exercise.content,
                    exercise_type=exercise.type,
                    knowledge_points=exercise.knowledge_points,
                )
                added_to_wrong_book = True

        # Unlock next exercise
        next_unlocked = False
        next_result = await self.db.execute(
            select(ArenaExerciseProgress).where(
                ArenaExerciseProgress.user_id == user_id,
                ArenaExerciseProgress.course_id == course_id,
                ArenaExerciseProgress.exercise_index == progress.exercise_index + 1,
            )
        )
        next_progress = next_result.scalar_one_or_none()
        if next_progress and not next_progress.is_unlocked:
            next_progress.is_unlocked = True
            next_unlocked = True

        await self.db.commit()

        return {
            "is_correct": all_passed,
            "test_results": test_results,
            "xp_earned": 10 if all_passed else 0,
            "next_unlocked": next_unlocked,
            "added_to_wrong_book": added_to_wrong_book,
        }

    async def save_code(
        self,
        user_id: str,
        course_id: int,
        exercise_id: int,
        code: str,
        language: str,
    ) -> bool:
        """Save code for a specific language"""
        result = await self.db.execute(
            select(ArenaExerciseProgress).where(
                ArenaExerciseProgress.user_id == user_id,
                ArenaExerciseProgress.course_id == course_id,
                ArenaExerciseProgress.exercise_id == exercise_id,
            )
        )
        progress = result.scalar_one_or_none()
        if not progress:
            return False

        saved_codes = progress.saved_codes or {}
        saved_codes[language] = code
        progress.saved_codes = saved_codes
        progress.current_language = language

        await self.db.commit()
        return True

    async def switch_exercise(
        self,
        user_id: str,
        course_id: int,
        target_index: int,
    ) -> dict:
        """Switch to a different exercise by index"""
        # Get total count
        count_result = await self.db.execute(
            select(func.count()).select_from(ArenaExerciseProgress).where(
                ArenaExerciseProgress.user_id == user_id,
                ArenaExerciseProgress.course_id == course_id,
            )
        )
        total = count_result.scalar() or 0

        if target_index < 0 or target_index >= total:
            raise ValueError("Invalid exercise index")

        # Get target progress
        result = await self.db.execute(
            select(ArenaExerciseProgress).where(
                ArenaExerciseProgress.user_id == user_id,
                ArenaExerciseProgress.course_id == course_id,
                ArenaExerciseProgress.exercise_index == target_index,
            )
        )
        progress = result.scalar_one_or_none()
        if not progress:
            raise ValueError("Progress not found")

        # Check if unlocked
        if not progress.is_unlocked:
            raise ValueError("Exercise is locked")

        # Get exercise
        ex_result = await self.db.execute(
            select(Exercise).where(Exercise.id == progress.exercise_id)
        )
        exercise = ex_result.scalar_one_or_none()

        return {
            "exercise_id": progress.exercise_id,
            "saved_code": (progress.saved_codes or {}).get(progress.current_language, ""),
            "current_language": progress.current_language,
            "is_completed": progress.is_completed,
            "is_correct": progress.is_correct,
            "exercise": exercise,
        }

    async def append_exercises(
        self,
        user_id: str,
        course_id: int,
        difficulty_level: int = 3,
        count: int = 5,
    ) -> list[int]:
        """Append more exercises to the challenge path using adaptive recommendation"""
        # Get current max index
        max_index_result = await self.db.execute(
            select(func.max(ArenaExerciseProgress.exercise_index)).where(
                ArenaExerciseProgress.user_id == user_id,
                ArenaExerciseProgress.course_id == course_id,
            )
        )
        max_index = max_index_result.scalar() or -1

        # Get existing exercise IDs to exclude
        existing_result = await self.db.execute(
            select(ArenaExerciseProgress.exercise_id).where(
                ArenaExerciseProgress.user_id == user_id,
                ArenaExerciseProgress.course_id == course_id,
            )
        )
        existing_ids = list(set(row[0] for row in existing_result.fetchall()))

        # Get user for adaptive recommendation
        user_result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()

        selected = []

        if user:
            # Use adaptive recommendation service for intelligent matching
            adaptive_service = AdaptiveRecommendationService(self.db)
            recommendation = await adaptive_service.get_recommendations(
                user=user,
                limit=count,
                min_difficulty=max(1, difficulty_level - 1),
                max_difficulty=min(8, difficulty_level + 1),
                course_id=course_id,
                learning_path="challenge",
                exclude_ids=existing_ids,
            )

            recommended_ids = [rec["exercise_id"] for rec in recommendation.get("recommendations", [])]

            if recommended_ids:
                result = await self.db.execute(
                    select(Exercise).where(Exercise.id.in_(recommended_ids))
                )
                exercises_map = {ex.id: ex for ex in result.scalars().all()}
                selected = [exercises_map[eid] for eid in recommended_ids if eid in exercises_map]

        # Fallback: traditional random selection if adaptive fails
        if len(selected) < count:
            chapters_result = await self.db.execute(
                select(Chapter.id).where(Chapter.course_id == course_id)
            )
            chapter_ids = [c[0] for c in chapters_result.fetchall()]

            all_exclude = existing_ids + [ex.id for ex in selected]

            exercises_result = await self.db.execute(
                select(Exercise).where(
                    Exercise.chapter_id.in_(chapter_ids),
                    Exercise.difficulty == difficulty_level,
                    ~Exercise.id.in_(all_exclude),
                ).limit(count * 2)
            )
            all_exercises = exercises_result.scalars().all()

            if len(all_exercises) < count - len(selected):
                exercises_result = await self.db.execute(
                    select(Exercise).where(
                        Exercise.chapter_id.in_(chapter_ids),
                        ~Exercise.id.in_(all_exclude),
                    ).limit(count * 2)
                )
                all_exercises = exercises_result.scalars().all()

            remaining = random.sample(
                list(all_exercises),
                min(count - len(selected), len(all_exercises))
            ) if all_exercises else []
            selected.extend(remaining)

        if not selected:
            return []

        # Check if last exercise is completed (for unlocking first new one)
        last_exercise_completed = False
        if max_index >= 0:
            last_result = await self.db.execute(
                select(ArenaExerciseProgress).where(
                    ArenaExerciseProgress.user_id == user_id,
                    ArenaExerciseProgress.course_id == course_id,
                    ArenaExerciseProgress.exercise_index == max_index,
                )
            )
            last_progress = last_result.scalar_one_or_none()
            last_exercise_completed = last_progress.is_completed if last_progress else False

        new_ids = []
        for i, ex in enumerate(selected):
            progress = ArenaExerciseProgress(
                user_id=user_id,
                course_id=course_id,
                exercise_id=ex.id,
                exercise_index=max_index + 1 + i,
                is_unlocked=(i == 0 and (max_index < 0 or last_exercise_completed)),
            )
            self.db.add(progress)
            new_ids.append(ex.id)

        await self.db.commit()
        return new_ids

    async def get_stats(
        self,
        user_id: str,
        course_id: int,
    ) -> dict:
        """Get challenge path statistics"""
        progress_records = await self._get_user_progress(user_id, course_id)

        if not progress_records:
            return {
                "total_exercises": 0,
                "completed_count": 0,
                "correct_count": 0,
                "total_xp": 0,
            }

        completed = sum(1 for p in progress_records if p.is_completed)
        correct = sum(1 for p in progress_records if p.is_correct)

        return {
            "total_exercises": len(progress_records),
            "completed_count": completed,
            "correct_count": correct,
            "total_xp": correct * 10,
        }


def get_challenge_path_service(db: AsyncSession) -> ChallengePathService:
    """Get ChallengePathService instance"""
    return ChallengePathService(db)


# Backward compatibility alias
ArenaInfiniteService = ChallengePathService
get_arena_infinite_service = get_challenge_path_service
