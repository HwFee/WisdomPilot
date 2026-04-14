"""Course API Router"""

from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.course import Course
from app.models.chapter import Chapter
from app.models.exercise import Exercise
from app.models.user import User
from app.models.stage import Stage
from app.schemas.course import (
    CourseListResponse,
    CourseDetailResponse,
    CourseSummary,
    ChapterSummary,
    ChapterDetail,
    ExerciseSummary,
    ChapterDetailResponse,
    CourseDetail,
)
from app.schemas.stage import StageSummary

router = APIRouter(prefix="/api/courses", tags=["courses"])

db_dependency = Annotated[AsyncSession, Depends(get_db)]

# Import dependencies directly from deps module
from app.utils.deps import get_current_active_user, get_optional_user

auth_dependency = Annotated[User, Depends(get_current_active_user)]
optional_user_dependency = Annotated[Optional[User], Depends(get_optional_user)]


# 8门课程初始化数据
COURSES_INIT_DATA = [
    {"code": "C", "name": "C语言程序设计", "difficulty_level": 1, "icon": "c"},
    {"code": "CPP", "name": "C++程序设计", "difficulty_level": 2, "icon": "cpp"},
    {"code": "Python", "name": "Python程序设计", "difficulty_level": 1, "icon": "python"},
    {"code": "Java", "name": "Java程序设计", "difficulty_level": 2, "icon": "java"},
    {"code": "Rust", "name": "Rust程序设计", "difficulty_level": 4, "icon": "rust"},
    {"code": "DSA", "name": "数据结构与算法", "difficulty_level": 3, "icon": "dsa"},
    {"code": "ADA", "name": "算法设计与分析", "difficulty_level": 4, "icon": "ada"},
    {"code": "DiscreteMath", "name": "离散数学", "difficulty_level": 3, "icon": "math"},
]


@router.get("", response_model=CourseListResponse)
async def get_courses(db: db_dependency):
    """
    Get all active courses with chapter count.

    Returns a list of courses with basic info and chapter count.
    This endpoint is public - no authentication required.
    """
    query = (
        select(
            Course,
            func.count(Chapter.id).label("chapter_count")
        )
        .outerjoin(Chapter, Course.id == Chapter.course_id)
        .where(Course.is_active == True)
        .group_by(Course.id)
        .order_by(Course.difficulty_level, Course.code)
    )

    result = await db.execute(query)
    rows = result.all()

    courses = []
    for course, chapter_count in rows:
        courses.append(CourseSummary(
            id=course.id,
            code=course.code,
            name=course.name,
            description=course.description,
            difficulty_level=course.difficulty_level,
            icon=course.icon,
            is_active=course.is_active,
            chapter_count=chapter_count
        ))

    return CourseListResponse(courses=courses, total=len(courses))


@router.get("/{course_id}", response_model=CourseDetailResponse)
async def get_course(
    course_id: int,
    db: db_dependency,
    user: optional_user_dependency = None
):
    """
    Get course details including chapters.

    Returns course info with embedded chapter list.
    If authenticated, also returns enrolled status.
    """
    query = (
        select(Course)
        .where(Course.id == course_id)
        .options(selectinload(Course.chapters))
    )

    result = await db.execute(query)
    course = result.scalar_one_or_none()

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with id {course_id} not found"
        )

    chapters = [
        ChapterSummary.model_validate(ch)
        for ch in sorted(course.chapters, key=lambda x: x.order_index)
        if ch.is_active
    ]

    course_detail = CourseDetail.model_validate(course)
    course_detail.chapters = chapters

    # Check if user is enrolled (if authenticated)
    enrolled = False
    if user:
        enrolled_ids = user.courses_enrolled or []
        enrolled = course_id in enrolled_ids

    return CourseDetailResponse(course=course_detail, enrolled=enrolled)


@router.get("/code/{code}", response_model=CourseDetailResponse)
async def get_course_by_code(code: str, db: db_dependency):
    """
    Get course details by course code.

    Returns course info with embedded chapter list.
    This endpoint is public - no authentication required.
    """
    query = (
        select(Course)
        .where(Course.code == code)
        .options(selectinload(Course.chapters))
    )

    result = await db.execute(query)
    course = result.scalar_one_or_none()

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with code '{code}' not found"
        )

    chapters = [
        ChapterSummary.model_validate(ch)
        for ch in sorted(course.chapters, key=lambda x: x.order_index)
        if ch.is_active
    ]

    course_detail = CourseDetail.model_validate(course)
    course_detail.chapters = chapters

    return CourseDetailResponse(course=course_detail)


