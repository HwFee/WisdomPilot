"""
Learning Path Router

API endpoints for the dual learning path system:
- Mastery Path (精进之路): Chapter-based learning
- Challenge Path (挑战之路): Difficulty-based challenges
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, Field

from app.database import get_db
from app.utils.deps import get_current_user
from app.models.user import User
from app.models.chapter_mastery import ChapterMastery
from app.models.challenge_session import ChallengeSession
from app.models.user_arena import UserArenaProfile
from app.models.arena_exercise_progress import ArenaExerciseProgress
from app.models.course import Course
from app.models.chapter import Chapter
from app.models.exercise import Exercise
from app.services.chapter_mastery import ChapterMasteryService, get_chapter_mastery_service
from app.services.challenge_service import ChallengeService, get_challenge_service
from app.services.leaderboard_service import (
    ArenaLeaderboardService,
    MasteryLeaderboardService,
    get_arena_leaderboard_service,
    get_mastery_leaderboard_service,
)
from app.services.adaptive_recommendation import AdaptiveRecommendationService
from app.services.wrong_question import wrong_question_service
from app.services.arena_infinite import ArenaInfiniteService, get_arena_infinite_service
from app.schemas.exercise import ExerciseRecommendRequest


router = APIRouter(prefix="/api/learning-path", tags=["learning-path"])


# ========== Schemas ==========

class MasteryOverviewResponse(BaseModel):
    """Response for mastery path overview"""
    course_id: int
    total_chapters: int
    mastered_chapters: int
    current_chapter: Optional[int]
    total_mastery_points: float
    avg_mastery: float
    chapters: list[dict]


class ChapterMasteryResponse(BaseModel):
    """Response for chapter mastery details"""
    chapter_id: int
    chapter_title: str
    mastery_score: float
    mastery_level: str
    accuracy_score: float
    consistency_score: float
    depth_score: float
    recency_score: float
    total_exercises: int
    correct_exercises: int
    can_advance: bool
    objectives_status: Optional[dict]


class ChallengeStartRequest(BaseModel):
    """Request to start a challenge"""
    difficulty_level: int = Field(..., ge=1, le=5, description="Difficulty level 1-5")
    question_count: int = Field(default=10, ge=5, le=20, description="Number of questions")


class ChallengeSubmitRequest(BaseModel):
    """Request to submit challenge answers"""
    answers: list[dict]  # [{exercise_id: str, answer: str, is_correct: bool, time_spent: int}]
    total_time: int  # Total time in seconds


class ChallengeSessionResponse(BaseModel):
    """Response for challenge session"""
    session_id: str
    difficulty_level: int
    exercises: list[dict]
    time_limit: int
    score_multiplier: float
    status: str


class ChallengeResultResponse(BaseModel):
    """Response for completed challenge"""
    session_id: str
    correct_answers: int
    total_questions: int
    base_score: float
    time_bonus: float
    streak_bonus: float
    final_score: float
    tier: str
    new_tier: Optional[str]


class ArenaProfileResponse(BaseModel):
    """Response for arena profile"""
    user_id: str
    course_id: int
    total_score: float
    tier: str
    rank: Optional[int]
    total_challenges: int
    wins: int
    losses: int
    highest_difficulty: int
    best_streak: int
    current_streak: int


class LeaderboardResponse(BaseModel):
    """Response for leaderboard"""
    leaderboard_type: str
    course_id: int
    entries: list[dict]
    user_rank: Optional[int]


# ========== Mastery Path Endpoints ==========

@router.get("/mastery/{course_id}/overview", response_model=MasteryOverviewResponse)
async def get_mastery_overview(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's mastery path overview for a course"""
    from app.models.mastery_exercise_progress import MasteryExerciseProgress
    from app.models.chapter_base_question import ChapterBaseQuestion

    # Get all chapters for the course
    chapters_result = await db.execute(
        select(Chapter).where(Chapter.course_id == course_id).order_by(Chapter.order_index)
    )
    chapters = chapters_result.scalars().all()

    if not chapters:
        # Return empty overview instead of error when no chapters
        return MasteryOverviewResponse(
            course_id=course_id,
            total_chapters=0,
            mastered_chapters=0,
            current_chapter=None,
            total_mastery_points=0,
            avg_mastery=0,
            chapters=[],
        )

    # Get user's mastery records (from completed quizzes)
    mastery_result = await db.execute(
        select(ChapterMastery).where(
            ChapterMastery.user_id == current_user.id,
            ChapterMastery.course_id == course_id
        )
    )
    masteries = {m.chapter_id: m for m in mastery_result.scalars().all()}

    # Also get per-question progress for chapters without a ChapterMastery record
    # This ensures partial progress is visible even if the user hasn't completed the full quiz
    exercise_progress_result = await db.execute(
        select(MasteryExerciseProgress).where(
            MasteryExerciseProgress.user_id == current_user.id,
            MasteryExerciseProgress.course_id == course_id,
            MasteryExerciseProgress.question_type == "base",
        )
    )
    exercise_progress_list = exercise_progress_result.scalars().all()

    # Group exercise progress by chapter_id
    chapter_exercise_progress = {}
    for p in exercise_progress_list:
        if p.chapter_id not in chapter_exercise_progress:
            chapter_exercise_progress[p.chapter_id] = []
        chapter_exercise_progress[p.chapter_id].append(p)

    # Get base question counts per chapter (for calculating partial progress)
    chapter_ids = [ch.id for ch in chapters]
    base_questions_result = await db.execute(
        select(
            ChapterBaseQuestion.chapter_id,
            func.count(ChapterBaseQuestion.id)
        ).where(
            ChapterBaseQuestion.chapter_id.in_(chapter_ids),
            ChapterBaseQuestion.is_active == True,
        ).group_by(ChapterBaseQuestion.chapter_id)
    )
    chapter_question_counts = {row[0]: row[1] for row in base_questions_result.fetchall()}

    # Calculate stats
    total_mastery_points = sum(m.mastery_score for m in masteries.values())
    mastered_count = sum(1 for m in masteries.values() if m.mastery_score >= 85)

    # Find current chapter (first unmastered)
    current_chapter = None
    for ch in chapters:
        if ch.id not in masteries or masteries[ch.id].mastery_score < 75:
            current_chapter = ch.order_index
            break

    # Build chapter list with partial progress fallback
    chapter_list = []
    for ch in chapters:
        m = masteries.get(ch.id)
        if m:
            # Use ChapterMastery data (from completed quiz)
            chapter_list.append({
                "chapter_id": ch.id,
                "order_index": ch.order_index,
                "title": ch.title,
                "mastery_score": m.mastery_score,
                "mastery_level": m.mastery_level,
                "can_advance": m.mastery_score >= 75,
            })
        else:
            # Fallback: calculate partial progress from exercise progress
            progress_list = chapter_exercise_progress.get(ch.id, [])
            total_q = chapter_question_counts.get(ch.id, 0)
            if progress_list and total_q > 0:
                completed = sum(1 for p in progress_list if p.is_completed)
                correct = sum(1 for p in progress_list if p.is_correct)
                # Partial mastery score based on completion and accuracy
                partial_score = (correct / total_q) * 100
                partial_level = (
                    "入门" if partial_score < 20 else
                    "学习" if partial_score < 40 else
                    "练习" if partial_score < 60 else
                    "熟练" if partial_score < 80 else
                    "精通"
                )
                total_mastery_points += partial_score
                if partial_score >= 85:
                    mastered_count += 1
                chapter_list.append({
                    "chapter_id": ch.id,
                    "order_index": ch.order_index,
                    "title": ch.title,
                    "mastery_score": round(partial_score, 2),
                    "mastery_level": partial_level,
                    "can_advance": partial_score >= 75,
                })
            else:
                chapter_list.append({
                    "chapter_id": ch.id,
                    "order_index": ch.order_index,
                    "title": ch.title,
                    "mastery_score": 0,
                    "mastery_level": "入门",
                    "can_advance": False,
                })

    # Recalculate avg_mastery with partial progress included
    chapters_with_progress = len(masteries) + len([
        ch_id for ch_id in chapter_exercise_progress
        if ch_id not in masteries and chapter_exercise_progress[ch_id]
    ])
    avg_mastery = total_mastery_points / chapters_with_progress if chapters_with_progress > 0 else 0

    return MasteryOverviewResponse(
        course_id=course_id,
        total_chapters=len(chapters),
        mastered_chapters=mastered_count,
        current_chapter=current_chapter,
        total_mastery_points=round(total_mastery_points, 2),
        avg_mastery=round(avg_mastery, 2),
        chapters=chapter_list,
    )


