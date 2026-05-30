"""Review API Router - 复习系统路由"""

from typing import Annotated, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.database import get_db
from app.models.user import User
from app.models.exercise import Exercise
from app.models.user_weak_point import UserWeakPoint
from app.models.spaced_repetition import SpacedRepetition
from app.services.wrong_question import wrong_question_service
from app.schemas.review import (
    ReviewQueueResponse,
    ReviewQueueItem,
    SpacedRepetitionResponse,
    CompleteReviewRequest,
    CompleteReviewResponse,
    WeakPointListResponse,
    WeakPointResponse,
    TargetPracticeRequest,
    TargetPracticeResponse,
    ReviewStatsResponse,
    WrongQuestionListResponse,
    WrongQuestionResponse,
    WeakPointAnalysisResponse,
    KnowledgePointAnalysis,
    EnhancedTargetPracticeRequest,
    EnhancedTargetPracticeResponse,
    ReviewReminderResponse,
    CollectWrongQuestionRequest,
    CollectWrongQuestionResponse,
)

logger = logging.getLogger(__name__)

# Helper to ensure datetime is timezone-aware (for comparing with utc_now())
def _make_aware(dt):
    """Convert naive datetime to UTC-aware datetime"""
    from datetime import timezone
    if dt is None:
        return None
    if dt.tzinfo is None:
        # Assume naive datetime is UTC
        return dt.replace(tzinfo=timezone.utc)
    return dt

router = APIRouter(prefix="/api/review", tags=["review"])

db_dependency = Annotated[AsyncSession, Depends(get_db)]

# Import the actual dependency function
from app.utils.deps import get_current_active_user as _get_current_active_user

auth_dependency = Annotated[User, Depends(_get_current_active_user)]


@router.get("/queue", response_model=ReviewQueueResponse)
async def get_review_queue(
    db: db_dependency,
    user: auth_dependency,
    limit: int = 20
):
    """
    Get the review queue for the current user.

    Returns exercises due for review, prioritized by:
    1. Overdue items
    2. Weak point priority
    3. Difficulty
    """
    from app.utils.time import utc_now

    now = utc_now()

    # Get all repetitions for this user
    all_result = await db.execute(
        select(SpacedRepetition).where(SpacedRepetition.user_id == user.id)
    )
    all_repetitions = all_result.scalars().all()

    # Filter due items (timezone-aware comparison)
    due_repetitions = [r for r in all_repetitions if _make_aware(r.next_review_at) <= now]
    due_repetitions.sort(key=lambda r: r.next_review_at)
    due_repetitions = due_repetitions[:limit]

    # Get exercise details
    exercise_ids = [r.exercise_id for r in due_repetitions]
    exercises = {}
    if exercise_ids:  # 只有在有 ID 时才查询，避免空列表查询错误
        exercises_result = await db.execute(
            select(Exercise).where(Exercise.id.in_(exercise_ids))
        )
        exercises = {e.id: e for e in exercises_result.scalars().all()}

    # Get weak points for priority calculation
    weak_result = await db.execute(
        select(UserWeakPoint).where(UserWeakPoint.user_id == user.id)
    )
    weak_points = {wp.knowledge_point: wp for wp in weak_result.scalars().all()}

    # Build queue items
    items = []
    for rep in due_repetitions:
        exercise = exercises.get(rep.exercise_id)
        if not exercise:
            continue

        # Calculate priority
        priority = 0.0
        # Overdue factor
        days_overdue = (now - _make_aware(rep.next_review_at)).days
        priority += days_overdue * 0.5
        # Weak point factor
        for kp in exercise.knowledge_points:
            if kp in weak_points:
                priority += weak_points[kp].weakness_score * 2

        items.append(ReviewQueueItem(
            repetition=SpacedRepetitionResponse.model_validate(rep),
            exercise_id=exercise.id,
            exercise_type=exercise.type,
            exercise_difficulty=exercise.difficulty,
            knowledge_points=exercise.knowledge_points,
            stage_id=rep.stage_id,
            priority=priority
        ))

    # Sort by priority (higher first)
    items.sort(key=lambda x: x.priority, reverse=True)

    # Get total counts
    total_scheduled = len(all_repetitions)
    total_due = len([r for r in all_repetitions if _make_aware(r.next_review_at) <= now])

    return ReviewQueueResponse(
        items=items,
        total_due=total_due,
        total_scheduled=total_scheduled
    )


