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

    # Get user's mastery records
    mastery_result = await db.execute(
        select(ChapterMastery).where(
            ChapterMastery.user_id == current_user.id,
            ChapterMastery.course_id == course_id
        )
    )
    masteries = {m.chapter_id: m for m in mastery_result.scalars().all()}

    # Calculate stats
    total_mastery_points = sum(m.mastery_score for m in masteries.values())
    mastered_count = sum(1 for m in masteries.values() if m.mastery_score >= 85)

    # Find current chapter (first unmastered)
    current_chapter = None
    for ch in chapters:
        if ch.id not in masteries or masteries[ch.id].mastery_score < 75:
            current_chapter = ch.order_index
            break

    # Build chapter list
    chapter_list = []
    for ch in chapters:
        m = masteries.get(ch.id)
        chapter_list.append({
            "chapter_id": ch.id,
            "order_index": ch.order_index,
            "title": ch.title,
            "mastery_score": m.mastery_score if m else 0,
            "mastery_level": m.mastery_level if m else "入门",
            "can_advance": m.mastery_score >= 75 if m else False,
        })

    avg_mastery = total_mastery_points / len(masteries) if masteries else 0

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

    # Randomly select exercises
    import random
    selected = random.sample(list(all_exercises), min(request.question_count, len(all_exercises)))
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

    # Return exercise info (without answers)
    exercise_list = [{
        "id": ex.id,
        "title": ex.title,
        "difficulty": ex.difficulty,
        "knowledge_points": ex.knowledge_points or [],
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