# Direct chapter access by chapter ID (for frontend convenience)
@router.get("/chapters/{chapter_id}", response_model=ChapterDetailResponse)
async def get_chapter_by_id(chapter_id: int, db: db_dependency):
    """
    Get chapter details by chapter ID directly.

    Returns chapter info with embedded exercise list.
    This endpoint is public - no authentication required.
    """
    query = (
        select(Chapter)
        .where(Chapter.id == chapter_id)
        .options(selectinload(Chapter.exercises))
    )

    result = await db.execute(query)
    chapter = result.scalar_one_or_none()

    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter {chapter_id} not found"
        )

    exercises = [
        ExerciseSummary(
            id=ex.id,
            chapter_id=ex.chapter_id,
            source=ex.source,
            source_id=ex.source_id,
            type=ex.type,
            difficulty=ex.difficulty,
            content=ex.content,
            hints=ex.hints,
        )
        for ex in chapter.exercises
    ]

    chapter_detail = ChapterDetail(
        id=chapter.id,
        course_id=chapter.course_id,
        title=chapter.title,
        description=chapter.description,
        content=chapter.content,
        order_index=chapter.order_index,
        learning_objectives=chapter.learning_objectives,
        difficulty_tags=chapter.difficulty_tags,
        skill_tags=chapter.skill_tags,
        estimated_minutes=chapter.estimated_minutes,
        is_active=chapter.is_active,
    )

    return ChapterDetailResponse(chapter=chapter_detail, exercises=exercises)


@router.get("/{course_id}/chapters/{chapter_id}", response_model=ChapterDetailResponse)
async def get_chapter(course_id: int, chapter_id: int, db: db_dependency):
    """
    Get chapter details including exercises.

    Returns chapter info with embedded exercise list.
    This endpoint is public - no authentication required.
    """
    query = (
        select(Chapter)
        .where(Chapter.id == chapter_id, Chapter.course_id == course_id)
        .options(selectinload(Chapter.exercises))
    )

    result = await db.execute(query)
    chapter = result.scalar_one_or_none()

    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter {chapter_id} not found in course {course_id}"
        )

    exercises = [
        ExerciseSummary(
            id=ex.id,
            chapter_id=ex.chapter_id,
            source=ex.source,
            source_id=ex.source_id,
            type=ex.type,
            difficulty=ex.difficulty,
            content=ex.content,
            hints=ex.hints,
        )
        for ex in chapter.exercises
    ]

    chapter_detail = ChapterDetail(
        id=chapter.id,
        course_id=chapter.course_id,
        title=chapter.title,
        description=chapter.description,
        content=chapter.content,
        order_index=chapter.order_index,
        learning_objectives=chapter.learning_objectives,
        difficulty_tags=chapter.difficulty_tags,
        skill_tags=chapter.skill_tags,
        estimated_minutes=chapter.estimated_minutes,
        is_active=chapter.is_active,
    )

    return ChapterDetailResponse(chapter=chapter_detail, exercises=exercises)


@router.post("/{course_id}/enroll")
async def enroll_course(
    course_id: int,
    db: db_dependency,
    current_user: User = Depends(get_current_active_user)
):
    """
    Enroll current user in a course.

    Adds the course to user's enrolled courses list.
    """
    try:
        # Check course exists
        result = await db.execute(
            select(Course).where(Course.id == course_id, Course.is_active == True)
        )
        course = result.scalar_one_or_none()

        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course {course_id} not found"
            )

        # Re-fetch user in current session to ensure it's attached
        user_result = await db.execute(
            select(User).where(User.id == current_user.id)
        )
        user = user_result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Check if already enrolled - handle None case
        enrolled = list(user.courses_enrolled) if user.courses_enrolled else []
        if course_id in enrolled:
            return {
                "message": f"Already enrolled in {course.name}",
                "course_id": course_id,
                "enrolled_courses": enrolled,
                "already_enrolled": True
            }

        # Add to enrolled courses - create new list to trigger SQLAlchemy change detection
        enrolled.append(course_id)
        user.courses_enrolled = enrolled  # Assign new list to trigger change

        # Mark the attribute as modified for SQLAlchemy (needed for JSON fields)
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(user, "courses_enrolled")

        await db.commit()

        return {
            "message": f"Successfully enrolled in {course.name}",
            "course_id": course_id,
            "enrolled_courses": enrolled
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Enrollment failed: {str(e)}"
        )


@router.get("/{course_id}/stages")
async def get_course_stages(
    course_id: int,
    db: db_dependency,
    user: auth_dependency
):
    """
    Get all stages for a course.

    Returns stage list with progress info.
    """
    # Check course exists
    result = await db.execute(
        select(Course).where(Course.id == course_id, Course.is_active == True)
    )
    course = result.scalar_one_or_none()

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course {course_id} not found"
        )

    # Get stages
    stages_result = await db.execute(
        select(Stage)
        .where(Stage.course_id == course_id, Stage.is_active == True)
        .order_by(Stage.order_index)
    )
    stages = stages_result.scalars().all()

    return {
        "course_id": course_id,
        "course_name": course.name,
        "stages": [StageSummary.model_validate(s) for s in stages],
        "total": len(stages)
    }