@router.post("/complete/{exercise_id}", response_model=CompleteReviewResponse)
async def complete_review(
    exercise_id: int,
    request: CompleteReviewRequest,
    db: db_dependency,
    user: auth_dependency
):
    """
    Complete a review for an exercise.

    Updates spaced repetition schedule and weak point tracking.
    """

    # Get repetition record
    result = await db.execute(
        select(SpacedRepetition).where(
            SpacedRepetition.user_id == user.id,
            SpacedRepetition.exercise_id == exercise_id
        )
    )
    repetition = result.scalar_one_or_none()

    if not repetition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repetition record not found"
        )

    # Update spaced repetition
    repetition.calculate_next_review(request.quality)

    # Get exercise for knowledge points
    exercise_result = await db.execute(
        select(Exercise).where(Exercise.id == exercise_id)
    )
    exercise = exercise_result.scalar_one_or_none()

    weak_point_updated = False
    mastery_change = 0

    if exercise:
        # Update weak points
        for kp in exercise.knowledge_points:
            wp_result = await db.execute(
                select(UserWeakPoint).where(
                    UserWeakPoint.user_id == user.id,
                    UserWeakPoint.course_id == exercise.chapter.course_id
                    if hasattr(exercise, 'chapter') and exercise.chapter else 0,
                    UserWeakPoint.knowledge_point == kp
                )
            )
            weak_point = wp_result.scalar_one_or_none()

            if weak_point:
                old_mastery = weak_point.mastery_level
                weak_point.record_review(request.success)
                weak_point_updated = True
                mastery_change += weak_point.mastery_level - old_mastery

    await db.flush()

    return CompleteReviewResponse(
        repetition=SpacedRepetitionResponse.model_validate(repetition),
        weak_point_updated=weak_point_updated,
        mastery_change=mastery_change,
        message="Review completed successfully"
    )


@router.get("/weak-points", response_model=WeakPointListResponse)
async def get_weak_points(
    db: db_dependency,
    user: auth_dependency,
    course_id: int = None,
    limit: int = 20
):
    """
    Get list of user's weak knowledge points.

    Optionally filtered by course.
    """
    query = select(UserWeakPoint).where(UserWeakPoint.user_id == user.id)

    if course_id:
        query = query.where(UserWeakPoint.course_id == course_id)

    query = query.order_by(UserWeakPoint.mastery_level, UserWeakPoint.error_count.desc()).limit(limit)

    result = await db.execute(query)
    weak_points = result.scalars().all()

    return WeakPointListResponse(
        weak_points=[WeakPointResponse.model_validate(wp) for wp in weak_points],
        total=len(weak_points)
    )


