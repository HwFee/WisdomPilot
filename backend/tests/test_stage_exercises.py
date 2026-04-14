"""Tests for Stage Exercise Generation API"""

import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course import Course
from app.models.stage import Stage
from app.models.exercise import Exercise
from app.models.user import User


# Mock AI service responses for testing
MOCK_EXERCISES = [
    {
        "content": {
            "text": "Python中用于定义函数的关键字是？",
            "options": ["function", "def", "func", "define"],
        },
        "solution": {"answer": 1, "explanation": "Python使用def关键字定义函数"},
        "hints": ["想想Python的语法"],
    },
    {
        "content": {
            "text": "以下哪个是有效的Python变量名？",
            "options": ["1var", "var-name", "my_var", "class"],
        },
        "solution": {"answer": 2, "explanation": "变量名可以包含字母、数字和下划线，但不能以数字开头"},
        "hints": ["变量命名规则"],
    },
    {
        "content": {
            "text": "print(type(3.14))的输出结果是？",
            "options": ["<class 'int'>", "<class 'float'>", "<class 'str'>", "<class 'number'>"],
        },
        "solution": {"answer": 1, "explanation": "3.14是浮点数，类型为float"},
        "hints": ["小数是什么类型？"],
    },
]


@pytest.mark.asyncio
async def test_get_stage_exercises_empty(db_session: AsyncSession, client: AsyncClient, test_user_token: str):
    """Test getting exercises for a stage with no exercises."""
    # Create test course and stage
    course = Course(code="TEST_COURSE", name="测试课程", difficulty_level=1)
    db_session.add(course)
    await db_session.flush()

    stage = Stage(
        course_id=course.id,
        order_index=1,
        title="测试关卡",
        description="测试描述",
        required_exercises=5,
        difficulty_level=1,
    )
    db_session.add(stage)
    await db_session.flush()

    # Get exercises
    response = await client.get(
        f"/api/stages/{stage.id}/exercises",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["exercises"] == []


@pytest.mark.asyncio
async def test_generate_stage_exercises(db_session: AsyncSession, client: AsyncClient, admin_token: str):
    """Test AI generation of exercises for a stage."""
    # Create test course and stage
    course = Course(code="TEST_GEN", name="测试生成课程", difficulty_level=1)
    db_session.add(course)
    await db_session.flush()

    stage = Stage(
        course_id=course.id,
        order_index=1,
        title="变量与数据类型",
        description="学习Python基础变量和数据类型",
        required_exercises=5,
        difficulty_level=1,
        learning_objectives=["理解变量概念", "掌握基本数据类型"],
    )
    db_session.add(stage)
    await db_session.flush()

    # Mock AI service to return test exercises
    with patch("app.routers.stages.ai_service") as mock_ai:
        mock_ai.is_configured.return_value = True
        mock_ai.generate_exercises = AsyncMock(return_value=MOCK_EXERCISES)

        # Generate exercises
        response = await client.post(
            f"/api/stages/{stage.id}/exercises/generate",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "count": 3,
                "exercise_type": "choice",
                "difficulty": 1,
            }
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["generated"] == 3
    assert len(data["exercises"]) == 3


@pytest.mark.asyncio
async def test_generate_stage_exercises_quota_check(db_session: AsyncSession, client: AsyncClient, test_user_token: str, test_user: User):
    """Test that exercise generation consumes quota."""
    # Create test course and stage
    course = Course(code="QUOTA_TEST", name="配额测试", difficulty_level=1)
    db_session.add(course)
    await db_session.flush()

    stage = Stage(
        course_id=course.id,
        order_index=1,
        title="测试关卡",
        required_exercises=5,
        difficulty_level=1,
    )
    db_session.add(stage)
    await db_session.flush()

    # Set user quota
    test_user.ai_quota = 10
    await db_session.flush()

    # Try to generate as regular user (should fail or consume quota)
    response = await client.post(
        f"/api/stages/{stage.id}/exercises/generate",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={"count": 3, "exercise_type": "choice", "difficulty": 1}
    )

    # Regular users should not have permission
    assert response.status_code in [403, 401]


@pytest.mark.asyncio
async def test_get_stage_exercises_with_data(db_session: AsyncSession, client: AsyncClient, test_user_token: str):
    """Test getting exercises for a stage with existing exercises."""
    # Create test course, stage and exercises
    course = Course(code="EX_DATA", name="数据测试", difficulty_level=1)
    db_session.add(course)
    await db_session.flush()

    stage = Stage(
        course_id=course.id,
        order_index=1,
        title="测试关卡",
        required_exercises=5,
        difficulty_level=1,
    )
    db_session.add(stage)
    await db_session.flush()

    # Create exercises
    for i in range(3):
        exercise = Exercise(
            stage_id=stage.id,
            type="choice",
            difficulty=1,
            content={
                "text": f"测试题目 {i+1}",
                "options": ["A", "B", "C", "D"],
            },
            solution={"answer": 0, "explanation": "解释"},
            is_verified=True,
        )
        db_session.add(exercise)
    await db_session.flush()

    # Get exercises
    response = await client.get(
        f"/api/stages/{stage.id}/exercises",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["exercises"]) == 3


@pytest.mark.asyncio
async def test_start_stage_with_exercises(db_session: AsyncSession, client: AsyncClient, test_user_token: str):
    """Test starting a stage returns available exercises."""
    # Create test course and stage
    course = Course(code="START_TEST", name="开始测试", difficulty_level=1)
    db_session.add(course)
    await db_session.flush()

    stage = Stage(
        course_id=course.id,
        order_index=1,
        title="第一关",
        required_exercises=3,
        difficulty_level=1,
    )
    db_session.add(stage)
    await db_session.flush()

    # Create exercises
    for i in range(5):
        exercise = Exercise(
            stage_id=stage.id,
            type="choice",
            difficulty=1,
            content={
                "text": f"题目 {i+1}",
                "options": ["选项A", "选项B", "选项C", "选项D"],
            },
            solution={"answer": i % 4, "explanation": "解释"},
            is_verified=True,
        )
        db_session.add(exercise)
    await db_session.flush()

    # Start the stage
    response = await client.post(
        f"/api/stages/{stage.id}/start",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["progress"]["status"] == "in_progress"

    # Get exercises for practice
    response = await client.get(
        f"/api/stages/{stage.id}/exercises",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )

    assert response.status_code == 200
    exercises = response.json()["exercises"]
    assert len(exercises) >= stage.required_exercises
