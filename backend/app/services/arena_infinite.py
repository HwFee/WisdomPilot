"""
Arena Infinite Mode Service

Service for managing Arena infinite mode:
- Session management
- Progress tracking
- Code persistence
- Wrong question collection
"""

import random
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.models.arena_exercise_progress import ArenaExerciseProgress
from app.models.challenge_session import ChallengeSession
from app.models.exercise import Exercise
from app.models.chapter import Chapter
from app.models.user_weak_point import UserWeakPoint
from app.services.wrong_question import wrong_question_service


class ArenaInfiniteService:
    """Service for Arena infinite mode operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def start_infinite_session(
        self,
        user_id: str,
        course_id: int,
        difficulty_level: int = 3,
        initial_count: int = 10,
    ) -> tuple[ChallengeSession, list[Exercise]]:
        """Start a new infinite mode session"""
        # Get chapters for this course
        chapters_result = await self.db.execute(
            select(Chapter.id).where(Chapter.course_id == course_id)
        )
        chapter_ids = [c[0] for c in chapters_result.fetchall()]

        if not chapter_ids:
            raise ValueError("No chapters available for this course")

        # Get exercises based on difficulty
        exercises_result = await self.db.execute(
            select(Exercise).where(
                Exercise.chapter_id.in_(chapter_ids),
                Exercise.difficulty == difficulty_level
            ).limit(initial_count * 3)
        )
        all_exercises = exercises_result.scalars().all()

        if len(all_exercises) < initial_count:
            # Get from all difficulties if not enough
            exercises_result = await self.db.execute(
                select(Exercise).where(
                    Exercise.chapter_id.in_(chapter_ids)
                ).limit(initial_count * 3)
            )
            all_exercises = exercises_result.scalars().all()

        if len(all_exercises) < initial_count:
            raise ValueError("Not enough exercises available")

        # Randomly select exercises
        selected = random.sample(list(all_exercises), initial_count)
        exercise_ids = [ex.id for ex in selected]

        # Create session
        session = ChallengeSession(
            user_id=user_id,
            course_id=course_id,
            difficulty_level=difficulty_level,
            exercise_ids=exercise_ids,
            time_limit=0,  # No time limit for infinite mode
            score_multiplier=1.0 + (difficulty_level - 3) * 0.1,
            session_type="infinite",
            current_index=0,
            status="in_progress",
            started_at=datetime.utcnow(),
        )
        self.db.add(session)
        await self.db.flush()

        # Create progress records for each exercise
        for i, ex_id in enumerate(exercise_ids):
            progress = ArenaExerciseProgress(
                user_id=user_id,
                course_id=course_id,
                session_id=session.id,
                exercise_id=ex_id,
                exercise_index=i,
                is_unlocked=(i == 0),  # Only first exercise is unlocked
            )
            self.db.add(progress)

        await self.db.commit()
        await self.db.refresh(session)

        return session, selected

    async def get_progress(
        self,
        user_id: str,
        session_id: str,
    ) -> dict:
        """Get current progress for infinite mode session"""
        # Get session
        session_result = await self.db.execute(
            select(ChallengeSession).where(
                ChallengeSession.id == session_id,
                ChallengeSession.user_id == user_id,
            )
        )
        session = session_result.scalar_one_or_none()
        if not session:
            raise ValueError("Session not found")

        # Get all progress records
        progress_result = await self.db.execute(
            select(ArenaExerciseProgress).where(
                ArenaExerciseProgress.session_id == session_id
            ).order_by(ArenaExerciseProgress.exercise_index)
        )
        progress_records = progress_result.scalars().all()

        # Get exercises
        exercise_ids = session.exercise_ids
        exercises_result = await self.db.execute(
            select(Exercise).where(Exercise.id.in_(exercise_ids))
        )
        exercises = {ex.id: ex for ex in exercises_result.scalars().all()}

        # Build progress list
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
                    "saved_code": p.saved_codes.get(p.current_language, ""),
                    "current_language": p.current_language,
                    "title": ex.content.get("title", f"题目 {p.exercise_index + 1}"),
                    "difficulty": ex.difficulty,
                })

        # Calculate stats
        correct_count = sum(1 for p in progress_records if p.is_correct)
        completed_count = sum(1 for p in progress_records if p.is_completed)

        return {
            "session_id": session.id,
            "current_index": session.current_index,
            "total_exercises": len(exercise_ids),
            "exercises": progress_list,
            "correct_count": correct_count,
            "completed_count": completed_count,
            "total_xp_earned": correct_count * 10,
        }

    async def submit_exercise(
        self,
        user_id: str,
        session_id: str,
        exercise_id: int,
        code: str,
        language: str,
        test_results: list[dict],
    ) -> dict:
        """Submit exercise answer and update progress"""
        # Get progress record
        progress_result = await self.db.execute(
            select(ArenaExerciseProgress).where(
                ArenaExerciseProgress.session_id == session_id,
                ArenaExerciseProgress.exercise_id == exercise_id,
                ArenaExerciseProgress.user_id == user_id,
            )
        )
        progress = progress_result.scalar_one_or_none()
        if not progress:
            raise ValueError("Progress record not found")

        # Get session
        session_result = await self.db.execute(
            select(ChallengeSession).where(ChallengeSession.id == session_id)
        )
        session = session_result.scalar_one_or_none()
        if not session:
            raise ValueError("Session not found")

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

        # Update session stats
        if all_passed:
            session.correct_answers += 1
        session.total_questions = max(session.total_questions, progress.exercise_index + 1)

        # Collect wrong question if incorrect
        added_to_wrong_book = False
        if not all_passed:
            exercise_result = await self.db.execute(
                select(Exercise).where(Exercise.id == exercise_id)
            )
            exercise = exercise_result.scalar_one_or_none()
            if exercise:
                await wrong_question_service.collect_wrong_question(
                    db=self.db,
                    user_id=user_id,
                    exercise=exercise,
                    user_answer=code,
                    course_id=progress.course_id,
                    chapter_id=exercise.chapter_id,
                    challenge_session_id=session_id,
                )
                added_to_wrong_book = True

        # Unlock next exercise
        next_unlocked = False
        if progress.exercise_index < len(session.exercise_ids) - 1:
            next_progress_result = await self.db.execute(
                select(ArenaExerciseProgress).where(
                    ArenaExerciseProgress.session_id == session_id,
                    ArenaExerciseProgress.exercise_index == progress.exercise_index + 1,
                )
            )
            next_progress = next_progress_result.scalar_one_or_none()
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
        session_id: str,
        exercise_id: int,
        code: str,
        language: str,
    ) -> None:
        """Save code for a specific language"""
        progress_result = await self.db.execute(
            select(ArenaExerciseProgress).where(
                ArenaExerciseProgress.session_id == session_id,
                ArenaExerciseProgress.exercise_id == exercise_id,
                ArenaExerciseProgress.user_id == user_id,
            )
        )
        progress = progress_result.scalar_one_or_none()
        if not progress:
            return

        saved_codes = progress.saved_codes or {}
        saved_codes[language] = code
        progress.saved_codes = saved_codes
        progress.current_language = language

        await self.db.commit()

    async def switch_exercise(
        self,
        user_id: str,
        session_id: str,
        target_index: int,
    ) -> dict:
        """Switch to a different exercise"""
        session_result = await self.db.execute(
            select(ChallengeSession).where(
                ChallengeSession.id == session_id,
                ChallengeSession.user_id == user_id,
            )
        )
        session = session_result.scalar_one_or_none()
        if not session:
            raise ValueError("Session not found")

        if target_index < 0 or target_index >= len(session.exercise_ids):
            raise ValueError("Invalid exercise index")

        # Get target progress
        progress_result = await self.db.execute(
            select(ArenaExerciseProgress).where(
                ArenaExerciseProgress.session_id == session_id,
                ArenaExerciseProgress.exercise_index == target_index,
            )
        )
        progress = progress_result.scalar_one_or_none()
        if not progress:
            raise ValueError("Progress not found")

        # Check if unlocked
        if not progress.is_unlocked:
            raise ValueError("Exercise is locked")

        # Update session current index
        session.current_index = target_index
        await self.db.commit()

        # Get exercise
        exercise_result = await self.db.execute(
            select(Exercise).where(Exercise.id == progress.exercise_id)
        )
        exercise = exercise_result.scalar_one_or_none()

        return {
            "exercise_id": progress.exercise_id,
            "saved_code": progress.saved_codes.get(progress.current_language, ""),
            "current_language": progress.current_language,
            "is_completed": progress.is_completed,
            "is_correct": progress.is_correct,
            "exercise": exercise,
        }

    async def append_exercises(
        self,
        user_id: str,
        session_id: str,
        count: int = 5,
    ) -> list[int]:
        """Append more exercises to the session"""
        session_result = await self.db.execute(
            select(ChallengeSession).where(
                ChallengeSession.id == session_id,
                ChallengeSession.user_id == user_id,
            )
        )
        session = session_result.scalar_one_or_none()
        if not session:
            raise ValueError("Session not found")

        # Get chapters
        chapters_result = await self.db.execute(
            select(Chapter.id).where(Chapter.course_id == session.course_id)
        )
        chapter_ids = [c[0] for c in chapters_result.fetchall()]

        # Get existing exercise IDs
        existing_ids = set(session.exercise_ids)

        # Get new exercises
        exercises_result = await self.db.execute(
            select(Exercise).where(
                Exercise.chapter_id.in_(chapter_ids),
                Exercise.difficulty == session.difficulty_level,
                ~Exercise.id.in_(existing_ids),
            ).limit(count * 2)
        )
        all_exercises = exercises_result.scalars().all()

        if len(all_exercises) < count:
            # Get from all difficulties
            exercises_result = await self.db.execute(
                select(Exercise).where(
                    Exercise.chapter_id.in_(chapter_ids),
                    ~Exercise.id.in_(existing_ids),
                ).limit(count * 2)
            )
            all_exercises = exercises_result.scalars().all()

        if not all_exercises:
            return []

        selected = random.sample(list(all_exercises), min(count, len(all_exercises)))
        new_ids = [ex.id for ex in selected]

        # Update session
        session.exercise_ids = session.exercise_ids + new_ids

        # Create progress records for new exercises
        start_index = len(session.exercise_ids) - len(new_ids)
        for i, ex_id in enumerate(new_ids):
            progress = ArenaExerciseProgress(
                user_id=user_id,
                course_id=session.course_id,
                session_id=session_id,
                exercise_id=ex_id,
                exercise_index=start_index + i,
                is_unlocked=False,
            )
            self.db.add(progress)

        await self.db.commit()

        return new_ids

    async def save_on_exit(
        self,
        user_id: str,
        session_id: str,
        current_exercise_id: int,
        current_code: str,
        current_language: str,
    ) -> None:
        """Save progress when user exits"""
        await self.save_code(
            user_id=user_id,
            session_id=session_id,
            exercise_id=current_exercise_id,
            code=current_code,
            language=current_language,
        )

        # Mark session as abandoned
        session_result = await self.db.execute(
            select(ChallengeSession).where(ChallengeSession.id == session_id)
        )
        session = session_result.scalar_one_or_none()
        if session:
            session.status = "abandoned"
            session.completed_at = datetime.utcnow()
            await self.db.commit()


def get_arena_infinite_service(db: AsyncSession) -> ArenaInfiniteService:
    """Get ArenaInfiniteService instance"""
    return ArenaInfiniteService(db)