@router.post("/weak-points/target", response_model=TargetPracticeResponse)
async def target_weak_points(
    request: TargetPracticeRequest,
    db: db_dependency,
    user: auth_dependency
):
    """
    Get exercises for targeted practice on weak points.

    Returns exercises that target the specified weak knowledge points.
    """
    # Get weak points
    query = select(UserWeakPoint).where(UserWeakPoint.user_id == user.id)

    if request.course_id:
        query = query.where(UserWeakPoint.course_id == request.course_id)

    if request.knowledge_points:
        query = query.where(UserWeakPoint.knowledge_point.in_(request.knowledge_points))

    query = query.order_by(UserWeakPoint.mastery_level).limit(10)

    result = await db.execute(query)
    weak_points = result.scalars().all()

    if not weak_points:
        return TargetPracticeResponse(
            exercises=[],
            weak_points=[],
            total=0
        )

    # Find exercises targeting these knowledge points
    kp_list = [wp.knowledge_point for wp in weak_points]

    # Use JSON query to find exercises with matching knowledge points
    exercise_result = await db.execute(
        select(Exercise).limit(request.limit)
    )
    all_exercises = exercise_result.scalars().all()

    # Filter by knowledge points (SQLite JSON query is limited, filter in Python)
    exercises = []
    for ex in all_exercises:
        if any(kp in ex.knowledge_points for kp in kp_list):
            exercises.append({
                "id": ex.id,
                "type": ex.type,
                "difficulty": ex.difficulty,
                "content": ex.content,
                "knowledge_points": ex.knowledge_points
            })
            if len(exercises) >= request.limit:
                break

    return TargetPracticeResponse(
        exercises=exercises,
        weak_points=[WeakPointResponse.model_validate(wp) for wp in weak_points],
        total=len(exercises)
    )


@router.get("/stats", response_model=ReviewStatsResponse)
async def get_review_stats(
    db: db_dependency,
    user: auth_dependency
):
    """
    Get review statistics for the current user.
    """
    from app.utils.time import utc_now

    now = utc_now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Get all repetitions
    result = await db.execute(
        select(SpacedRepetition).where(SpacedRepetition.user_id == user.id)
    )
    all_repetitions = result.scalars().all()

    # Calculate stats (use _make_aware for timezone-aware comparison)
    total_due = len([r for r in all_repetitions if _make_aware(r.next_review_at) <= now])
    total_scheduled = len(all_repetitions)

    # Reviewed today
    reviewed_today = len([
        r for r in all_repetitions
        if _make_aware(r.last_review_at) and _make_aware(r.last_review_at) >= today_start
    ])

    # Get weak points count
    weak_result = await db.execute(
        select(UserWeakPoint).where(UserWeakPoint.user_id == user.id)
    )
    weak_points = weak_result.scalars().all()

    # Mastery distribution
    mastery_dist = {}
    for wp in weak_points:
        level = wp.mastery_level
        mastery_dist[str(level)] = mastery_dist.get(str(level), 0) + 1

    return ReviewStatsResponse(
        total_due=total_due,
        total_scheduled=total_scheduled,
        reviewed_today=reviewed_today,
        streak_days=user.current_streak or 0,
        weak_points_count=len(weak_points),
        mastery_distribution=mastery_dist
    )


# ========== Wrong Questions Endpoints ==========

@router.get("/wrong-questions", response_model=WrongQuestionListResponse)
async def get_wrong_questions(
    db: db_dependency,
    user: auth_dependency,
    course_id: int = None,
    chapter_id: int = None,
    is_resolved: bool = None,
    limit: int = 50,
    offset: int = 0,
):
    """
    Get list of user's wrong questions.

    Supports filtering by course, chapter, and resolution status.
    """
    logger.info(f"[API] 获取错题列表: user_id={user.id}, course_id={course_id}, chapter_id={chapter_id}, is_resolved={is_resolved}")

    try:
        wrong_questions, total = await wrong_question_service.get_user_wrong_questions(
            db=db,
            user_id=user.id,
            course_id=course_id,
            chapter_id=chapter_id,
            is_resolved=is_resolved,
            limit=limit,
            offset=offset,
        )

        unresolved_count = await wrong_question_service.get_unresolved_count(
            db=db,
            user_id=user.id,
            course_id=course_id,
        )

        logger.info(f"[API] 错题列表结果: total={total}, unresolved={unresolved_count}, 返回 {len(wrong_questions)} 条")

        return WrongQuestionListResponse(
            wrong_questions=[WrongQuestionResponse.model_validate(wq) for wq in wrong_questions],
            total=total,
            unresolved_count=unresolved_count,
        )
    except Exception as e:
        logger.error(f"[API] 获取错题列表失败: {e}", exc_info=True)
        raise


