"""Exercise Service - Question Bank and AI Generation"""

from typing import Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.exercise import Exercise
from app.models.chapter import Chapter
from app.services.ai import ai_service
from app.services.wrong_question import wrong_question_service
import logging


class ExerciseService:
    """Service for managing exercise question bank and AI generation"""

    async def get_exercises_by_chapter(
        self,
        db: AsyncSession,
        chapter_id: int,
        limit: int = 50,
    ) -> list[Exercise]:
        """Get verified exercises for a chapter"""
        result = await db.execute(
            select(Exercise)
            .where(
                Exercise.chapter_id == chapter_id,
                Exercise.is_verified,
            )
            .order_by(Exercise.difficulty, Exercise.id)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def generate_exercises(
        self,
        db: AsyncSession,
        chapter_id: int,
        count: int = 5,
        exercise_type: str = "choice",
        difficulty: int = 1,
        topic: Optional[str] = None,
    ) -> dict:
        """Generate exercises using AI"""
        # Get chapter info for context
        chapter = await db.execute(
            select(Chapter).where(Chapter.id == chapter_id)
        )
        chapter = chapter.scalar_one_or_none()
        if not chapter:
            raise ValueError(f"Chapter {chapter_id} not found")

        # Generate exercises using AI service
        generated_exercises = await ai_service.generate_exercises(
            chapter_title=chapter.title,
            chapter_description=chapter.description or "",
            topic=topic,
            count=count,
            exercise_type=exercise_type,
            difficulty=difficulty,
        )

        # Save generated exercises to database
        saved_count = 0
        exercises_data = []
        for ex_data in generated_exercises:
            exercise = Exercise(
                chapter_id=chapter_id,
                source="ai_generated",
                source_id=ex_data.get("source_id"),
                type=exercise_type,
                difficulty=difficulty,
                content=ex_data.get("content", {}),
                solution=ex_data.get("solution"),
                hints=ex_data.get("hints", []),
                is_verified=False,  # AI generated, needs verification
                usage_count=0,
            )
            db.add(exercise)
            exercises_data.append(ex_data)
            saved_count += 1

        await db.commit()

        return {
            "success": True,
            "generated": saved_count,
            "exercises": exercises_data,
            "message": f"Successfully generated {saved_count} exercises",
        }

    async def check_answer(
        self,
        db: AsyncSession,
        user: User,
        exercise: Exercise,
        user_answer: Any,
        course_id: int = 0,
        chapter_id: int = None,
        stage_id: int = None,
    ) -> dict:
        """Check user's answer and return feedback

        Args:
            db: 数据库会话
            user: 用户对象
            exercise: 练习题对象
            user_answer: 用户答案
            course_id: 课程ID（用于错题收集）
            chapter_id: 章节ID（可选）
            stage_id: 关卡ID（可选）
        """
        # Get correct answer from solution
        solution = exercise.solution or {}
        correct_answer = solution.get("answer")

        is_correct = False
        explanation = None

        if exercise.type == "choice":
            # For choice questions, compare indices or values
            if isinstance(user_answer, int):
                is_correct = user_answer == correct_answer
            elif isinstance(user_answer, str):
                is_correct = user_answer == correct_answer
            elif isinstance(user_answer, list):
                is_correct = set(user_answer) == set(correct_answer) if correct_answer else False
            explanation = solution.get("explanation")
        elif exercise.type == "programming":
            # For programming, check via test cases
            # This would need actual code execution
            is_correct = user_answer == correct_answer
            explanation = solution.get("explanation")
        else:
            # fill_blank or other types
            is_correct = str(user_answer).strip().lower() == str(correct_answer).strip().lower()
            explanation = solution.get("explanation")

        # Update exercise usage stats
        exercise.usage_count += 1
        if exercise.correct_rate is None:
            exercise.correct_rate = {"total": 0, "correct": 0}

        exercise.correct_rate["total"] = exercise.correct_rate.get("total", 0) + 1
        if is_correct:
            exercise.correct_rate["correct"] = exercise.correct_rate.get("correct", 0) + 1

        # Calculate XP earned
        xp_earned = 0
        points = 0
        wrong_question_updated = False

        if is_correct:
            # Base XP by difficulty
            base_xp = {1: 5, 2: 10, 3: 15, 4: 20, 5: 25}
            xp_earned = base_xp.get(exercise.difficulty, 5)
            points = xp_earned * 10  # 1 point per XP, times 10

            # Update user XP
            user.xp += xp_earned
            user.total_exercises += 1
            user.correct_exercises += 1

            # Update accuracy rate
            if user.total_exercises > 0:
                user.accuracy_rate = round(
                    user.correct_exercises / user.total_exercises * 100, 1
                )

            # 答对了：检查是否是曾经错过的题目，标记为已解决
            existing_wrong = await wrong_question_service.get_wrong_question_by_exercise(
                db=db,
                user_id=user.id,
                exercise_id=exercise.id,
            )
            if existing_wrong:
                await wrong_question_service.mark_resolved(
                    db=db,
                    user_id=user.id,
                    exercise_id=exercise.id,
                )
                wrong_question_updated = True

            db.add(user)
        else:
            user.total_exercises += 1
            db.add(user)

            # 答错了：收集错题
            if course_id > 0:
                await wrong_question_service.collect_wrong_question(
                    db=db,
                    user_id=user.id,
                    exercise=exercise,
                    user_answer=user_answer,
                    course_id=course_id,
                    chapter_id=chapter_id,
                    stage_id=stage_id,
                )
                wrong_question_updated = True

        db.add(exercise)
        await db.commit()

        return {
            "is_correct": is_correct,
            "correct_answer": correct_answer,
            "explanation": explanation,
            "xp_earned": xp_earned,
            "points": points,
            "wrong_question_updated": wrong_question_updated,
        }

    async def verify_exercise(
        self, db: AsyncSession, exercise_id: int, verified: bool = True
    ) -> Exercise:
        """Mark an exercise as verified (admin)"""
        result = await db.execute(
            select(Exercise).where(Exercise.id == exercise_id)
        )
        exercise = result.scalar_one_or_none()
        if not exercise:
            raise ValueError(f"Exercise {exercise_id} not found")

        exercise.is_verified = verified
        db.add(exercise)
        await db.commit()
        await db.refresh(exercise)
        return exercise


exercise_service = ExerciseService()


logger = logging.getLogger(__name__)