@router.get("/users/me/course-progress")
async def get_user_course_progress(
    db: db_dependency,
    current_user: auth_dependency
):
    """
    Get progress for all courses for the current user.

    Returns a list of all 8 courses with user's progress in each:
    - Progress percentage
    - Mastery score (for 精进之路)
    - Arena tier and score (for 挑战之路)
    - Current chapter
    """
    from app.models.stage import Stage
    from app.models.user_stage import UserStageProgress, StageStatus
    from app.models.chapter_mastery import ChapterMastery
    from app.models.user_arena import UserArenaProfile

    # Get all courses
    courses_result = await db.execute(
        select(Course).where(Course.is_active == True).order_by(Course.difficulty_level, Course.code)
    )
    all_courses = courses_result.scalars().all()

    # Get user's stage progress for all courses
    stage_progress_result = await db.execute(
        select(UserStageProgress, Stage)
        .join(Stage, UserStageProgress.stage_id == Stage.id)
        .where(UserStageProgress.user_id == current_user.id)
    )
    stage_progress_rows = stage_progress_result.all()

    # Group stage progress by course
    course_stages: dict[int, list] = {}
    for progress, stage in stage_progress_rows:
        if stage.course_id not in course_stages:
            course_stages[stage.course_id] = []
        course_stages[stage.course_id].append(progress)

    # Get total stages per course
    total_stages_result = await db.execute(
        select(Stage.course_id, func.count(Stage.id).label('count'))
        .where(Stage.is_active == True)
        .group_by(Stage.course_id)
    )
    total_stages_map = {row.course_id: row.count for row in total_stages_result.all()}

    # Get user's mastery scores per course
    mastery_result = await db.execute(
        select(ChapterMastery.course_id, func.sum(ChapterMastery.mastery_score).label('total_mastery'))
        .where(ChapterMastery.user_id == current_user.id)
        .group_by(ChapterMastery.course_id)
    )
    mastery_map = {row.course_id: row.total_mastery for row in mastery_result.all()}

    # Get user's arena profiles per course
    arena_result = await db.execute(
        select(UserArenaProfile).where(UserArenaProfile.user_id == current_user.id)
    )
    arena_profiles = {p.course_id: p for p in arena_result.scalars().all()}

    # Build response
    courses_data = []
    for course in all_courses:
        total_stages = total_stages_map.get(course.id, 0)
        user_stages = course_stages.get(course.id, [])

        # Calculate progress
        completed_stages = len([s for s in user_stages if s.status == StageStatus.COMPLETED.value])
        progress = round((completed_stages / total_stages) * 100, 1) if total_stages > 0 else 0

        # Get current chapter (first in-progress stage)
        current_chapter = None
        in_progress = [s for s in user_stages if s.status == StageStatus.IN_PROGRESS.value]
        if in_progress:
            # Get stage title
            for p, s in stage_progress_rows:
                if p.id == in_progress[0].id:
                    current_chapter = s.title
                    break

        # Get mastery and arena data
        mastery_score = mastery_map.get(course.id)
        arena_profile = arena_profiles.get(course.id)

        courses_data.append({
            "course_id": course.id,
            "course_code": course.code,
            "course_name": course.name,
            "progress": progress,
            "completed_stages": completed_stages,
            "total_stages": total_stages,
            "current_chapter": current_chapter,
            "mastery_score": round(mastery_score, 2) if mastery_score else None,
            "arena_tier": arena_profile.tier if arena_profile else None,
            "arena_score": arena_profile.total_score if arena_profile else None,
        })

    return {"courses": courses_data}


@router.post("/init")
async def init_courses(db: db_dependency, user: auth_dependency):
    """
    Initialize the 8 courses if they don't exist.

    Admin only endpoint.
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    created = []
    for course_data in COURSES_INIT_DATA:
        # Check if exists
        result = await db.execute(
            select(Course).where(Course.code == course_data["code"])
        )
        existing = result.scalar_one_or_none()

        if not existing:
            course = Course(
                code=course_data["code"],
                name=course_data["name"],
                difficulty_level=course_data["difficulty_level"],
                icon=course_data["icon"],
                is_active=True
            )
            db.add(course)
            created.append(course_data["code"])

    await db.flush()

    return {
        "message": f"Created {len(created)} new courses",
        "created": created
    }