@router.get("/wrong-questions/{wrong_question_id}")
async def get_wrong_question(
    wrong_question_id: str,
    db: db_dependency,
    user: auth_dependency,
):
    """
    Get details of a specific wrong question.
    """
    wrong_question = await wrong_question_service.get_wrong_question_by_id(
        db=db,
        wrong_question_id=wrong_question_id,
        user_id=user.id,
    )

    if not wrong_question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wrong question not found"
        )

    return WrongQuestionResponse.model_validate(wrong_question)


@router.post("/wrong-questions/collect", response_model=CollectWrongQuestionResponse)
async def collect_wrong_question(
    request: CollectWrongQuestionRequest,
    db: db_dependency,
    user: auth_dependency,
):
    """
    Collect a wrong question (for frontend hardcoded exercises).

    当前端使用硬编码习题（非数据库 Exercise）时，使用此端点收集错题。
    exercise_key 格式：chapterId-subsectionIndex-exerciseId
    """
    logger.info(f"[API] 收集错题: user_id={user.id}, exercise_key={request.exercise_key}, course_id={request.course_id}")

    try:
        wrong_question = await wrong_question_service.collect_wrong_question_by_key(
            db=db,
            user_id=user.id,
            exercise_key=request.exercise_key,
            user_answer=request.user_answer,
            course_id=request.course_id,
            chapter_id=request.chapter_id,
            section_id=request.section_id,
            exercise_content=request.exercise_content,
            exercise_type=request.exercise_type,
            knowledge_points=request.knowledge_points,
        )

        await db.commit()

        logger.info(f"[API] 错题收集成功: id={wrong_question.id}, error_count={wrong_question.error_count}")

        return CollectWrongQuestionResponse(
            id=wrong_question.id,
            exercise_key=request.exercise_key,
            error_count=wrong_question.error_count,
            is_resolved=wrong_question.is_resolved,
            message="错题已记录" if wrong_question.error_count == 1 else f"错题已更新，累计错误 {wrong_question.error_count} 次",
        )
    except Exception as e:
        logger.error(f"[API] 收集错题失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"收集错题失败: {str(e)}",
        )


class ResolveWrongQuestionRequest(BaseModel):
    """标记错题已解决请求"""
    exercise_key: Optional[str] = Field(None, description="练习题标识（用于精进之路/挑战之路等 exercise_id 为 None 的情况）")


@router.post("/wrong-questions/{exercise_id}/resolve")
async def resolve_wrong_question(
    exercise_id: int,
    request: ResolveWrongQuestionRequest,
    db: db_dependency,
    user: auth_dependency,
):
    """
    Mark a wrong question as resolved (when user answers correctly).

    当用户答对曾经错过的题目时调用此端点。
    支持通过 exercise_id 或 exercise_key 查找错题记录。
    """
    logger.info(f"[API] 标记错题已解决: user_id={user.id}, exercise_id={exercise_id}, exercise_key={request.exercise_key}")

    try:
        # 如果提供了 exercise_key（如 mastery-1-2-3），优先用它查找
        # 因为精进之路/挑战之路的错题 exercise_id 为 None
        if request.exercise_key:
            wrong_question = await wrong_question_service.mark_resolved(
                db=db,
                user_id=user.id,
                exercise_key=request.exercise_key,
            )
        else:
            wrong_question = await wrong_question_service.mark_resolved(
                db=db,
                user_id=user.id,
                exercise_id=exercise_id,
            )

        if not wrong_question:
            # 没有找到对应的错题记录，但这不是错误（可能用户第一次答这道题）
            logger.info(f"[API] 未找到错题记录，无需标记: exercise_id={exercise_id}")
            return {"success": True, "message": "未找到错题记录"}

        await db.commit()

        logger.info(f"[API] 错题已标记解决: id={wrong_question.id}")

        return {
            "success": True,
            "wrong_question": WrongQuestionResponse.model_validate(wrong_question),
            "message": "错题已标记为已掌握",
        }
    except Exception as e:
        logger.error(f"[API] 标记错题解决失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"标记失败: {str(e)}",
        )


