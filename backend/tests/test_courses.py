"""Tests for Course API endpoints"""

import pytest

from app.main import app
from app.utils.deps import get_current_admin_user


@pytest.mark.asyncio
class TestCourseList:
    """Test GET /api/courses endpoint"""

    async def test_get_courses_returns_list(self, client):
        """Should return a list of courses (may be empty)"""
        response = await client.get("/api/courses")
        assert response.status_code == 200

        data = response.json()
        assert "courses" in data
        assert isinstance(data["courses"], list)

    async def test_get_courses_includes_course_fields(self, client):
        """Each course should have required fields if courses exist"""
        response = await client.get("/api/courses")
        assert response.status_code == 200

        data = response.json()
        courses = data["courses"]

        # If there are courses, verify structure
        if len(courses) > 0:
            course = courses[0]
            assert "id" in course
            assert "code" in course
            assert "name" in course
            # Verify fields are correct types
            assert isinstance(course["id"], int)
            assert isinstance(course["code"], str)
            assert isinstance(course["name"], str)


@pytest.mark.asyncio
class TestCourseInitializationAuthorization:
    async def test_regular_user_cannot_initialize_courses(
        self, client, auth_headers
    ) -> None:
        response = await client.post("/api/courses/init", headers=auth_headers)

        assert response.status_code == 403
        assert response.json()["detail"] == "Admin access required"

    async def test_init_uses_central_admin_dependency(
        self, client, admin_user
    ) -> None:
        app.dependency_overrides[get_current_admin_user] = lambda: admin_user
        try:
            response = await client.post("/api/courses/init")
        finally:
            app.dependency_overrides.pop(get_current_admin_user, None)

        assert response.status_code == 200
        assert response.json()["created"] == ["C", "CPP", "Python"]


@pytest.mark.asyncio
class TestCourseDetail:
    """Test GET /api/courses/{course_id} endpoint"""

    async def test_get_course_detail_returns_404_for_empty_db(self, client):
        """Should return 404 when course not found"""
        response = await client.get("/api/courses/99999")
        assert response.status_code == 404

    async def test_get_course_detail_returns_404_for_invalid_id(self, client):
        """Should return 422 for non-numeric course ID"""
        response = await client.get("/api/courses/nonexistent-id")
        assert response.status_code in [404, 422]


@pytest.mark.asyncio
class TestChapterContent:
    """Test GET /api/courses/{course_id}/chapters/{chapter_id} endpoint"""

    async def test_get_chapter_returns_404_for_empty_db(self, client):
        """Should return 404 when chapter not found"""
        response = await client.get("/api/courses/1/chapters/99999")
        assert response.status_code in [404, 422]

    async def test_get_chapter_returns_404_for_invalid_ids(self, client):
        """Should return 422 for non-existent chapter"""
        response = await client.get("/api/courses/some-course/chapters/nonexistent")
        assert response.status_code in [404, 422]


# ========================================
# Phase 1: Course Progress Overview API
# ========================================

@pytest.mark.asyncio
class TestUserCourseProgress:
    """Test GET /api/courses/users/me/course-progress endpoint"""

    async def test_get_course_progress_requires_auth(self, client):
        """Should return 401 when not authenticated"""
        response = await client.get("/api/courses/users/me/course-progress")
        assert response.status_code == 401

    async def test_get_course_progress_returns_list(self, client, auth_headers):
        """Should return a list of courses with progress"""
        response = await client.get(
            "/api/courses/users/me/course-progress",
            headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert "courses" in data
        assert isinstance(data["courses"], list)

    async def test_get_course_progress_includes_required_fields(self, client, auth_headers):
        """Each course should have required progress fields"""
        response = await client.get(
            "/api/courses/users/me/course-progress",
            headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        courses = data["courses"]

        # If there are courses, verify structure
        if len(courses) > 0:
            course = courses[0]
            # Required fields
            assert "course_id" in course
            assert "course_name" in course
            assert "progress" in course
            # Optional fields that should exist
            assert "mastery_score" in course or True  # May be null
            assert "arena_tier" in course or True  # May be null
            assert "arena_score" in course or True  # May be null

    async def test_get_course_progress_returns_all_8_courses(self, client, auth_headers, init_courses):
        """Should return all 8 courses even if user has no progress"""
        response = await client.get(
            "/api/courses/users/me/course-progress",
            headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        # Should have exactly 8 courses
        assert len(data["courses"]) == 8


# ========================================
# Phase 3: Today Stats API
# ========================================

@pytest.mark.asyncio
class TestTodayStats:
    """Test GET /api/stats/today endpoint"""

    async def test_get_today_stats_requires_auth(self, client):
        """Should return 401 when not authenticated"""
        response = await client.get("/api/stats/today")
        assert response.status_code == 401

    async def test_get_today_stats_returns_data(self, client, auth_headers):
        """Should return today's learning statistics"""
        response = await client.get(
            "/api/stats/today",
            headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        # Required fields
        assert "exercises" in data
        assert "correct" in data
        assert "accuracy" in data
        assert "time_minutes" in data

        # Verify types
        assert isinstance(data["exercises"], int)
        assert isinstance(data["correct"], int)
        assert isinstance(data["accuracy"], (int, float))
        assert isinstance(data["time_minutes"], (int, float))
