"""
Tests for Section API endpoints.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, Course, Chapter, Section, SectionProgress
from app.utils.security import create_access_token


@pytest.fixture
async def setup_sections_data(db_session: AsyncSession):
    """Setup test data for sections tests."""
    # Create course
    course = Course(
        code="TEST_C",
        name="Test C Course",
        difficulty_level=1,
        icon="c",
        is_active=True,
    )
    db_session.add(course)
    await db_session.flush()

    # Create chapter
    chapter = Chapter(
        course_id=course.id,
        title="Test Chapter",
        order_index=1,
    )
    db_session.add(chapter)
    await db_session.flush()

    # Create sections
    sections = [
        Section(
            chapter_id=chapter.id,
            title=f"Section {i}",
            description=f"Description for section {i}",
            content=f"# Section {i}\n\nContent for section {i}.",
            order_index=i,
            estimated_minutes=15,
            is_active=True,
        )
        for i in range(1, 4)
    ]
    db_session.add_all(sections)
    await db_session.flush()

    return {
        "course": course,
        "chapter": chapter,
        "sections": sections,
    }


@pytest.mark.asyncio
async def test_get_chapter_sections(
    client: AsyncClient,
    auth_user: User,
    setup_sections_data,
):
    """Test getting chapter sections list."""
    data = setup_sections_data
    token = create_access_token({"sub": auth_user.id})

    response = await client.get(
        f"/api/courses/chapters/{data['chapter'].id}/sections",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    result = response.json()
    assert "sections" in result
    assert result["total"] == 3
    assert len(result["sections"]) == 3

    # Verify sections are ordered correctly
    for i, section in enumerate(result["sections"]):
        assert section["title"] == f"Section {i + 1}"
        assert section["is_completed"] == False


@pytest.mark.asyncio
async def test_get_chapter_sections_with_progress(
    client: AsyncClient,
    auth_user: User,
    db_session: AsyncSession,
    setup_sections_data,
):
    """Test getting chapter sections with user progress."""
    data = setup_sections_data
    token = create_access_token({"sub": auth_user.id})

    # Mark first section as completed
    progress = SectionProgress(
        user_id=auth_user.id,
        section_id=data["sections"][0].id,
        is_completed=True,
        last_position="content",
    )
    db_session.add(progress)
    await db_session.flush()

    response = await client.get(
        f"/api/courses/chapters/{data['chapter'].id}/sections",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    result = response.json()

    # First section should be completed
    assert result["sections"][0]["is_completed"] == True
    assert result["sections"][1]["is_completed"] == False


@pytest.mark.asyncio
async def test_get_chapter_sections_not_found(
    client: AsyncClient,
    auth_user: User,
):
    """Test getting sections for non-existent chapter."""
    token = create_access_token({"sub": auth_user.id})

    response = await client.get(
        "/api/courses/chapters/99999/sections",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_section_detail(
    client: AsyncClient,
    auth_user: User,
    setup_sections_data,
):
    """Test getting section detail."""
    data = setup_sections_data
    token = create_access_token({"sub": auth_user.id})
    section = data["sections"][0]

    response = await client.get(
        f"/api/courses/sections/{section.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["section"]["id"] == section.id
    assert result["section"]["title"] == "Section 1"
    assert result["section"]["content"] is not None
    assert result["section"]["is_completed"] == False


@pytest.mark.asyncio
async def test_get_section_not_found(
    client: AsyncClient,
    auth_user: User,
):
    """Test getting non-existent section."""
    token = create_access_token({"sub": auth_user.id})

    response = await client.get(
        "/api/courses/sections/99999",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_save_section_progress(
    client: AsyncClient,
    auth_user: User,
    db_session: AsyncSession,
    setup_sections_data,
):
    """Test saving section progress."""
    data = setup_sections_data
    token = create_access_token({"sub": auth_user.id})
    section = data["sections"][0]

    # Save progress (position: content, not completed)
    response = await client.post(
        f"/api/courses/sections/{section.id}/progress",
        headers={"Authorization": f"Bearer {token}"},
        json={"position": "content", "is_completed": False},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["section_id"] == section.id
    assert result["is_completed"] == False
    assert result["last_position"] == "content"

    # Verify progress is saved in database
    from sqlalchemy import select
    progress_result = await db_session.execute(
        select(SectionProgress).where(
            SectionProgress.user_id == auth_user.id,
            SectionProgress.section_id == section.id,
        )
    )
    progress = progress_result.scalar_one()
    assert progress.is_completed == False
    assert progress.last_position == "content"


@pytest.mark.asyncio
async def test_save_section_progress_completed(
    client: AsyncClient,
    auth_user: User,
    db_session: AsyncSession,
    setup_sections_data,
):
    """Test marking section as completed."""
    data = setup_sections_data
    token = create_access_token({"sub": auth_user.id})
    section = data["sections"][0]

    # Mark as completed
    response = await client.post(
        f"/api/courses/sections/{section.id}/progress",
        headers={"Authorization": f"Bearer {token}"},
        json={"position": "quiz", "is_completed": True},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["is_completed"] == True
    assert result["completed_at"] is not None


@pytest.mark.asyncio
async def test_get_current_position_no_progress(
    client: AsyncClient,
    auth_user: User,
    setup_sections_data,
):
    """Test getting current position when no progress exists - returns first section."""
    data = setup_sections_data
    token = create_access_token({"sub": auth_user.id})

    response = await client.get(
        f"/api/courses/{data['course'].id}/current-position",
        headers={"Authorization": f"Bearer {token}"},
    )

    # Should return 200 with first section (since no progress, first incomplete section)
    assert response.status_code == 200
    result = response.json()
    assert result["course_id"] == data["course"].id
    assert result["section_id"] == data["sections"][0].id  # First section
    assert result["position"] == "content"  # Default position


@pytest.mark.asyncio
async def test_get_current_position_with_progress(
    client: AsyncClient,
    auth_user: User,
    db_session: AsyncSession,
    setup_sections_data,
):
    """Test getting current position with existing progress - returns first incomplete section."""
    data = setup_sections_data
    token = create_access_token({"sub": auth_user.id})

    # Mark first section as completed
    progress = SectionProgress(
        user_id=auth_user.id,
        section_id=data["sections"][0].id,
        is_completed=True,
        last_position="quiz",
    )
    db_session.add(progress)
    await db_session.flush()

    response = await client.get(
        f"/api/courses/{data['course'].id}/current-position",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["course_id"] == data["course"].id
    assert result["chapter_id"] == data["chapter"].id
    # Should return second section since first is completed
    assert result["section_id"] == data["sections"][1].id
    assert result["position"] == "content"  # Default for no progress


@pytest.mark.asyncio
async def test_unauthorized_access(
    client: AsyncClient,
    setup_sections_data,
):
    """Test accessing sections without authentication."""
    data = setup_sections_data

    # All these should return 401
    response1 = await client.get(
        f"/api/courses/chapters/{data['chapter'].id}/sections"
    )
    assert response1.status_code == 401

    response2 = await client.get(f"/api/courses/sections/{data['sections'][0].id}")
    assert response2.status_code == 401

    response3 = await client.post(
        f"/api/courses/sections/{data['sections'][0].id}/progress",
        json={"position": "content", "is_completed": False},
    )
    assert response3.status_code == 401