@router.delete("/wrong-questions/{wrong_question_id}")
async def delete_wrong_question(
    wrong_question_id: str,
    db: db_dependency,
    user: auth_dependency,
):
    """
    Delete a wrong question record.

    删除指定的错题记录。
    """
    logger.info(f"[API] 删除错题: user_id={user.id}, wrong_question_id={wrong_question_id}")

    try:
        deleted = await wrong_question_service.delete_wrong_question(
            db=db,
            wrong_question_id=wrong_question_id,
            user_id=user.id,
        )

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="错题记录不存在或无权删除"
            )

        await db.commit()

        logger.info(f"[API] 错题已删除: wrong_question_id={wrong_question_id}")

        return {
            "success": True,
            "message": "错题已删除",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] 删除错题失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除失败: {str(e)}",
        )


# ========== Analysis Endpoints ==========

@router.get("/analysis/weak-points", response_model=WeakPointAnalysisResponse)
async def get_weak_points_analysis(
    db: db_dependency,
    user: auth_dependency,
    course_id: int = None,
    limit: int = 20,
):
    """
    Get analysis of weak knowledge points.

    Returns:
    - All knowledge points with error rates
    - Weakest points (top 5)
    - Strongest points (top 5)
    - Overall error rate
    """
    query = select(UserWeakPoint).where(UserWeakPoint.user_id == user.id)

    if course_id:
        query = query.where(UserWeakPoint.course_id == course_id)

    result = await db.execute(query)
    weak_points = list(result.scalars().all())

    if not weak_points:
        return WeakPointAnalysisResponse(
            knowledge_points=[],
            weakest_knowledge_points=[],
            strongest_knowledge_points=[],
            total_knowledge_points=0,
            overall_error_rate=0.0,
        )

    # Calculate analysis for each knowledge point
    analyses = []
    total_errors = sum(wp.error_count for wp in weak_points)
    total_attempts = sum(wp.error_count + wp.review_count for wp in weak_points)

    for wp in weak_points:
        # Calculate error rate
        attempts = wp.error_count + wp.review_count
        error_rate = wp.error_count / attempts if attempts > 0 else 0.0

        # Calculate weak score (higher = weaker)
        error_factor = min(1.0, wp.error_count / 10)
        mastery_factor = (6 - wp.mastery_level) / 5
        weak_score = (error_factor + mastery_factor) / 2

        analyses.append(KnowledgePointAnalysis(
            knowledge_point=wp.knowledge_point,
            error_count=wp.error_count,
            total_attempts=attempts,
            error_rate=error_rate,
            mastery_level=wp.mastery_level,
            weak_score=weak_score,
            rank=0,  # Will be set after sorting
        ))

    # Sort by weak_score (descending) and assign ranks
    analyses.sort(key=lambda x: x.weak_score, reverse=True)
    for i, a in enumerate(analyses):
        a.rank = i + 1

    # Get weakest and strongest
    weakest = analyses[:5] if len(analyses) >= 5 else analyses
    strongest = analyses[-5:] if len(analyses) >= 5 else analyses
    strongest = sorted(strongest, key=lambda x: x.weak_score, reverse=False)

    overall_error_rate = total_errors / total_attempts if total_attempts > 0 else 0.0

    return WeakPointAnalysisResponse(
        knowledge_points=analyses,
        weakest_knowledge_points=weakest,
        strongest_knowledge_points=strongest,
        total_knowledge_points=len(analyses),
        overall_error_rate=overall_error_rate,
    )