@router.get("/mastery/{course_id}/chapter/{chapter_id}", response_model=ChapterMasteryResponse)
async def get_chapter_mastery(
    course_id: int,
    chapter_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed mastery info for a specific chapter"""
    # Get chapter
    chapter_result = await db.execute(
        select(Chapter).where(Chapter.id == chapter_id, Chapter.course_id == course_id)
    )
    chapter = chapter_result.scalar_one_or_none()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    # Get mastery record
    mastery_result = await db.execute(
        select(ChapterMastery).where(
            ChapterMastery.user_id == current_user.id,
            ChapterMastery.chapter_id == chapter_id
        )
    )
    mastery = mastery_result.scalar_one_or_none()

    if not mastery:
        # Return default values
        return ChapterMasteryResponse(
            chapter_id=chapter_id,
            chapter_title=chapter.title,
            mastery_score=0,
            mastery_level="入门",
            accuracy_score=0,
            consistency_score=0,
            depth_score=0,
            recency_score=0,
            total_exercises=0,
            correct_exercises=0,
            can_advance=False,
            objectives_status=None,
        )

    service = get_chapter_mastery_service(db)
    can_advance = service.can_advance(mastery.mastery_score)

    return ChapterMasteryResponse(
        chapter_id=chapter_id,
        chapter_title=chapter.title,
        mastery_score=mastery.mastery_score,
        mastery_level=mastery.mastery_level,
        accuracy_score=mastery.accuracy_score,
        consistency_score=mastery.consistency_score,
        depth_score=mastery.depth_score,
        recency_score=mastery.recency_score,
        total_exercises=mastery.total_exercises,
        correct_exercises=mastery.correct_exercises,
        can_advance=can_advance,
        objectives_status=mastery.objectives_status,
    )


@router.post("/mastery/{course_id}/chapter/{chapter_id}/recommend")
async def recommend_mastery_exercises(
    course_id: int,
    chapter_id: int,
    limit: int = Query(default=5, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get recommended exercises for mastery path (chapter-based)"""
    # Get chapter
    chapter_result = await db.execute(
        select(Chapter).where(Chapter.id == chapter_id, Chapter.course_id == course_id)
    )
    chapter = chapter_result.scalar_one_or_none()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    # Use adaptive recommendation with chapter_id and mastery path
    request = ExerciseRecommendRequest(
        course_id=course_id,
        chapter_id=chapter_id,
        learning_path="mastery",
        limit=limit,
    )

    service = AdaptiveRecommendationService(db)
    exercises = await service.recommend_exercises(
        user_id=current_user.id,
        request=request,
    )

    return {
        "chapter_id": chapter_id,
        "chapter_title": chapter.title,
        "learning_path": "mastery",
        "exercises": exercises,
    }


# ========== Challenge Path Endpoints ==========

@router.get("/challenge/{course_id}/profile", response_model=ArenaProfileResponse)
async def get_arena_profile(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's arena profile for a course"""
    profile_result = await db.execute(
        select(UserArenaProfile).where(
            UserArenaProfile.user_id == current_user.id,
            UserArenaProfile.course_id == course_id
        )
    )
    profile = profile_result.scalar_one_or_none()

    if not profile:
        # Create default profile
        profile = UserArenaProfile(
            user_id=current_user.id,
            course_id=course_id,
        )
        db.add(profile)
        await db.commit()
        await db.refresh(profile)

    return ArenaProfileResponse(
        user_id=profile.user_id,
        course_id=profile.course_id,
        total_score=profile.total_score,
        tier=profile.tier,
        rank=profile.rank,
        total_challenges=profile.total_challenges,
        wins=profile.wins,
        losses=profile.losses,
        highest_difficulty=profile.highest_difficulty,
        best_streak=profile.best_streak,
        current_streak=profile.current_streak,
    )


@router.post("/challenge/{course_id}/start", response_model=ChallengeSessionResponse)
async def start_challenge(
    course_id: int,
    request: ChallengeStartRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start a new challenge session"""
    # Get chapters for this course
    chapters_result = await db.execute(
        select(Chapter.id).where(Chapter.course_id == course_id)
    )
    chapter_ids = [c[0] for c in chapters_result.fetchall()]

    if not chapter_ids:
        raise HTTPException(
            status_code=400,
            detail="No chapters available for this course"
        )

    # Get exercises for the difficulty level from these chapters
    exercises_result = await db.execute(
        select(Exercise).where(
            Exercise.chapter_id.in_(chapter_ids),
            Exercise.difficulty == request.difficulty_level
        ).limit(request.question_count * 2)  # Get extra for randomization
    )
    all_exercises = exercises_result.scalars().all()

    if len(all_exercises) < request.question_count:
        # If not enough exercises at exact difficulty, get from all difficulties
        exercises_result = await db.execute(
            select(Exercise).where(
                Exercise.chapter_id.in_(chapter_ids)
            ).limit(request.question_count * 2)
        )
        all_exercises = exercises_result.scalars().all()

    if len(all_exercises) < request.question_count:
        raise HTTPException(
            status_code=400,
            detail=f"Not enough exercises available for this course"
        )

    # DEBUG: First exercise is always matrix multiplication (ID: 32)
    MATRIX_EXERCISE_ID = 32
    matrix_exercise_result = await db.execute(
        select(Exercise).where(Exercise.id == MATRIX_EXERCISE_ID)
    )
    matrix_exercise = matrix_exercise_result.scalar_one_or_none()

    # Randomly select remaining exercises
    import random
    remaining_count = request.question_count - 1
    other_exercises = [ex for ex in all_exercises if ex.id != MATRIX_EXERCISE_ID]

    if len(other_exercises) < remaining_count:
        remaining_count = len(other_exercises)

    selected_others = random.sample(other_exercises, remaining_count) if remaining_count > 0 else []

    # First exercise is matrix, then the rest
    if matrix_exercise:
        selected = [matrix_exercise] + selected_others
    else:
        selected = selected_others[:request.question_count] if selected_others else random.sample(list(all_exercises), min(request.question_count, len(all_exercises)))

    exercise_ids = [ex.id for ex in selected]

    # Create session
    service = get_challenge_service(db)
    session = await service.create_session(
        user_id=current_user.id,
        course_id=course_id,
        difficulty=request.difficulty_level,
        exercise_ids=exercise_ids,
    )

    # Update status to in_progress
    session.status = "in_progress"
    session.started_at = datetime.utcnow()
    await db.commit()

    # Return exercise info with full content (without answers)
    exercise_list = [{
        "id": ex.id,
        "title": ex.content.get("title", "") or (ex.content.get("text", "")[:50] if ex.content.get("text") else f"题目 {ex.id}"),
        "type": ex.type,
        "difficulty": ex.difficulty,
        "knowledge_points": ex.knowledge_points or [],
        "content": {
            "text": ex.content.get("text", ""),
            "title": ex.content.get("title", ""),
            "options": ex.content.get("options", []),
            "code_template": ex.content.get("code_template"),
            "description": ex.content.get("description"),
            "samples": ex.content.get("samples", []),
        },
        "test_cases": ex.test_cases if ex.type == "programming" else None,
    } for ex in selected]

    return ChallengeSessionResponse(
        session_id=session.id,
        difficulty_level=session.difficulty_level,
        exercises=exercise_list,
        time_limit=session.time_limit,
        score_multiplier=session.score_multiplier,
        status=session.status,
    )


@router.post("/challenge/{course_id}/session/{session_id}/submit", response_model=ChallengeResultResponse)
async def submit_challenge(
    course_id: int,
    session_id: str,
    request: ChallengeSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit challenge answers and get results"""
    # Get session
    session_result = await db.execute(
        select(ChallengeSession).where(
            ChallengeSession.id == session_id,
            ChallengeSession.user_id == current_user.id,
            ChallengeSession.course_id == course_id
        )
    )
    session = session_result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status != "in_progress":
        raise HTTPException(status_code=400, detail="Session already completed")

    # Calculate results
    correct_count = sum(1 for a in request.answers if a.get("is_correct", False))
    max_streak = 0
    current_streak = 0
    for a in request.answers:
        if a.get("is_correct", False):
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0

    # Complete session
    service = get_challenge_service(db)
    session = await service.complete_session(
        session_id=session_id,
        correct_answers=correct_count,
        time_spent=request.total_time,
        max_streak=max_streak,
    )

    # Update arena profile
    profile_result = await db.execute(
        select(UserArenaProfile).where(
            UserArenaProfile.user_id == current_user.id,
            UserArenaProfile.course_id == course_id
        )
    )
    profile = profile_result.scalar_one_or_none()

    if not profile:
        profile = UserArenaProfile(
            user_id=current_user.id,
            course_id=course_id,
        )
        db.add(profile)

    # Update stats
    profile.total_score += session.final_score
    profile.total_challenges += 1
    profile.total_time_spent += request.total_time
    profile.last_challenge_at = datetime.utcnow()

    if correct_count / session.total_questions >= 0.8:
        profile.wins += 1
        profile.current_streak += 1
        profile.best_streak = max(profile.best_streak, profile.current_streak)
    elif correct_count / session.total_questions < 0.5:
        profile.losses += 1
        profile.current_streak = 0

    if session.difficulty_level > profile.highest_difficulty:
        profile.highest_difficulty = session.difficulty_level

    # Update tier
    old_tier = profile.tier
    arena_service = get_arena_leaderboard_service(db)
    new_tier = await arena_service.update_user_tier(current_user.id, course_id)

    # Collect wrong questions
    for answer_data in request.answers:
        if not answer_data.get("is_correct", False):
            exercise_id = answer_data.get("exercise_id")
            user_answer = answer_data.get("answer")
            if exercise_id:
                # Get exercise details for knowledge points
                ex_result = await db.execute(
                    select(Exercise).where(Exercise.id == int(exercise_id))
                )
                exercise = ex_result.scalar_one_or_none()
                if exercise:
                    await wrong_question_service.collect_wrong_question(
                        db=db,
                        user_id=current_user.id,
                        exercise=exercise,
                        user_answer=user_answer,
                        course_id=course_id,
                        chapter_id=exercise.chapter_id,
                        challenge_session_id=session_id,
                    )

    await db.commit()

    return ChallengeResultResponse(
        session_id=session.id,
        correct_answers=session.correct_answers,
        total_questions=session.total_questions,
        base_score=session.base_score,
        time_bonus=session.time_bonus,
        streak_bonus=session.streak_bonus,
        final_score=session.final_score,
        tier=old_tier,
        new_tier=new_tier if new_tier != old_tier else None,
    )


# ========== Leaderboard Endpoints ==========

@router.get("/leaderboard/{course_id}/mastery", response_model=LeaderboardResponse)
async def get_mastery_leaderboard(
    course_id: int,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get mastery leaderboard for a course"""
    service = get_mastery_leaderboard_service(db)
    entries = await service.get_leaderboard(course_id, limit, offset)
    user_rank = await service.get_user_rank(current_user.id, course_id)

    return LeaderboardResponse(
        leaderboard_type="mastery",
        course_id=course_id,
        entries=entries,
        user_rank=user_rank,
    )


@router.get("/leaderboard/{course_id}/arena", response_model=LeaderboardResponse)
async def get_arena_leaderboard(
    course_id: int,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get arena leaderboard for a course"""
    service = get_arena_leaderboard_service(db)
    entries = await service.get_leaderboard(course_id, limit, offset)

    # Get user rank
    user_rank = None
    for i, entry in enumerate(entries):
        if entry["user_id"] == current_user.id:
            user_rank = entry["rank"]
            break

    return LeaderboardResponse(
        leaderboard_type="arena",
        course_id=course_id,
        entries=entries,
        user_rank=user_rank,
    )


# ========== Mastery Quiz Endpoints (精进之路测试) ==========

from app.services.mastery_quiz import mastery_quiz_service
from app.schemas.mastery_quiz import (
    MasteryQuizGenerateRequest,
    MasteryQuizGenerateResponse,
    MasteryQuizSubmitRequest,
    MasteryQuizSubmitResponse,
    KnowledgeContentResponse,
)


@router.get("/mastery/{course_id}/chapter/{chapter_id}/knowledge")
async def get_chapter_knowledge(
    course_id: int,
    chapter_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取章节知识点内容（精进之路）

    返回章节的知识点讲解内容，由 AI 生成。
    """
    result = await mastery_quiz_service.get_chapter_knowledge_content(
        db=db,
        chapter_id=chapter_id,
        user_id=current_user.id
    )

    if not result:
        raise HTTPException(status_code=404, detail="章节不存在或知识点生成失败")

    return result


@router.post("/mastery/{course_id}/generate-quiz")
async def generate_mastery_quiz(
    course_id: int,
    request: MasteryQuizGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    生成精进之路测试题

    根据用户画像和章节知识点，由 AI 生成个性化测试题。
    """
    # 确保请求中的 course_id 与路径一致
    request.course_id = course_id

    result = await mastery_quiz_service.generate_quiz(
        db=db,
        user_id=current_user.id,
        request=request
    )

    return result


@router.post("/mastery/{course_id}/submit-quiz")
async def submit_mastery_quiz(
    course_id: int,
    request: MasteryQuizSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    提交精进之路测试结果

    评估用户答案，更新学习进度，返回结果和建议。
    """
    result = await mastery_quiz_service.submit_quiz(
        db=db,
        user_id=current_user.id,
        request=request
    )

    return result


# ========== Chapter Base Question Endpoints (精进之路基础测试) ==========

from app.services.chapter_base_question import chapter_base_question_service
from app.schemas.chapter_base_question import (
    BaseAnswersSubmitRequest,
    BaseAnswersSubmitResponse,
    EnhancedQuizGenerateRequest,
    EnhancedQuizGenerateResponse,
    EnhancedQuizSubmitRequest,
    EnhancedQuizSubmitResponse,
)
from app.services.mastery_progress import mastery_progress_service
from app.schemas.mastery_progress import (
    MasteryExerciseProgressSaveRequest,
    MasteryExerciseProgressResponse,
    MasteryChapterProgressResponse,
    MasteryQuizCompleteRequest,
)


@router.get("/mastery/{course_id}/chapter/{chapter_id}/base-questions")
async def get_chapter_base_questions(
    course_id: int,
    chapter_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取章节基础测试题（精进之路）

    返回该章节的固定基础测试题，用于学习知识点后的基础测试。
    """
    result = await chapter_base_question_service.get_chapter_base_questions(
        db=db,
        chapter_id=chapter_id,
    )
    return result


@router.post("/mastery/{course_id}/chapter/{chapter_id}/submit-base", response_model=BaseAnswersSubmitResponse)
async def submit_base_answers(
    course_id: int,
    chapter_id: int,
    request: BaseAnswersSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    提交基础测试题答案（精进之路）

    评估答案，识别薄弱知识点，返回分析结果。
    同时更新用户的 mastery_xp。
    """
    result = await chapter_base_question_service.submit_base_answers(
        db=db,
        chapter_id=chapter_id,
        request=request,
        user_id=current_user.id,
    )
    return result


@router.post("/mastery/{course_id}/generate-enhanced", response_model=EnhancedQuizGenerateResponse)
async def generate_enhanced_quiz(
    course_id: int,
    request: EnhancedQuizGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    生成强化测试题（精进之路）

    根据基础测试识别的薄弱点，AI 生成个性化强化题目。
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"[API] generate_enhanced_quiz 开始: course_id={course_id}, user={current_user.id[:8]}..., chapter={request.chapter_id}, weak_points={request.weak_points}")

    request.course_id = course_id
    result = await chapter_base_question_service.generate_enhanced_quiz(
        db=db,
        user_id=current_user.id,
        request=request,
    )
    logger.info(f"[API] generate_enhanced_quiz 完成: success={result.success}, questions_count={len(result.questions) if result.questions else 0}")
    return result


@router.post("/mastery/{course_id}/submit-enhanced", response_model=EnhancedQuizSubmitResponse)
async def submit_enhanced_quiz(
    course_id: int,
    request: EnhancedQuizSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    提交强化测试题答案（精进之路）

    评估答案，更新学习进度，返回最终结果。
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"[API] submit_enhanced_quiz 开始: course_id={course_id}, user={current_user.id[:8]}..., session={request.session_id}, answers={len(request.answers)}")

    result = await chapter_base_question_service.submit_enhanced_quiz(
        db=db,
        user_id=current_user.id,
        request=request,
    )
    logger.info(f"[API] submit_enhanced_quiz 完成: correct={result.correct_answers}/{result.total_questions}")
    return result


# ========== Mastery Progress Endpoints (精进之路进度) ==========

@router.post("/mastery/progress/exercise", response_model=MasteryExerciseProgressResponse)
async def save_mastery_exercise_progress(
    request: MasteryExerciseProgressSaveRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    保存精进之路做题进度

    当用户完成一道题（交卷）时调用。
    """
    result = await mastery_progress_service.save_exercise_progress(
        db=db,
        user_id=current_user.id,
        request=request,
    )
    return result


@router.get("/mastery/{course_id}/{chapter_id}/progress", response_model=MasteryChapterProgressResponse)
async def get_mastery_chapter_progress(
    course_id: int,
    chapter_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取精进之路章节进度

    返回用户在某个章节的完成情况。
    """
    result = await mastery_progress_service.get_chapter_progress(
        db=db,
        user_id=current_user.id,
        course_id=course_id,
        chapter_id=chapter_id,
    )
    return result


@router.get("/mastery/{course_id}/{chapter_id}/progress/detail")
async def get_mastery_chapter_detail_progress(
    course_id: int,
    chapter_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取精进之路章节详细进度

    返回用户在某个章节的详细完成情况，包含每道题的进度信息。
    """
    result = await mastery_progress_service.get_chapter_detail_progress(
        db=db,
        user_id=current_user.id,
        course_id=course_id,
        chapter_id=chapter_id,
    )
    return result


@router.post("/mastery/progress/complete-quiz")
async def complete_mastery_quiz(
    request: MasteryQuizCompleteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    完成章节quiz时更新ChapterMastery

    当用户完成整个章节测试后调用，用于更新章节掌握度。
    """
    success = await mastery_progress_service.complete_chapter_quiz(
        db=db,
        user_id=current_user.id,
        request=request,
    )
    return {"success": success, "message": "章节进度已更新" if success else "更新失败"}


@router.get("/mastery/progress/exercise/{exercise_key}")
async def get_mastery_progress_by_key(
    exercise_key: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    根据exercise_key获取做题进度（用于错题本跳转定位）

    返回进度信息，包括题目ID、章节ID等。
    """
    progress = await mastery_progress_service.get_progress_by_exercise_key(
        db=db,
        user_id=current_user.id,
        exercise_key=exercise_key,
    )
    if not progress:
        return {"found": False, "message": "未找到进度记录"}

    return {
        "found": True,
        "progress": {
            "course_id": progress.course_id,
            "chapter_id": progress.chapter_id,
            "question_id": progress.question_id,
            "question_index": progress.question_index,
            "is_completed": progress.is_completed,
            "is_correct": progress.is_correct,
        }
    }


# ========== Arena Infinite Mode Endpoints ==========

class InfiniteSessionStartRequest(BaseModel):
    """Request to start infinite mode session"""
    difficulty_level: int = Field(default=3, ge=1, le=5)
    initial_count: int = Field(default=5, ge=5, le=50)


class InfiniteProgressResponse(BaseModel):
    """Response for infinite mode progress"""
    session_id: str
    current_index: int
    total_exercises: int
    exercises: list[dict]
    correct_count: int
    completed_count: int
    total_stars_earned: int


class SubmitExerciseRequest(BaseModel):
    """Request to submit exercise answer"""
    exercise_id: int
    code: str
    language: str
    test_results: list[dict]


class SubmitExerciseResponse(BaseModel):
    """Response for exercise submission"""
    is_correct: bool
    test_results: list[dict]
    stars_earned: int
    next_unlocked: bool
    added_to_wrong_book: bool
    tier_changed: bool
    new_tier: str | None
    new_sub_tier: int | None
    new_stars: int
    promoted: bool
    demoted: bool
    first_time_correct: bool
    first_time_wrong: bool


class SaveCodeRequest(BaseModel):
    """Request to save code"""
    exercise_id: int
    code: str
    language: str


class SwitchExerciseRequest(BaseModel):
    """Request to switch to a different exercise"""
    target_index: int


class AppendExercisesRequest(BaseModel):
    """Request to append more exercises"""
    count: int = Field(default=5, ge=1, le=20)


class ExitSaveRequest(BaseModel):
    """Request to save on exit"""
    current_exercise_id: int
    current_code: str
    current_language: str


# ========================================
# Challenge Path APIs (No Session Concept)
# ========================================

class ChallengePathResponse(BaseModel):
    """Response for challenge path"""
    exercises: list[dict]
    total_exercises: int
    completed_count: int
    correct_count: int
    current_index: int


@router.post("/challenge/{course_id}/infinite/start", response_model=ChallengeSessionResponse)
async def start_infinite_session(
    course_id: int,
    request: InfiniteSessionStartRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start or get challenge path for a course (no session concept)"""
    service = get_arena_infinite_service(db)

    try:
        exercises, is_new = await service.get_or_create_challenge_path(
            user_id=current_user.id,
            course_id=course_id,
            difficulty_level=request.difficulty_level,
            initial_count=request.initial_count,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    exercise_list = [{
        "id": ex.id,
        "title": ex.content.get("title", "") or (ex.content.get("text", "")[:50] if ex.content.get("text") else f"题目 {i+1}"),
        "type": ex.type,
        "difficulty": ex.difficulty,
        "knowledge_points": ex.knowledge_points or [],
        "content": {
            "text": ex.content.get("text", ""),
            "title": ex.content.get("title", ""),
            "options": ex.content.get("options", []),
            "code_template": ex.content.get("code_template"),
            "description": ex.content.get("description"),
            "samples": ex.content.get("samples", []),
        },
        "test_cases": ex.test_cases if ex.type == "programming" else None,
    } for i, ex in enumerate(exercises)]

    # Use course_id as pseudo session_id for backward compatibility
    pseudo_session_id = f"challenge-{course_id}"

    return ChallengeSessionResponse(
        session_id=pseudo_session_id,
        difficulty_level=request.difficulty_level,
        exercises=exercise_list,
        time_limit=0,
        score_multiplier=1.0,
        status="in_progress",
    )


@router.get("/challenge/{course_id}/progress")
async def get_challenge_path_progress(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get challenge path progress (no session_id needed)"""
    service = get_arena_infinite_service(db)

    progress = await service.get_progress(
        user_id=current_user.id,
        course_id=course_id,
    )

    return progress


@router.post("/challenge/{course_id}/submit")
async def submit_challenge_exercise(
    course_id: int,
    request: SubmitExerciseRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit exercise answer in challenge path"""
    service = get_arena_infinite_service(db)

    try:
        result = await service.submit_exercise(
            user_id=current_user.id,
            course_id=course_id,
            exercise_id=request.exercise_id,
            code=request.code,
            language=request.language,
            test_results=request.test_results,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return result


@router.post("/challenge/{course_id}/save-code")
async def save_challenge_code(
    course_id: int,
    request: SaveCodeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Save code for an exercise"""
    service = get_arena_infinite_service(db)

    success = await service.save_code(
        user_id=current_user.id,
        course_id=course_id,
        exercise_id=request.exercise_id,
        code=request.code,
        language=request.language,
    )

    return {"success": success}


@router.post("/challenge/{course_id}/switch")
async def switch_challenge_exercise(
    course_id: int,
    request: SwitchExerciseRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Switch to a different exercise by index"""
    service = get_arena_infinite_service(db)

    try:
        result = await service.switch_exercise(
            user_id=current_user.id,
            course_id=course_id,
            target_index=request.target_index,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    exercise = result.pop("exercise", None)
    if exercise:
        result["exercise"] = {
            "id": exercise.id,
            "title": exercise.content.get("title", ""),
            "type": exercise.type,
            "difficulty": exercise.difficulty,
            "knowledge_points": exercise.knowledge_points or [],
            "content": {
                "text": exercise.content.get("text", ""),
                "title": exercise.content.get("title", ""),
                "options": exercise.content.get("options", []),
                "code_template": exercise.content.get("code_template"),
                "description": exercise.content.get("description"),
                "samples": exercise.content.get("samples", []),
            },
            "test_cases": exercise.test_cases if exercise.type == "programming" else None,
        }

    return result


@router.post("/challenge/{course_id}/append")
async def append_challenge_exercises(
    course_id: int,
    request: AppendExercisesRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Append more exercises to challenge path"""
    service = get_arena_infinite_service(db)

    try:
        new_ids = await service.append_exercises(
            user_id=current_user.id,
            course_id=course_id,
            count=request.count,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"new_exercise_ids": new_ids, "count": len(new_ids)}


@router.post("/challenge/{course_id}/exit")
async def exit_challenge_path(
    course_id: int,
    request: ExitSaveRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Save progress and exit challenge path"""
    service = get_arena_infinite_service(db)

    success = await service.save_code(
        user_id=current_user.id,
        course_id=course_id,
        exercise_id=request.current_exercise_id,
        code=request.current_code,
        language=request.current_language,
    )

    return {"success": success, "message": "Progress saved"}


@router.get("/challenge/{course_id}/exercise/{exercise_id}")
async def get_challenge_exercise(
    course_id: int,
    exercise_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get specific exercise info for wrong question book / favorites navigation"""
    service = get_arena_infinite_service(db)

    result = await service.get_exercise_by_id(
        user_id=current_user.id,
        course_id=course_id,
        exercise_id=exercise_id,
    )

    if not result:
        raise HTTPException(status_code=404, detail="Exercise not found in challenge path")

    # Get all progress to find index
    progress = await service.get_progress(current_user.id, course_id)

    return {
        "exercise": result.get("exercise"),
        "exercise_index": result["exercise_index"],
        "is_unlocked": result["is_unlocked"],
        "is_completed": result["is_completed"],
        "is_correct": result["is_correct"],
        "saved_code": result["saved_code"],
        "current_language": result["current_language"],
        "total_exercises": progress["total_exercises"],
    }


# ========================================
# Legacy APIs (for backward compatibility)
# ========================================

@router.get("/challenge/{course_id}/infinite/{session_id}/progress", response_model=InfiniteProgressResponse)
async def get_infinite_progress_legacy(
    course_id: int,
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Legacy API - redirects to new progress endpoint"""
    service = get_arena_infinite_service(db)
    progress = await service.get_progress(
        user_id=current_user.id,
        course_id=course_id,
    )
    progress["session_id"] = session_id
    return InfiniteProgressResponse(**progress)


@router.post("/challenge/{course_id}/infinite/{session_id}/submit", response_model=SubmitExerciseResponse)
async def submit_infinite_exercise_legacy(
    course_id: int,
    session_id: str,
    request: SubmitExerciseRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Legacy API - redirects to new submit endpoint"""
    return await submit_challenge_exercise(course_id, request, current_user, db)


@router.post("/challenge/{course_id}/infinite/{session_id}/save-code")
async def save_infinite_code_legacy(
    course_id: int,
    session_id: str,
    request: SaveCodeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Legacy API - redirects to new save-code endpoint"""
    return await save_challenge_code(course_id, request, current_user, db)


@router.post("/challenge/{course_id}/infinite/{session_id}/switch")
async def switch_infinite_exercise_legacy(
    course_id: int,
    session_id: str,
    request: SwitchExerciseRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Legacy API - redirects to new switch endpoint"""
    return await switch_challenge_exercise(course_id, request, current_user, db)


@router.post("/challenge/{course_id}/infinite/{session_id}/append")
async def append_infinite_exercises_legacy(
    course_id: int,
    session_id: str,
    request: AppendExercisesRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Legacy API - redirects to new append endpoint"""
    return await append_challenge_exercises(course_id, request, current_user, db)


@router.post("/challenge/{course_id}/infinite/{session_id}/exit")
async def exit_infinite_session_legacy(
    course_id: int,
    session_id: str,
    request: ExitSaveRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Legacy API - redirects to new exit endpoint"""
    return await exit_challenge_path(course_id, request, current_user, db)


class RecentArenaExercise(BaseModel):
    """最近挑战之路练习"""
    exercise_id: int
    title: str
    is_correct: bool
    difficulty: int


@router.get("/challenge/{course_id}/recent", response_model=list[RecentArenaExercise])
async def get_recent_arena_exercises(
    course_id: int,
    limit: int = Query(default=3, ge=1, le=10),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取挑战之路最近练习的题目（含正确情况）"""
    # 查询最近的 arena_exercise_progress，按最后尝试时间倒序
    result = await db.execute(
        select(ArenaExerciseProgress, Exercise)
        .join(Exercise, ArenaExerciseProgress.exercise_id == Exercise.id)
        .where(
            ArenaExerciseProgress.user_id == current_user.id,
            ArenaExerciseProgress.course_id == course_id,
            ArenaExerciseProgress.is_completed == True,  # 只取已提交的
        )
        .order_by(ArenaExerciseProgress.last_attempt_at.desc())
        .limit(limit)
    )
    rows = result.all()

    exercises = []
    for progress, exercise in rows:
        # 获取标题
        title = ""
        if exercise.content:
            title = exercise.content.get("title", "") or exercise.content.get("text", "")[:30] or f"题目 {exercise.id}"
        else:
            title = f"题目 {exercise.id}"

        exercises.append(RecentArenaExercise(
            exercise_id=exercise.id,
            title=title,
            is_correct=progress.is_correct,
            difficulty=exercise.difficulty,
        ))

    return exercises


@router.get("/challenge/{course_id}/active-session")
async def get_active_challenge_session(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取用户某门课的挑战之路信息（用于错题本跳转）

    由于移除了会话概念，现在直接返回课程维度的题目信息
    """
    service = get_arena_infinite_service(db)

    # Get all progress for this course
    progress = await service.get_progress(
        user_id=current_user.id,
        course_id=course_id,
    )

    if not progress["exercises"]:
        return {"session": None, "exercise_map": {}, "message": "No challenge path found"}

    # Build exercise map
    exercise_map = {
        ex["exercise_id"]: {
            "exercise_index": ex["exercise_index"],
            "is_completed": ex["is_completed"],
            "is_correct": ex["is_correct"],
            "is_unlocked": ex["is_unlocked"],
        }
        for ex in progress["exercises"]
    }

    # Return pseudo session for backward compatibility
    pseudo_session_id = f"challenge-{course_id}"

    return {
        "session": {
            "id": pseudo_session_id,
            "course_id": course_id,
            "status": "in_progress",
            "current_index": progress["current_index"],
            "total_exercises": progress["total_exercises"],
            "exercise_ids": [ex["exercise_id"] for ex in progress["exercises"]],
        },
        "exercise_map": exercise_map,
    }