# ========== Enhanced Practice Endpoints ==========

@router.post("/practice/enhanced", response_model=EnhancedTargetPracticeResponse)
async def enhanced_target_practice(
    request: EnhancedTargetPracticeRequest,
    db: db_dependency,
    user: auth_dependency,
):
    """
    Get exercises for enhanced targeted practice.

    Modes:
    - quick: 5 questions focusing on weakest points
    - deep: 10 questions with more variety
    - specific: Focus on specific knowledge points
    """
    # Determine limit based on mode
    limit = request.limit
    if request.mode == "quick":
        limit = min(limit, 5)
    elif request.mode == "deep":
        limit = min(limit, 10)

    # Get weak points to target
    query = select(UserWeakPoint).where(UserWeakPoint.user_id == user.id)

    if request.course_id:
        query = query.where(UserWeakPoint.course_id == request.course_id)

    if request.knowledge_points:
        query = query.where(UserWeakPoint.knowledge_point.in_(request.knowledge_points))

    # Order by weakness (weakest first)
    query = query.order_by(UserWeakPoint.mastery_level, UserWeakPoint.error_count.desc())

    result = await db.execute(query)
    weak_points = list(result.scalars().all())

    if not weak_points:
        return EnhancedTargetPracticeResponse(
            exercises=[],
            weak_points=[],
            mode=request.mode,
            total=0,
            message="No weak points found matching the criteria"
        )

    # Find exercises targeting these knowledge points
    kp_list = [wp.knowledge_point for wp in weak_points]

    # Build query for exercises
    exercise_query = select(Exercise).where(Exercise.is_verified)

    if request.difficulty_range:
        min_diff, max_diff = request.difficulty_range
        exercise_query = exercise_query.where(
            Exercise.difficulty >= min_diff,
            Exercise.difficulty <= max_diff
        )

    exercise_result = await db.execute(exercise_query)
    all_exercises = list(exercise_result.scalars().all())

    # Filter and prioritize by knowledge points
    exercises = []
    kp_coverage = {kp: [] for kp in kp_list}

    for ex in all_exercises:
        ex_kps = ex.knowledge_points or []
        matched_kps = [kp for kp in ex_kps if kp in kp_list]
        if matched_kps:
            # Calculate match score based on how many weak KPs this addresses
            match_score = len(matched_kps)
            exercises.append({
                "id": ex.id,
                "type": ex.type,
                "difficulty": ex.difficulty,
                "content": ex.content,
                "knowledge_points": ex.knowledge_points,
                "match_score": match_score,
                "matched_knowledge_points": matched_kps,
            })
            for kp in matched_kps:
                kp_coverage[kp].append(ex.id)

    # Sort by match score
    exercises.sort(key=lambda x: x.get("match_score", 0), reverse=True)

    # Take top exercises ensuring variety
    selected = []
    covered_kps = set()
    for ex in exercises:
        if len(selected) >= limit:
            break
        # Ensure variety - don't pick too many from same KPs
        ex_kps = ex.get("matched_knowledge_points", [])
        if len(selected) < 3 or not any(kp in covered_kps for kp in ex_kps):
            selected.append({
                "id": ex["id"],
                "type": ex["type"],
                "difficulty": ex["difficulty"],
                "content": ex["content"],
                "knowledge_points": ex["knowledge_points"],
            })
            covered_kps.update(ex_kps)

    return EnhancedTargetPracticeResponse(
        exercises=selected,
        weak_points=[WeakPointResponse.model_validate(wp) for wp in weak_points],
        mode=request.mode,
        total=len(selected),
        message=f"Found {len(selected)} exercises for {request.mode} practice"
    )


# ========== Review Reminder Endpoints ==========

@router.get("/reminders", response_model=ReviewReminderResponse)
async def get_review_reminders(
    db: db_dependency,
    user: auth_dependency,
):
    """
    Get review reminders based on Ebbinghaus forgetting curve.

    Returns:
    - Due reviews (past scheduled time)
    - Upcoming reviews (next 30 days)
    - Ebbinghaus schedule (1, 3, 7, 15, 30 days)
    """
    from app.utils.time import utc_now
    from datetime import timedelta

    now = utc_now()

    # Get all repetitions
    result = await db.execute(
        select(SpacedRepetition).where(SpacedRepetition.user_id == user.id)
    )
    all_repetitions = list(result.scalars().all())

    # Get exercise details
    exercise_ids = [r.exercise_id for r in all_repetitions]
    exercises = {}
    if exercise_ids:  # 只有在有 ID 时才查询，避免空列表查询错误
        exercises_result = await db.execute(
            select(Exercise).where(Exercise.id.in_(exercise_ids))
        )
        exercises = {e.id: e for e in exercises_result.scalars().all()}

    # Get weak points
    weak_result = await db.execute(
        select(UserWeakPoint).where(UserWeakPoint.user_id == user.id)
    )
    weak_points = {wp.knowledge_point: wp for wp in weak_result.scalars().all()}

    # Ebbinghaus intervals
    ebbinghaus_intervals = [
        {"day": 1, "label": "1天"},
        {"day": 3, "label": "3天"},
        {"day": 7, "label": "7天"},
        {"day": 15, "label": "15天"},
        {"day": 30, "label": "30天"},
    ]

    # Categorize reviews
    due_reviews = []
    upcoming_by_date = {}
    schedule_counts = {eb["day"]: 0 for eb in ebbinghaus_intervals}

    for rep in all_repetitions:
        exercise = exercises.get(rep.exercise_id)
        if not exercise:
            continue

        # Calculate priority (use _make_aware for timezone-aware comparison)
        next_review_aware = _make_aware(rep.next_review_at)
        priority = 0.0
        days_overdue = (now - next_review_aware).days if next_review_aware <= now else 0
        priority += days_overdue * 0.5
        for kp in exercise.knowledge_points:
            if kp in weak_points:
                priority += weak_points[kp].weakness_score * 2

        if next_review_aware <= now:
            # Due now
            due_reviews.append(ReviewQueueItem(
                repetition=SpacedRepetitionResponse.model_validate(rep),
                exercise_id=exercise.id,
                exercise_type=exercise.type,
                exercise_difficulty=exercise.difficulty,
                knowledge_points=exercise.knowledge_points,
                stage_id=rep.stage_id,
                priority=priority
            ))
            schedule_counts[1] += 1  # Count as due
        else:
            # Future - categorize by interval
            days_until = (next_review_aware - now).days
            for eb in ebbinghaus_intervals:
                if eb["day"] - 1 <= days_until <= eb["day"] + 1:
                    date_key = (now + timedelta(days=eb["day"])).strftime("%Y-%m-%d")
                    if date_key not in upcoming_by_date:
                        upcoming_by_date[date_key] = {"count": 0, "label": eb["label"]}
                    upcoming_by_date[date_key]["count"] += 1
                    schedule_counts[eb["day"]] += 1
                    break

    # Sort due reviews by priority
    due_reviews.sort(key=lambda x: x.priority, reverse=True)

    # Build upcoming list
    upcoming = [
        {"date": date, "count": data["count"], "label": data["label"]}
        for date, data in sorted(upcoming_by_date.items())
    ]

    # Build schedule
    schedule = [
        {"day": eb["day"], "label": eb["label"], "count": schedule_counts[eb["day"]]}
        for eb in ebbinghaus_intervals
    ]

    return ReviewReminderResponse(
        due_reviews=due_reviews[:20],  # Limit to top 20
        upcoming_reviews=upcoming,
        ebbinghaus_schedule=schedule,
        total_due=len(due_reviews),
        total_upcoming=sum(u["count"] for u in upcoming),
    )

